# backend/routes/profile.py
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from ..models.user import User, UserUpdate, UserOut
from ..routes.auth import get_current_user

router = APIRouter()

@router.put("/update", response_model=UserOut)
async def update_profile(user_update: UserUpdate, current_user: User = Depends(get_current_user)):

    if not user_update.name:
        raise HTTPException(status_code=400, detail="No valid fields provided")

    current_user.name = user_update.name
    current_user.updated_at = datetime.now(timezone.utc)
    await current_user.save()

    return UserOut(id=str(current_user.id), name=current_user.name, email=current_user.email)
