from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=True)
Base = declarative_base()
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def session_opener():
    session = Session(bind=engine)
    try:
        yield session
    finally:
        session.close()