# backend/app/routes/payment.py
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.db import database
import stripe
from datetime import datetime, timezone, timedelta
from app.config import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, FRONTEND_URL
from app.models.user import User
from app.routes.auth import get_current_user

router = APIRouter()
stripe.api_key = STRIPE_SECRET_KEY

# ------------------- Request Models -------------------
class CheckoutRequest(BaseModel):
    package_id: str
    user_id: str

class UpdateSubscriptionRequest(BaseModel):
    user_id: str
    subscription_id: str
    new_package_id: str

class CancelSubscriptionRequest(BaseModel):
    user_id: str
    subscription_id: str

# ------------------- Helper -------------------
def serialize_package(package):
    package["_id"] = str(package["_id"])
    return package

# ------------------- Routes -------------------
@router.get("/packages")
async def get_packages(user_id: str):
    """ Return packages. Exclude free trial if user already used a package (trial). """
    used_trial = await database["subscriptions"].find_one({
        "user_id": user_id,
        "package_id": {"$exists": True},
        "status": {"$in": ["active", "expired", "canceled"]}
    })
    
    query = {}
    if used_trial:
        query = {"is_free_trial": {"$ne": True}}
    
    packages = await database["packages"].find(query).to_list(100)
    return [serialize_package(p) for p in packages]

@router.post("/create-checkout-session")
async def create_checkout_session(req: CheckoutRequest):
    package_id = req.package_id
    user_id = req.user_id
    
    package = await database["packages"].find_one({"_id": package_id})
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    
    try:
        # Use your app's custom URL scheme for deep linking
        success_url = f"{FRONTEND_URL}payment/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{FRONTEND_URL}payment/cancel"
        
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": package["name"]},
                    "unit_amount": int(package["price"] * 100),
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "user_id": user_id, 
                "package_id": str(package["_id"]),
                "package_name": package["name"]
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")
    
    return {
        "checkout_url": session.url,
    }

@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = (await request.body()).decode("utf-8")  # decode raw body
    sig_header = request.headers.get("stripe-signature")
    endpoint_secret = STRIPE_WEBHOOK_SECRET
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        print("Webhook error:", e)
        raise HTTPException(status_code=400, detail=f"Webhook Error: {str(e)}")
    
    # Handle checkout.session.completed
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})
        user_id = metadata.get("user_id")
        package_id = metadata.get("package_id")
        
        # fetch package to compute duration
        package = await database["packages"].find_one({"_id": package_id})
        
        start_date = datetime.now(timezone.utc)
        if package and package.get("interval") == "trial":
            days = package.get("trial_duration_days", 7)
            end_date = start_date + timedelta(days=days)
        elif package and package.get("interval") == "month":
            end_date = start_date + timedelta(days=30)
        elif package and package.get("interval") == "year":
            end_date = start_date + timedelta(days=365)
        else:
            end_date = None
        
        # Create subscription document
        doc = {
            "user_id": user_id,
            "package_id": package_id,
            "package_name": package.get("name") if package else None,
            "start_date": start_date,
            "end_date": end_date,
            "status": "active",
            "payment_intent_id": session.get("payment_intent"),
            "created_at": datetime.now(timezone.utc)
        }
        await database["subscriptions"].insert_one(doc)
        
        try:
            from app.models.user import User  
            user_obj_id = ObjectId(user_id)
            
            # Update using Beanie for consistency
            user = await User.get(user_obj_id)
            if user:
                user.is_subscribed = True
                user.updated_at = datetime.now(timezone.utc)
                await user.save()
                print(f"Updated user {user_id} subscription status to True")
            else:
                print(f"User {user_id} not found")      
        except Exception as e:
            print(f"Error updating user subscription: {e}")
    
    return JSONResponse(content={"status": "success"})

# Get single user's active subscription (with package details)
@router.get("/subscription/{user_id}")
async def get_subscription(user_id: str):
    # Always ensure we're querying with string user_id since subscriptions.user_id is a string
    user_id_str = str(user_id)

    sub = await database["subscriptions"].find_one(
        {"user_id": user_id_str, "status": "active"}
    )
    if not sub:
        return {}

    # Convert subscription fields
    sub["_id"] = str(sub["_id"])
    if "start_date" in sub and sub["start_date"]:
        sub["start_date"] = sub["start_date"].isoformat()
    if "end_date" in sub and sub["end_date"]:
        sub["end_date"] = sub["end_date"].isoformat()

    # Fetch and attach package details
    package = await database["packages"].find_one({"_id": sub["package_id"]})
    if package:
        package["_id"] = str(package["_id"])
        sub["package"] = package

    return sub


# ----------------- CANCELLATION & UPDATING LOGIC -----------------

@router.post("/cancel-subscription")
async def cancel_subscription(req: CancelSubscriptionRequest):
    try:
        sub_id_obj = ObjectId(req.subscription_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid subscription ID format")

    user_id_str = str(req.user_id)

    # Check if user exists and is subscribed
    user = await database["users"].find_one({"_id": ObjectId(user_id_str)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.get("is_subscribed", False):
        raise HTTPException(status_code=400, detail="User is not currently subscribed")

    # Find active subscription for this user
    sub = await database["subscriptions"].find_one(
        {"_id": sub_id_obj, "user_id": user_id_str, "status": "active"}
    )
    if not sub:
        raise HTTPException(status_code=404, detail="Active subscription not found")

    # Cancel subscription
    update_result = await database["subscriptions"].update_one(
        {"_id": sub_id_obj, "user_id": user_id_str},
        {"$set": {"status": "canceled", "cancellation_date": datetime.now(timezone.utc)}}
    )

    if update_result.modified_count != 1:
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")

    # Mark user as unsubscribed
    await database["users"].update_one(
        {"_id": ObjectId(user_id_str)},
        {"$set": {"is_subscribed": False, "updated_at": datetime.now(timezone.utc)}}
    )

    return {"status": "canceled", "message": "Subscription cancelled successfully"}


# Update subscription (prepare for upgrade/downgrade)
@router.patch("/update-subscription")
async def update_subscription(req: UpdateSubscriptionRequest):
    """ Don't update DB immediately. Just tell frontend that checkout is required. The actual subscription update will happen only after Stripe webhook confirms payment. """
    sub = await database["subscriptions"].find_one(
        {"_id": req.subscription_id, "user_id": req.user_id}
    )
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    return {
        "status": "pending",
        "message": "Proceed with checkout for new package",
        "old_subscription_id": str(sub["_id"]),
    }