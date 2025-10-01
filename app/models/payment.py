# backend/app/models/payment.py

from datetime import datetime
from typing import List, Optional
from beanie import Document
from pydantic import BaseModel, Field

# ---------- Pydantic Sub-Schema (Embedded) ----------
class PaymentHistory(BaseModel):
    stripe_payment_id: str
    amount: float
    currency: str
    status: str
    timestamp: datetime

# ---------- Beanie Collections ----------
class Package(Document):
    name: str
    price: float
    interval: str 
    description: str
    features: List[str]
    is_free_trial: bool = False
    trial_duration_days: int = 0

    class Settings:
        name = "packages"

class Subscription(Document):
    user_id: str
    package_id: str
    status: str  
    start_date: datetime
    end_date: Optional[datetime]
    payment_history: List[PaymentHistory] = Field(default_factory=list)

    class Settings:
        name = "subscriptions"  
