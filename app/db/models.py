"""P Square database models for v1.1."""
from datetime import datetime, date
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(100))
    dob: Mapped[Optional[date]] = mapped_column(Date)
    sex: Mapped[Optional[str]] = mapped_column(String(20))
    ethnicity: Mapped[Optional[str]] = mapped_column(String(50))
    language: Mapped[str] = mapped_column(String(10), default="en")
    city: Mapped[Optional[str]] = mapped_column(String(50))
    tz: Mapped[str] = mapped_column(String(50), default="Asia/Kolkata")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    consent_given_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    biometric_consent_given_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    profile: Mapped[Optional["Profile"]] = relationship(
        "Profile", back_populates="user", uselist=False
    )
    medical_history: Mapped[list["MedicalHistory"]] = relationship(
        "MedicalHistory", back_populates="user"
    )
    medications: Mapped[list["Medication"]] = relationship("Medication", back_populates="user")
    family_history: Mapped[list["FamilyHistory"]] = relationship(
        "FamilyHistory", back_populates="user"
    )
    lab_results: Mapped[list["LabResult"]] = relationship("LabResult", back_populates="user")
    bp_readings: Mapped[list["BPReading"]] = relationship("BPReading", back_populates="user")
    rhr_readings: Mapped[list["RHRReading"]] = relationship("RHRReading", back_populates="user")
    steps_logs: Mapped[list["StepsLog"]] = relationship("StepsLog", back_populates="user")
    habit_logs: Mapped[list["HabitLog"]] = relationship("HabitLog", back_populates="user")
    smoking_logs: Mapped[list["SmokingLog"]] = relationship("SmokingLog", back_populates="user")
    heart_scores: Mapped[list["HeartScore"]] = relationship("HeartScore", back_populates="user")
    ppg_scans: Mapped[list["PPGScan"]] = relationship("PPGScan", back_populates="user")
    bio_age_assessments: Mapped[list["BioAgeAssessment"]] = relationship(
        "BioAgeAssessment", back_populates="user"
    )
    plans: Mapped[list["Plan"]] = relationship("Plan", back_populates="user")
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation", back_populates="user"
    )
    reports: Mapped[list["Report"]] = relationship("Report", back_populates="user")
    checkins: Mapped[list["Checkin"]] = relationship("Checkin", back_populates="user")


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True)
    height_cm: Mapped[Optional[Float]] = mapped_column(Float)
    weight_kg: Mapped[Optional[Float]] = mapped_column(Float)
    waist_cm: Mapped[Optional[Float]] = mapped_column(Float)
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="profile")


class MedicalHistory(Base):
    __tablename__ = "medical_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    condition: Mapped[str] = mapped_column(String(50))
    since: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[Optional[str]] = mapped_column(String(20))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    user: Mapped["User"] = relationship("User", back_populates="medical_history")


class Medication(Base):
    __tablename__ = "medications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(100))
    dose: Mapped[Optional[str]] = mapped_column(String(50))
    frequency: Mapped[Optional[str]] = mapped_column(String(50))
    since: Mapped[Optional[date]] = mapped_column(Date)

    user: Mapped["User"] = relationship("User", back_populates="medications")


class FamilyHistory(Base):
    __tablename__ = "family_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    relation: Mapped[str] = mapped_column(String(20))
    condition: Mapped[str] = mapped_column(String(50))
    age_of_onset: Mapped[Optional[int]] = mapped_column(Integer)

    user: Mapped["User"] = relationship("User", back_populates="family_history")


class LabResult(Base):
    __tablename__ = "lab_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    test_name: Mapped[str] = mapped_column(String(50))
    value: Mapped[Optional[Float]] = mapped_column(Float)
    unit: Mapped[Optional[str]] = mapped_column(String(20))
    ref_low: Mapped[Optional[Float]] = mapped_column(Float)
    ref_high: Mapped[Optional[Float]] = mapped_column(Float)
    taken_on: Mapped[date] = mapped_column(Date)
    source: Mapped[str] = mapped_column(String(20), default="self_reported")

    user: Mapped["User"] = relationship("User", back_populates="lab_results")


class BPReading(Base):
    __tablename__ = "bp_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    systolic: Mapped[int] = mapped_column(Integer)
    diastolic: Mapped[int] = mapped_column(Integer)
    pulse: Mapped[Optional[int]] = mapped_column(Integer)
    taken_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    posture: Mapped[Optional[str]] = mapped_column(String(20))
    source: Mapped[str] = mapped_column(String(20), default="self_reported")

    user: Mapped["User"] = relationship("User", back_populates="bp_readings")


class RHRReading(Base):
    __tablename__ = "rhr_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    bpm: Mapped[int] = mapped_column(Integer)
    taken_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    source: Mapped[str] = mapped_column(String(20), default="self_reported")

    user: Mapped["User"] = relationship("User", back_populates="rhr_readings")


