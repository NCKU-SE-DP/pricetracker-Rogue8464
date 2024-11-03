from sqlalchemy.orm import Session
from urllib.parse import quote
import requests
from openai import OpenAI
from bs4 import BeautifulSoup
import json
from sqlalchemy import delete, insert, select
from src.news.model import NewsArticle, user_news_association_table
from src.config import OPENAI_API_KEY, OPENAI_MODEL, UDN_NEWS_API_URL
from src.news.config import CHANNEL_ID

def add_news_to_database(news_data):
    """
    add new to db
    :param news_data: news info
    :return:
    """
    session = Session()
    session.add(NewsArticle(
        url=news_data["url"],
        title=news_data["title"],
        time=news_data["time"],
        content=" ".join(news_data["content"]),  # 將內容list轉換為字串
        summary=news_data["summary"],
        reason=news_data["reason"],
    ))
    session.commit()
    session.close()

def get_news_info_by_search_term(search_term, is_initial=False):
    """
    get new

    :param search_term:
    :param is_initial:
    :return:
    """
    all_news_data = []
    # iterate pages to get more news data, not actually get all news data
    if is_initial:
        news_data = []
        for page in range(1, 10):
            params = {
                "page": page,
                "id": f"search:{quote(search_term)}",
                "channelId": CHANNEL_ID,
                "type": "searchword",
            }
            response = requests.get(UDN_NEWS_API_URL, params=params)
            news_data.append(response.json()["lists"])

        for news in news_data:
            all_news_data.append(news)
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
    """
    get new info

    :param is_initial:
    :return:
    """
    news_data = get_news_info_by_search_term("價格", is_initial=is_initial)
    for news in news_data:
        title = news["title"]
        message_content = [
            {
                "role": "system",
                "content": "你是一個關聯度評估機器人，請評估新聞標題是否與「民生用品的價格變化」相關，並給予'high'、'medium'、'low'評價。(僅需回答'high'、'medium'、'low'三個詞之一)",
            },
            {"role": "user", "content": f"{title}"},
        ]
        ai = OpenAI(api_key=OPENAI_API_KEY).chat.completions.create(
            model=OPENAI_MODEL,
            messages=message_content,
        )
        relevance = ai.choices[0].message.content
        if relevance == "high":
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
            detailed_news =  {
                "url": news["titleLink"],
                "title": title,
                "time": time,
                "content": paragraphs,
            }
            message_content = [
                {
                    "role": "system",
                    "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
                },
                {"role": "user", "content": " ".join(detailed_news["content"])},
            ]

            completion = OpenAI(api_key=OPENAI_API_KEY).chat.completions.create(
                model=OPENAI_MODEL,
                messages=message_content,
            )
            result = completion.choices[0].message.content
            result = json.loads(result)
            detailed_news["summary"] = result["影響"]
            detailed_news["reason"] = result["原因"]
            add_news_to_database(detailed_news)

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

# def generate_summary(content):
#     m = [
#         {
#             "role": "system",
#             "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
#         },
#         {"role": "user", "content": f"{content}"},
#     ]
#
#     completion = OpenAI(api_key=OPENAI_API_KEY).chat.completions.create(
#         model=OPENAI_MODEL,
#         messages=m,
#     )
#     return completion.choices[0].message.content

# def extract_search_keywords(content):
#     m = [
#         {
#             "role": "system",
#             "content": "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
#         },
#         {"role": "user", "content": f"{content}"},
#     ]
#
#     completion = OpenAI(api_key=OPENAI_API_KEY).chat.completions.create(
#         model=OPENAI_MODEL,
#         messages=m,
#     )
#     return completion.choices[0].message.content