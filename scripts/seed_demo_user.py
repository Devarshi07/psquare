"""Seed demo user for testing.

Per CLAUDE.md §17:
- 42-yr-old Indian male
- Smoker (10/day)
- BP 138/86
- LDL 142, HDL 38
- Sedentary desk job
- Father had MI at 54
"""
import asyncio
import sys
from datetime import datetime, date, timedelta

# Add parent dir to path
sys.path.insert(0, str(__file__).rsplit("/", 1)[0].rsplit("/", 1)[0])

from app.db import get_db_session
from app.db.models import (
    User, Profile, MedicalHistory, FamilyHistory, LabResult,
    BPReading, RHRReading, StepsLog, HeartScore, SmokingLog
)


async def seed_demo_user():
    """Create the demo user with full test data."""
    session = await get_db_session()

    # Check if demo user exists
    from sqlalchemy import select
    stmt = select(User).where(User.phone == "+919999999999")
    existing = await session.scalar(stmt)

    if existing:
        print("Demo user already exists, skipping seed.")
        return existing

    # Create user
    user = User(
        phone="+919999999999",
        name="Rahul Sharma",
        dob=date(1982, 5, 15),  # 42 years old
        sex="male",
        ethnicity="south_asian",
        city="Mumbai",
        language="en",
        consent_given_at=datetime.now(),
    )
    session.add(user)
    await session.flush()

    print(f"Created user: {user.name} (ID: {user.id})")

    # Create profile
    profile = Profile(
        user_id=user.id,
        height_cm=172,
        weight_kg=82,
        waist_cm=98,  # High risk for Indian male
    )
    session.add(profile)

    # Create medical history
    conditions = [
        MedicalHistory(user_id=user.id, condition="hypertension", status="well-controlled"),
        MedicalHistory(user_id=user.id, condition="high_cholesterol", status="on-medication"),
    ]
    for c in conditions:
        session.add(c)

    # Create family history
    fh = FamilyHistory(
        user_id=user.id,
        relation="father",
        condition="heart_attack",
        age_of_onset=54,
    )
    session.add(fh)

    # Create lab results
    labs = [
        LabResult(
            user_id=user.id,
            test_name="LDL",
            value=142,
            unit="mg/dL",
            ref_low=0,
            ref_high=100,
            taken_on=date.today() - timedelta(days=30),
            source="lab_uploaded",
        ),
        LabResult(
            user_id=user.id,
            test_name="HDL",
            value=38,
            unit="mg/dL",
            ref_low=40,
            ref_high=60,
            taken_on=date.today() - timedelta(days=30),
            source="lab_uploaded",
        ),
        LabResult(
            user_id=user.id,
            test_name="Total Cholesterol",
            value=220,
            unit="mg/dL",
            ref_low=0,
            ref_high=200,
            taken_on=date.today() - timedelta(days=30),
            source="lab_uploaded",
        ),
        LabResult(
            user_id=user.id,
            test_name="Triglycerides",
            value=180,
            unit="mg/dL",
            ref_low=0,
            ref_high=150,
            taken_on=date.today() - timedelta(days=30),
            source="lab_uploaded",
        ),
        LabResult(
            user_id=user.id,
            test_name="HbA1c",
            value=5.9,
            unit="%",
            ref_low=4.0,
            ref_high=5.6,
            taken_on=date.today() - timedelta(days=45),
            source="lab_uploaded",
        ),
    ]
    for lab in labs:
        session.add(lab)

    # Create BP readings (last 7 days)
    for i in range(7):
        bp = BPReading(
            user_id=user.id,
            systolic=136 + i,
            diastolic=84 + (i % 2),
            pulse=78 + (i % 3),
            taken_at=datetime.now() - timedelta(days=i),
            source="self_reported",
        )
        session.add(bp)

    # Create RHR readings
    for i in range(5):
        rhr = RHRReading(
            user_id=user.id,
            bpm=72 + (i % 3),
            taken_at=datetime.now() - timedelta(days=i),
            source="self_reported",
        )
        session.add(rhr)

    # Create steps logs (sedentary pattern)
    for i in range(14):
        steps = StepsLog(
            user_id=user.id,
            date=date.today() - timedelta(days=i),
            steps=3500 + (i * 200),  # Slowly increasing
            active_minutes=20 + i,
            source="self_reported",
        )
        session.add(steps)

    # Create smoking log
    for i in range(7):
        smoke = SmokingLog(
            user_id=user.id,
            date=date.today() - timedelta(days=i),
            cigarettes=10,
        )
        session.add(smoke)

    # Create heart score
    score = HeartScore(
        user_id=user.id,
        score=58,  # Fair
        breakdown_json={
            "cv_risk_percent": 18.5,
            "heart_age_gap": 8,
            "lifestyle_penalty": 35,
            "condition_penalty": 25,
        },
        confidence="High",
    )
    session.add(score)

    await session.commit()

    print("✅ Demo user seeded successfully!")
    print(f"  Phone: +919999999999")
    print(f"  Age: 42, Male, South Indian")
    print(f"  BP: 138/86 (elevated)")
    print(f"  LDL: 142, HDL: 38")
    print(f"  Steps: ~3500/day (sedentary)")
    print(f"  Smokes: 10/day")
    print(f"  Father: MI at 54")
    print(f"  Heart Score: 58 (Fair)")

    return user


if __name__ == "__main__":
    asyncio.run(seed_demo_user())