# backend/routes/password_forget.py
from fastapi import APIRouter, HTTPException, Form, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone

from ..models.user import User
from ..utils.security import (
    hash_password,
    create_password_reset_token,
    decode_password_reset_token,
)
from ..utils.email import send_email
from ..routes.auth import get_current_user

router = APIRouter()

# ---------- 1) Forgot password (email reset flow) ----------
class ForgotRequest(BaseModel):
    email: EmailStr

@router.post("/forgot")
async def forgot_password(payload: ForgotRequest):
    user = await User.find_one(User.email == payload.email, User.is_verified == True)
    if not user:
        return {"msg": "If that email exists and is verified, a reset link has been sent."}

    token = create_password_reset_token(str(user.id))
    reset_link = f"http://10.0.2.2:8000/password/reset?token={token}"

    send_email(
        to_email=user.email,
        subject="Reset your password",
        body=f"Click here to reset your password:\n\n{reset_link}\n\n"
             "If you did not request this, you can ignore this email."
    )
    return {"msg": "If that email exists and is verified, a reset link has been sent."}


# ---------- 2) Reset password (via email link) ----------
@router.get("/reset", response_class=HTMLResponse)
async def reset_password_form(token: str):
    html = f"""
    <!doctype html>
    <html><head><meta charset="utf-8"><title>Reset Password</title></head>
    <body>
      <h2>Reset your password</h2>
      <form method="POST" action="/password/reset">
        <input type="hidden" name="token" value="{token}" />
        <label>New password</label><br/>
        <input type="password" name="new_password" required />
        <button type="submit">Update password</button>
      </form>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@router.post("/reset", response_class=HTMLResponse)
async def reset_password(token: str = Form(...), new_password: str = Form(...)):
    user_id = decode_password_reset_token(token)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = hash_password(new_password)
    user.hashed_refresh_token = None
    user.refresh_token_expiry = None
    user.password_changed_at = datetime.now(timezone.utc)
    user.updated_at = datetime.now(timezone.utc)
    await user.save()

    return HTMLResponse("<h3>Password updated successfully. You can now log in.</h3>")


# ---------- 3) Change password (in-app, requires login) ----------
class ChangePasswordRequest(BaseModel):
    new_password: str

@router.post("/change")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Allows a logged-in user to change their password inside profile screen.
    Logs them out everywhere afterwards.
    """
    current_user.hashed_password = hash_password(payload.new_password)
    current_user.hashed_refresh_token = None
    current_user.refresh_token_expiry = None
    current_user.password_changed_at = datetime.now(timezone.utc)
    current_user.updated_at = datetime.now(timezone.utc)

    await current_user.save()
    return {"msg": "Password updated. Please log in again."}
