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

router = APIRouter()


@router.get("/news")
def get_all_news_from_database(db=Depends(session_opener)):
    """
    read new

    :param db:
    :return:
    """
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
    """
    read user new

    :param db:
    :param u:
    :return:
    """
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
    response = {}
    message_content = [
        {
            "role": "system",
            "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
        },
        {"role": "user", "content": f"{payload.content}"},
    ]

    completion = OpenAI(api_key=OPENAI_API_KEY).chat.completions.create(
        model=OPENAI_MODEL,
        messages=message_content,
    )
    result = completion.choices[0].message.content
    if result:
        result = json.loads(result)
        response["summary"] = result["影響"]
        response["reason"] = result["原因"]
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
    prompt = request.prompt
    news_list = []
    message_content = [
        {
            "role": "system",
            "content": "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
        },
        {"role": "user", "content": f"{prompt}"},
    ]

    completion = OpenAI(api_key=OPENAI_API_KEY).chat.completions.create(
        model=OPENAI_MODEL,
        messages=message_content,
    )
    keywords = completion.choices[0].message.content
    # should change into simple factory pattern
    news_items = get_news_info_by_search_term(keywords, is_initial=False)
    for news in news_items:
        try:
            response = requests.get(news["titleLink"])
            soup = BeautifulSoup(response.text, "html.parser")
            # 標題
            title = soup.find("h1", class_="article-content__title").text
            time = soup.find("time", class_="article-content__time").text
            # 定位到包含文章内容的 <section>
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