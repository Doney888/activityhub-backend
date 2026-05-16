from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime, DECIMAL, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    
    avatar_url = Column(String, nullable=True)
    banner_url = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    role = Column(String, default="user")
    
    # Безопасность
    is_verified = Column(Boolean, default=False)
    is_2fa_enabled = Column(Boolean, default=False)
    
    # Геймификация
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_activity_date = Column(DateTime(timezone=True), nullable=True)
    
    notification_settings = Column(JSON, default={})
    last_filter_settings = Column(JSON, default={})
    
    is_google_fit_connected = Column(Boolean, default=False)
    daily_step_goal = Column(Integer, default=10000)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    admin_profile = relationship("Administrator", back_populates="user", uselist=False)

class OTPCode(Base):
    __tablename__ = "otp_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True, nullable=False)
    code = Column(String, nullable=False) # Токен или код
    purpose = Column(String, nullable=False) # 'registration' или 'login_2fa'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Administrator(Base):
    __tablename__ = "administrators"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    access_level = Column(String, default="moderator")
    department = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="admin_profile")

class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    category_id = Column(Integer, nullable=False)
    
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    image_url = Column(String, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=True)
    
    base_probability_weight = Column(Integer, default=50)
    is_sponsored = Column(Boolean, default=False)
    partner_name = Column(String, nullable=True)
    promo_url = Column(String, nullable=True)
    ad_expiration_date = Column(DateTime(timezone=True), nullable=True)
    
    latitude = Column(DECIMAL(10, 8), nullable=True)
    longitude = Column(DECIMAL(11, 8), nullable=True)
    address_text = Column(String, nullable=True)
    place_query = Column(String, nullable=True)
    
    cost_type = Column(String, nullable=False)
    duration_type = Column(String, nullable=False)
    location_type = Column(String, nullable=False)
    participants_type = Column(String, nullable=False)
    season = Column(String, nullable=False)
    preparation_type = Column(String, nullable=False)
    mood_type = Column(String, nullable=False)
    weather_condition = Column(String, nullable=False)
    time_of_day = Column(String, nullable=False)
    
    status = Column(String, default="published")
    priority_score = Column(Integer, default=0)
    likes_count = Column(Integer, default=0)
    views_count = Column(Integer, default=0)
    saves_count = Column(Integer, default=0)
    route_clicks_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())