from apscheduler.schedulers.background import BackgroundScheduler
import sentry_sdk
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from src.database import SessionLocal
from src.news.model import NewsArticle
from src.news.service import get_news_article
from src.news.router import router as news_router
from src.user.router import router as user_router
from src.price.router import router as price_router
from src.config import SENTRY_DSN, TRACES_SAMPLE_RATE, PROFILES_SAMPLE_RATE
from src.crawler.udn_crawler import UDNCrawler

app = FastAPI()
bgs = BackgroundScheduler()
crawler = UDNCrawler()

sentry_sdk.init(
    dsn=SENTRY_DSN,
    traces_sample_rate=TRACES_SAMPLE_RATE,
    profiles_sample_rate=PROFILES_SAMPLE_RATE,
)

app.add_middleware(
    CORSMiddleware,  # noqa
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def start_scheduler():
    db = SessionLocal()
    if db.query(NewsArticle).count() == 0:
        # should change into simple factory pattern
        crawler.startup("價格")
    db.close()
    bgs.add_job(get_news_article, "interval", minutes=100)
    bgs.start()

@app.on_event("shutdown")
def shutdown_scheduler():
    bgs.shutdown()

app.include_router(news_router, prefix="/api/v1/news")
app.include_router(user_router, prefix="/api/v1/user")
app.include_router(price_router, prefix="/api/v1/prices")