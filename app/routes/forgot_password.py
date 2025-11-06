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
    # reset_link = f"http://10.0.2.2:8000/password/reset?token={token}"
    reset_link = f"https://upcomestv.site/password/reset?token={token}"

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
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reset Password - UpComes TV</title>
    </head>
    <body style="
        font-family: 'Poppins', 'Segoe UI', sans-serif;
        background-color: #000;
        color: #fff;
        margin: 0;
        padding: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100vh;
    ">
        <div style="
            background: #111;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            width: 90%;
            max-width: 380px;
            padding: 30px 25px;
            text-align: center;
        ">
            <!-- App Logo -->
            <img src="/static/logo_with_name.png" alt="UpComes TV Logo" 
                 style="width: 140px; height: auto; margin-bottom: 15px;">

            <h2 style="margin-bottom: 10px; color: #FFD700;">Reset Your Password</h2>
            <p style="font-size: 14px; color: #cccccc; margin-bottom: 25px;">
                Enter your new password to continue watching UpComes TV.
            </p>

            <form method="POST" action="/password/reset" style="display: flex; flex-direction: column; gap: 15px;">
                <input type="hidden" name="token" value="{token}" />
                <input 
                    type="password" 
                    name="new_password" 
                    placeholder="New Password" 
                    required
                    style="
                        padding: 12px;
                        border: none;
                        border-radius: 8px;
                        font-size: 15px;
                        outline: none;
                        background: #222;
                        color: #00FF66;
                        text-align: center;
                    "
                />
                <button type="submit" style="
                    background: #00FF66;
                    color: #000;
                    padding: 12px;
                    border: none;
                    border-radius: 8px;
                    font-size: 16px;
                    font-weight: bold;
                    cursor: pointer;
                    transition: 0.3s;
                "
                onmouseover="this.style.background='#FFD700'"
                onmouseout="this.style.background='#00FF66'">
                    Update Password
                </button>
            </form>
        </div>
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
