from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from src.user.model import User
from src.user.config import password_context
from src.user.service import check_user_password_is_correct, create_access_token, authenticate_user_token
from src.user.schema import UserAuthSchema
from src.database import session_opener
from src.config import TOKEN_TYPE
from src.logger_config import logger

router = APIRouter()

@router.post("/login")
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(session_opener)
):
    user = check_user_password_is_correct(db, form_data.username, form_data.password)
    try:
        access_token = create_access_token(
            data={"sub": str(user.username)}, expires_delta=timedelta(minutes=30)
        )
        return {"access_token": access_token, "TOKEN_TYPE": TOKEN_TYPE}
    except Exception as e:
        logger.error(f"Error happened during creating access token:{e}",exc_info=True)
        raise

@router.post("/register")
def create_user(user: UserAuthSchema, db: Session = Depends(session_opener)):
    try:
        hashed_password = password_context.hash(user.password)
        db_user = User(username=user.username, hashed_password=hashed_password)
    except Exception as e:
        logger.error(f"Error happened during creating new user:{e}",exc_info=True)
        raise
    try:
        db.add(db_user)
        db.commit()
    except Exception as e:
        logger.error(f"Error happened during adding new user to database:{e}",exc_info=True)
        raise
    db.refresh(db_user)
    return db_user

@router.get("/me")
def read_users_me(user=Depends(authenticate_user_token)):
    try:
        username = {"username": user.username}
    except Exception as e:
        logger.warning(f"Error happened during loading username:{e} ",exc_info=True)
        username = {"username":"unable to load username"}
    return username