from fastapi import APIRouter, Depends
import requests
from bs4 import BeautifulSoup
from src.database import session_opener
from src.news.model import NewsArticle
from src.news.service import get_article_upvote_details, toggle_news_upvoted_status, get_news_info_by_search_term
from src.user.service import authenticate_user_token
from src.news.schema import NewsSumaryRequestSchema, PromptRequest, NewsSumaryCustomModelSchema
from src.news.config import _id_counter
from src.llm_client.openai_client import OPENAIClient
from src.llm_client.anthropic_client import ANTHROPICClient
from src.logger_config import logger
from src.crawler.udn_crawler import UDNCrawler

router = APIRouter()
openaiclient = OPENAIClient()
crawler = UDNCrawler()

@router.get("/news")
def get_all_news_from_database(db=Depends(session_opener)):
    try:
        news = db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    except Exception as e:
        logger.error(f"Error happened during fetching news from database:{e}",exc_info=True)
        raise
    result = []
    for n in news:
        try:
            upvotes, upvoted = get_article_upvote_details(n.id, None, db)
            result.append(
                {**n.__dict__, "upvotes": upvotes, "is_upvoted": upvoted}
            )
        except Exception as e:
            logger.warning(f"Error happened during fetching news upvote details:{e}",exc_info=True)
    return result

@router.get("/user_news")
def get_user_upvoted_news(
        db=Depends(session_opener),
        u=Depends(authenticate_user_token)
):
    try:
        news = db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    except Exception as e:
        logger.error(f"Error happened during fetching news from database:{e}",exc_info=True)
        raise
    result = []
    for article in news:
        try:
            upvotes, upvoted = get_article_upvote_details(article.id, u.id, db)
            result.append(
                {
                    **article.__dict__,
                    "upvotes": upvotes,
                    "is_upvoted": upvoted,
                }
            )
        except Exception as e:
            logger.warning(f"Error happened during fetching news upvote details:{e}",exc_info=True)
    return result

@router.post("/news_summary")
async def get_news_summary(
    payload: NewsSumaryRequestSchema, u=Depends(authenticate_user_token)
):
    response = openaiclient.sum_up_news(payload.content)
    return response

@router.post("/{id}/upvote")
def upvote_article(
        id,
        db=Depends(session_opener),
        user=Depends(authenticate_user_token),
):
    try:
        message = toggle_news_upvoted_status(id, user.id, db)
    except Exception as e:
        logger.error(f"Error happened during toggle news upvoted status:{e}",exc_info=True)
        raise
    return {"message": message}

@router.post("/search_news")
async def search_news(request: PromptRequest):
    news_list = []
    keywords = openaiclient.extract_keywords(request.prompt)
    # todo: should change into simple factory pattern
    news_items = get_news_info_by_search_term(keywords, is_initial=False)
    for news in news_items:
        try:
            detailed_news = crawler.parse(news["titleLink"])
            detailed_news["content"] = " ".join(detailed_news["content"])
            detailed_news["id"] = next(_id_counter)
            news_list.append(detailed_news)
        except Exception as e:
            logger.warning(f"Error happened during parsing news:{e}",exc_info=True)
    return sorted(news_list, key=lambda x: x["time"], reverse=True)

@router.post("/news_summary_custom_model")
async def get_news_summary_custom_model(
    payload: NewsSumaryCustomModelSchema
):
    if(payload.model == "openai"):
        llm_client = OPENAIClient()
    elif(payload.model == "anthropic"):
        llm_client = ANTHROPICClient()
    else:
        return "Invalid Client!"
    response = llm_client.sum_up_news(payload.content)
    return response