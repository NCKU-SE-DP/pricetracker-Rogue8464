from fastapi import APIRouter, Depends
import json
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from src.database import session_opener
from src.news.model import NewsArticle
from src.news.service import get_article_upvote_details, toggle_news_upvoted_status, get_news_info_by_search_term
from src.user.service import authenticate_user_token
from src.news.schema import NewsSumaryRequestSchema, PromptRequest
from src.news.config import _id_counter
from src.config import OPENAI_API_KEY, OPENAI_MODEL
from src.llm_client.openai_client import OPENAIClient

router = APIRouter()
openaiclient = OPENAIClient(openai_api_key=OPENAI_API_KEY,openai_model=OPENAI_MODEL)

@router.get("/news")
def get_all_news_from_database(db=Depends(session_opener)):
    news = db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    result = []
    for n in news:
        upvotes, upvoted = get_article_upvote_details(n.id, None, db)
        result.append(
            {**n.__dict__, "upvotes": upvotes, "is_upvoted": upvoted}
        )
    return result

@router.get("/user_news")
def get_user_upvoted_news(
        db=Depends(session_opener),
        u=Depends(authenticate_user_token)
):
    news = db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    result = []
    for article in news:
        upvotes, upvoted = get_article_upvote_details(article.id, u.id, db)
        result.append(
            {
                **article.__dict__,
                "upvotes": upvotes,
                "is_upvoted": upvoted,
            }
        )
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
    message = toggle_news_upvoted_status(id, user.id, db)
    return {"message": message}

@router.post("/search_news")
async def search_news(request: PromptRequest):
    news_list = []
    keywords = openaiclient.extract_keywords(request.prompt)
    # todo: should change into simple factory pattern
    news_items = get_news_info_by_search_term(keywords, is_initial=False)
    for news in news_items:
        try:
            response = requests.get(news["titleLink"])
            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.find("h1", class_="article-content__title").text
            time = soup.find("time", class_="article-content__time").text
            # 擷取文章的主要內容
            content_section = soup.find("section", class_="article-content__editor")

            paragraphs = [
                p.text
                for p in content_section.find_all("p")
                if p.text.strip() != "" and "▪" not in p.text
            ]
            detailed_news = {
                "url": news["titleLink"],
                "title": title,
                "time": time,
                "content": paragraphs,
            }
            detailed_news["content"] = " ".join(detailed_news["content"])
            detailed_news["id"] = next(_id_counter)
            news_list.append(detailed_news)
        except Exception as e:
            print(e)
    return sorted(news_list, key=lambda x: x["time"], reverse=True)