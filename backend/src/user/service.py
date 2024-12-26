from fastapi import Depends
from jose import jwt
from datetime import datetime, timedelta
from src.user.model import User
from src.database import session_opener
from src.user.schema import oauth2_scheme
from src.config import JWT_ENCRYPTION_ALGORITHM, JWT_SECRET_KEY
from src.user.config import password_context
from src.logger_config import logger

def verify_hashed_password(p1, p2):
    return password_context.verify(p1, p2)

def check_user_password_is_correct(db, user_input, password):
    try:
        user = db.query(User).filter(User.username == user_input).first()
        user_hashed_password = user.hashed_password
    except Exception as e:
        
        return False
    if not verify_hashed_password(password, user_hashed_password):
        return False
    return user

def authenticate_user_token(
    token = Depends(oauth2_scheme),
    db = Depends(session_opener)
):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ENCRYPTION_ALGORITHM])
        user_token = db.query(User).filter(User.username == payload.get("sub")).first()
    except Exception as e:
        logger.error(f"Error happened during authenticating user token:{e} ",exc_info=True)
        raise
    return user_token

def create_access_token(data, expires_delta=None):
    try:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        print(to_encode)
        encoded_json_webtoken = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ENCRYPTION_ALGORITHM)
    except Exception as e:
        logger.error(f"Error happened during creating access token:{e} ",exc_info=True)
        raise
    return encoded_json_webtoken