class StepsLog(Base):
    __tablename__ = "steps_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    date: Mapped[date] = mapped_column(Date, index=True)
    steps: Mapped[int] = mapped_column(Integer)
    active_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(20), default="self_reported")

    user: Mapped["User"] = relationship("User", back_populates="steps_logs")


class HabitLog(Base):
    __tablename__ = "habit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    date: Mapped[date] = mapped_column(Date, index=True)
    habits_json: Mapped[JSON] = mapped_column(JSON, default=dict)
    streak_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)

    user: Mapped["User"] = relationship("User", back_populates="habit_logs")


class SmokingLog(Base):
    __tablename__ = "smoking_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    date: Mapped[date] = mapped_column(Date, index=True)
    cigarettes: Mapped[Optional[int]] = mapped_column(Integer)

    user: Mapped["User"] = relationship("User", back_populates="smoking_logs")


class HeartScore(Base):
    __tablename__ = "heart_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    score: Mapped[int] = mapped_column(Integer)
    breakdown_json: Mapped[JSON] = mapped_column(JSON, default=dict)
    confidence: Mapped[str] = mapped_column(String(20), default="Medium")
    computed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="heart_scores")


class PPGScan(Base):
    __tablename__ = "ppg_scans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    taken_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    hr_bpm: Mapped[Optional[int]] = mapped_column(Integer)
    rmssd_ms: Mapped[Optional[Float]] = mapped_column(Float)
    sdnn_ms: Mapped[Optional[Float]] = mapped_column(Float)
    pnn50_pct: Mapped[Optional[Float]] = mapped_column(Float)
    stress_index: Mapped[Optional[int]] = mapped_column(Integer)
    signal_quality: Mapped[Optional[float]] = mapped_column(Float)
    raw_signal_url: Mapped[Optional[str]] = mapped_column(String(500))
    pre_scan_context_json: Mapped[Optional[JSON]] = mapped_column(JSON, default=dict)
    source_device: Mapped[Optional[str]] = mapped_column(String(50))

    user: Mapped["User"] = relationship("User", back_populates="ppg_scans")


class BioAgeAssessment(Base):
    __tablename__ = "bio_age_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    taken_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    biological_age: Mapped[Optional[float]] = mapped_column(Float)
    chronological_age: Mapped[Optional[int]] = mapped_column(Integer)
    face_image_url: Mapped[Optional[str]] = mapped_column(String(500))
    face_age_estimate: Mapped[Optional[float]] = mapped_column(Float)
    face_drivers_json: Mapped[Optional[JSON]] = mapped_column(JSON, default=list)
    questionnaire_json: Mapped[Optional[JSON]] = mapped_column(JSON, default=dict)
    computed_breakdown_json: Mapped[Optional[JSON]] = mapped_column(JSON, default=dict)

    user: Mapped["User"] = relationship("User", back_populates="bio_age_assessments")


class PlanType(str, Enum):
    CARDIO = "cardio"
    STRENGTH = "strength"
    MEALS = "meals"
    LIFESTYLE = "lifestyle"
    LAB_CADENCE = "lab_cadence"
    BIOAGE_REVERSAL = "bioage_reversal"


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    type: Mapped[PlanType] = mapped_column(SQLEnum(PlanType))
    version: Mapped[int] = mapped_column(Integer, default=1)
    payload_json: Mapped[JSON] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["User"] = relationship("User", back_populates="plans")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_msg_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="conversation")


class MessageDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(Integer, ForeignKey("conversations.id"))
    direction: Mapped[MessageDirection] = mapped_column(SQLEnum(MessageDirection))
    content: Mapped[str] = mapped_column(Text)
    media_url: Mapped[Optional[str]] = mapped_column(String(500))
    intent: Mapped[Optional[str]] = mapped_column(String(50))
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="messages"
    )


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    version: Mapped[str] = mapped_column(String(20), default="1.1")
    pdf_url: Mapped[str] = mapped_column(String(500))
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="reports")


class CheckinType(str, Enum):
    MORNING = "morning"
    EVENING = "evening"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class Checkin(Base):
    __tablename__ = "checkins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    scheduled_for: Mapped[datetime] = mapped_column(DateTime)
    type: Mapped[CheckinType] = mapped_column(SQLEnum(CheckinType))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    user: Mapped["User"] = relationship("User", back_populates="checkins")


class MiniAppSessionType(str, Enum):
    PPG = "ppg"
    BIOAGE = "bioage"


class MiniAppSession(Base):
    __tablename__ = "mini_app_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    type: Mapped[MiniAppSessionType] = mapped_column(SQLEnum(MiniAppSessionType))
    jwt_jti: Mapped[str] = mapped_column(String(100), unique=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    result_id: Mapped[Optional[int]] = mapped_column(Integer)


# Import at bottom to avoid circular imports
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402


def get_engine(url: str):
    return create_engine(url, pool_pre_ping=True)


def get_session_maker(engine):
    return sessionmaker(bind=engine, expire_on_commit=False)