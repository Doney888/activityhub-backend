from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi.middleware.cors import CORSMiddleware
from typing import List

import models
import schemas
import security
import email_utils
from database import get_db

app = FastAPI(title="ActivityHub API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@app.get("/")
async def root():
    return {"message": "ActivityHub Backend is Live!"}

# === РЕГИСТРАЦИЯ ===
@app.post("/auth/register")
async def register(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).where(models.User.email == user.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pw = security.get_password_hash(user.password)
    new_user = models.User(
        email=user.email, password_hash=hashed_pw, name=user.name, role="user", is_verified=False
    )
    db.add(new_user)
    
    token = email_utils.generate_email_token()
    otp_entry = models.OTPCode(email=user.email, code=token, purpose="registration")
    db.add(otp_entry)
    
    await db.commit()
    await email_utils.send_verification_link(user.email, token)
    
    return {"message": "User created. Check email for verification link."}

# === ПОДТВЕРЖДЕНИЕ EMAIL (ССЫЛКА) ===
@app.get("/auth/verify-email", response_class=HTMLResponse)
async def verify_email_link(token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.OTPCode).where(
        models.OTPCode.code == token, models.OTPCode.purpose == "registration"
    ))
    otp_record = result.scalars().first()
    
    if not otp_record:
        return "<h1>Ошибка: Ссылка недействительна.</h1>"
        
    result_user = await db.execute(select(models.User).where(models.User.email == otp_record.email))
    user = result_user.scalars().first()
    
    if user:
        user.is_verified = True
        await db.delete(otp_record)
        await db.commit()
        return "<h1>Email успешно подтвержден! Можно входить.</h1>"
    return "<h1>Ошибка пользователя</h1>"

# === ВХОД (LOGIN + 2FA) ===
@app.post("/auth/login")
async def login(user_data: schemas.UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).where(models.User.email == user_data.email))
    user = result.scalars().first()
    
    if not user or not security.verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified.")

    # Если 2FA включена
    if user.is_2fa_enabled:
        code = email_utils.generate_2fa_code()
        otp_entry = models.OTPCode(email=user.email, code=code.upper(), purpose="login_2fa")
        db.add(otp_entry)
        await db.commit()
        await email_utils.send_2fa_code(user.email, code)
        return {"message": "2FA Code sent", "require_2fa": True}

    # Если 2FA выключена
    access_token = security.create_access_token(
        data={"sub": user.email, "id": user.id, "role": user.role}
    )
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "user_id": user.id, 
        "name": user.name, 
        "role": user.role, 
        "require_2fa": False
    }

# === ПРОВЕРКА 2FA КОДА ===
@app.post("/auth/verify-2fa-login", response_model=schemas.Token)
async def verify_2fa_login(data: schemas.VerifyCodeRequest, db: AsyncSession = Depends(get_db)):
    code_check = data.code.upper().strip()
    result = await db.execute(select(models.OTPCode).where(
        models.OTPCode.email == data.email, models.OTPCode.code == code_check, models.OTPCode.purpose == "login_2fa"
    ))
    otp_record = result.scalars().first()
    
    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid 2FA code")
    
    result_user = await db.execute(select(models.User).where(models.User.email == data.email))
    user = result_user.scalars().first()
    
    access_token = security.create_access_token(data={"sub": user.email, "id": user.id, "role": user.role})
    await db.delete(otp_record)
    await db.commit()
    
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "user_id": user.id, 
        "name": user.name, 
        "role": user.role, 
        "require_2fa": False
    }

# === КОНТЕНТ ===
@app.get("/activities", response_model=List[schemas.ActivityResponse])
async def get_all_activities(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Activity).limit(limit))
    return result.scalars().all()

# === ПРОФИЛЬ (Тест токена) ===
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    try:
        payload = security.jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email: str = payload.get("sub")
        if email is None: raise HTTPException(status_code=401, detail="Invalid token")
    except security.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    result = await db.execute(select(models.User).where(models.User.email == email))
    user = result.scalars().first()
    if user is None: raise HTTPException(status_code=401, detail="User not found")
    return user

@app.get("/users/me", response_model=schemas.UserResponse)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user