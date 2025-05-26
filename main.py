from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
from datetime import datetime, timedelta, timezone

from bank import FinancialServices
from models import User, UserOut, UserAuth, Token, Base, Account
from starlette import status
import bcrypt
import os

from jwt import PyJWTError
import jwt

DATABASE_URL = os.getenv('DATABASE_URL')
# DATABASE_URL = 'postgresql://postgres:admin@localhost/test_db'
SECRET_KEY = "614bee45bb6735f3b22a24041059fd33ff42572f493c5896bab894c794a7ad37"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 20
oauth_scheme = OAuth2PasswordBearer(tokenUrl="authorization")

app = FastAPI()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db = next(get_db())
fs = FinancialServices(db=db)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encode_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encode_jwt


async def get_current_user(token: str = Depends(oauth_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=400, detail="Пользователь не найден")
    return user


def hash_password(password: str):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def check_password(plain_password: str, hashed_password: str):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


@app.post("/register", response_model=UserOut)
async def create_user(data: UserAuth, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User exists")
    hashed_password = hash_password(data.password)
    new_user = User(username=data.username, email=data.email, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    new_account = Account(user_id=new_user.id, user_balance=0)
    db.add(new_account)
    db.commit()
    return new_user


@app.post("/authorization", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not check_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/deposit")
async def deposit(amount: float, current_user: User = Depends(get_current_user)):
    try:
        balance = fs.deposit(user_id=current_user.id, amount=amount)
        return {"user_balance": balance}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/withdraw")
async def withdraw(amount: float, current_user: User = Depends(get_current_user)):
    try:
        balance = fs.withdraw(user_id=current_user.id, amount=amount)
        return {"user_balance": balance}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/send")
async def send(amount: float, recipient_id: int, current_user: User = Depends(get_current_user)):
    try:
        sender_balance, recipient_balance = fs.send_to(amount=amount, user_id=current_user.id,
                                                       send_to_user_id=recipient_id)
        return {"sender_balance": sender_balance, "recipient_balance": recipient_balance}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/show-balance")
async def show_balance(current_user: User = Depends(get_current_user)):
    try:
        balance = fs.show_balance(user_id=current_user.id)
        return {"user_balance": balance}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
