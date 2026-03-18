from datetime import datetime, date
from typing import Optional

from sqlalchemy import Integer, String, Boolean, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    sex: Mapped[str] = mapped_column(String(1)) # 'M' ou 'F'
    age: Mapped[int] = mapped_column(Integer)
    height_cm: Mapped[float] = mapped_column(Float)
    waist_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)   # Circunferência cintura
    hip_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)     # Circunferência quadril
    activity_level: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    language: Mapped[Optional[str]] = mapped_column(String(5), nullable=True, default='pt')

    measurements = relationship("Measurement", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    fasting_sessions = relationship("FastingSession", back_populates="user", cascade="all, delete-orphan")


class BLEDevice(Base):
    __tablename__ = 'ble_devices'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mac_address: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    protocol_version: Mapped[str] = mapped_column(String(10)) # 'v1' ou 'v2'
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    is_preferred: Mapped[bool] = mapped_column(Boolean, default=False)
    
    measurements = relationship("Measurement", back_populates="device")


class Measurement(Base):
    __tablename__ = 'measurements'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    device_id: Mapped[Optional[int]] = mapped_column(ForeignKey('ble_devices.id'), nullable=True)
    
    measured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    weight_kg: Mapped[float] = mapped_column(Float)
    impedance: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    bmi: Mapped[float] = mapped_column(Float)
    body_fat_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    muscle_mass_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    body_water_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bone_mass_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    visceral_fat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bmr: Mapped[float] = mapped_column(Float)
    tdee: Mapped[float] = mapped_column(Float)
    metabolic_age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    protein_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fat_free_mass_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # --- Expanded metrics ---
    smm_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)           # Skeletal Muscle Mass
    lbm_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)           # Lean Body Mass
    impedance_index: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # H²/R
    body_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)       # 1-100
    ideal_weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ffmi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)             # Fat-Free Mass Index
    smi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)              # Skeletal Muscle Index
    subcutaneous_fat_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    whr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)              # Waist-Hip Ratio
    whtr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)             # Waist-Height Ratio
    
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    raw_data_hex: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    source: Mapped[str] = mapped_column(String(20), default='ble') # 'ble' ou 'manual'
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="measurements")
    device = relationship("BLEDevice", back_populates="measurements")


class Goal(Base):
    __tablename__ = 'goals'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    metric: Mapped[str] = mapped_column(String(50))
    target_value: Mapped[float] = mapped_column(Float)
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    achieved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user = relationship("User", back_populates="goals")


class FastingSession(Base):
    __tablename__ = 'fasting_sessions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    protocol: Mapped[str] = mapped_column(String(10))  # '16:8', '18:6', '20:4', 'OMAD'
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    target_hours: Mapped[int] = mapped_column(Integer, default=16)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)

    user = relationship("User", back_populates="fasting_sessions")
