from sqlalchemy.orm import Session
from urllib.parse import quote
import requests
from sqlalchemy import delete, insert, select
from src.news.model import NewsArticle, user_news_association_table
from src.config import UDN_NEWS_API_URL
from src.news.config import CHANNEL_ID
from src.crawler.udn_crawler import UDNCrawler
from src.llm_client.openai_client import OPENAIClient

crawler = UDNCrawler()
openaiclient = OPENAIClient()

def add_news_to_database(news_data):
    session = Session()
    crawler.save(news_data,session)

def get_news_info_by_search_term(search_term, is_initial=False):
    all_news_data = []
    # 若為初始載入，遍歷頁面以獲取多頁新聞資料，實際上不會載入全部新聞
    if is_initial:
        all_news_data = crawler.get_headline(search_term,(1,10))
    else:
        params = {
            "page": 1,
            "id": f"search:{quote(search_term)}",
            "channelId": CHANNEL_ID,
            "type": "searchword",
        }
        response = requests.get(UDN_NEWS_API_URL, params=params)

        all_news_data = response.json()["lists"]
    return all_news_data

def get_news_article(is_initial=False):
    news_data = get_news_info_by_search_term("價格", is_initial=is_initial)
    for news in news_data:
        title = news["title"]
        relevance = openaiclient.evaluate_relevance(title)
        if relevance == "high":
            detailed_news = crawler.parse(news["titleLink"])
            news_summary = openaiclient.sum_up_news(" ".join(detailed_news["content"]))
            add_news_to_database(news_summary)

def get_news_exist_status(news_id, db: Session):
    return db.query(NewsArticle).filter_by(id=news_id).first() is not None

def toggle_news_upvoted_status(news_id, user_id, db):
    existing_upvote = db.execute(
        select(user_news_association_table).where(
            user_news_association_table.c.news_articles_id == news_id,
            user_news_association_table.c.user_id == user_id,
        )
    ).scalar()

    if existing_upvote:
        delete_stmt = delete(user_news_association_table).where(
            user_news_association_table.c.news_articles_id == news_id,
            user_news_association_table.c.user_id == user_id,
        )
        db.execute(delete_stmt)
        db.commit()
        return "Upvote removed"
    else:
        insert_stmt = insert(user_news_association_table).values(
            news_articles_id=news_id, user_id=user_id
        )
        db.execute(insert_stmt)
        db.commit()
        return "Article upvoted"
    
def get_article_upvote_details(article_id, user_id, db):
    count = (
        db.query(user_news_association_table)
        .filter_by(news_articles_id=article_id)
        .count()
    )
    voted = False
    if user_id:
        voted = (
                db.query(user_news_association_table)
                .filter_by(news_articles_id=article_id, user_id=user_id)
                .first()
                is not None
        )
    return count, voted