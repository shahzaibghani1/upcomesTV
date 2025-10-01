# backend/app/utils/seed_packages.py
import asyncio
from app.db import database

async def seed():
    packages = [
        {
            "_id": "free-trial",  # optional explicit id for easier testing
            "name": "Free Trial",
            "price": 0,
            "interval": "trial",
            "description": "Start your journey with a 7-day free trial. No commitments.",
            "features": [
                "Unlimited ad-free Movies and TV Shows",
                "Watch in HD",
                "Access on 2 devices"
            ],
            "is_free_trial": True,
            "trial_duration_days": 7,
        },
        {
            "_id": "monthly-basic",
            "name": "Monthly Basic",
            "price": 8.99,
            "interval": "month",
            "description": "Cancel at any time.",
            "features": [
                "Unlimited ad-free Movies and TV Shows",
                "Watch in HD",
                "2 devices"
            ],
            "is_free_trial": False,
        },
        {
            "_id": "monthly-premium",
            "name": "Monthly Premium",
            "price": 15.99,
            "interval": "month",
            "description": "Cancel at any time.",
            "features": [
                "Unlimited ad-free Movies and TV Shows",
                "Watch in 4K",
                "Unlimited devices",
                "Download content"
            ],
            "is_free_trial": False,
        },
        {
            "_id": "yearly",
            "name": "Yearly",
            "price": 159.99,
            "interval": "year",
            "description": "Save 10% annually.",
            "features": [
                "Unlimited ad-free Movies and TV Shows",
                "Watch in 4K",
                "Unlimited devices",
                "Download content",
                "Early access to new releases"
            ],
            "is_free_trial": False,
        },
    ]

    await database["packages"].delete_many({})
    await database["packages"].insert_many(packages)
    print("Packages seeded!")

if __name__ == "__main__":
    asyncio.run(seed())
