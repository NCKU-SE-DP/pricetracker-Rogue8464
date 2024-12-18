"""
UDN News Scraper Module

This module provides the UDNCrawler class for fetching, parsing, and saving news articles from the UDN website.
The class extends the NewsCrawlerBase and includes functionalities to search for news articles based on a search term,
parse the details of individual articles, and save them to a database using SQLAlchemy ORM.

Classes:
    UDNCrawler: A class to scrape news from UDN.

Exceptions:
    DomainMismatchException: Raised when the URL domain does not match the expected domain for the crawler.

Usage Example:
    crawler = UDNCrawler(timeout=10)
    headlines = crawler.startup("technology")
    for headline in headlines:
        news = crawler.parse(headline.url)
        crawler.save(news, db_session)

UDNCrawler Methods:
    __init__(self, timeout: int = 5): Initializes the crawler with a default timeout for HTTP requests.
    startup(self, search_term: str) -> list[Headline]: Fetches news headlines for a given search term across multiple pages.
    get_headline(self, search_term: str, page: int | tuple[int, int]) -> list[Headline]: Fetches news headlines for specified pages.
    _fetch_news(self, page: int, search_term: str) -> list[Headline]: Helper method to fetch news headlines for a specific page.
    _create_search_params(self, page: int, search_term: str): Creates the parameters for the search request.
    _perform_request(self, params: dict): Performs the HTTP request to fetch news data.
    _parse_headlines(response): Parses the response to extract headlines.
    parse(self, url: str) -> News: Parses a news article from a given URL.
    _extract_news(soup, url: str) -> News: Extracts news details from the BeautifulSoup object.
    save(self, news: News, db: Session): Saves a news article to the database.
    _commit_changes(db: Session): Commits the changes to the database with error handling.
"""

from requests import Response
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from src.news.config import CHANNEL_ID
from src.config import UDN_NEWS_API_URL
from src.crawler.crawler_base import NewsCrawlerBase, Headline, News, NewsWithSummary
from urllib.parse import quote
import requests
from src.logger_config import logger

class UDNCrawler(NewsCrawlerBase):

    def __init__(self, timeout: int = 5) -> None:
        self.news_website_url = UDN_NEWS_API_URL
        self.channel_id = CHANNEL_ID
        self.timeout = timeout

    def startup(self, search_term: str) -> list[Headline]:
        """
        Initializes the application by fetching news headlines for a given search term across multiple pages.
        This method is typically called at the beginning of the program when there is no data available,
        hence it fetches headlines from the first 10 pages.

        :param search_term: The term to search for in news headlines.
        :return: A list of Headline namedtuples containing the title and URL of news articles.
        :rtype: list[Headline]
        """
        return self.get_headline(search_term, page=(1, 10))

    def get_headline(self, search_term: str, page: int | tuple[int, int]) -> list[Headline]:
        all_news_data = []
        for news in self._fetch_news(page,search_term):
            all_news_data.append(news)
        return all_news_data

    def _fetch_news(self, page: int, search_term: str) -> list[Headline]:
        news_data = []
        for p in page:
            params = self._create_search_params(p,search_term)
            response = self._perform_request(self.news_website_url,params)
            news_data.append(response.json()["lists"])
        return news_data

    def _create_search_params(self, page: int, search_term: str) -> dict:
        params = {
            "page": page,
            "id": f"search:{quote(search_term)}",
            "channelId": self.channel_id,
            "type": "searchword",
        }
        return params

    def _perform_request(self, url: str | None = None, params: dict | None = None) -> Response:
        try:
            response = requests.get(url, params=params)
        except Exception as e:
            logger.error(f"Error happened during performing news api requests:{e}",exc_info=True)
            response = None
        return response

    @staticmethod
    def _parse_headlines(response: Response) -> list[Headline]:
        paragraphs = [
            p.text
            for p in response.find_all("p")
            if p.text.strip() != "" and "▪" not in p.text
        ]
        return paragraphs

    def parse(self, url: str) -> News:
        response = self._perform_request(url)
        try:
            soup = BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            logger.error(f"Error happened during parsing news:{e}",exc_info=True)
            return None
        title,time,content_section = self._extract_news(soup)
        paragraphs = self._parse_headlines(content_section)
        detailed_news =  {
            "url": url,
            "title": title,
            "time": time,
            "content": paragraphs,
        }
        return detailed_news
    @staticmethod
    def _extract_news(soup: BeautifulSoup, url: str) -> News:
        try:
            title = soup.find("h1", class_="article-content__title").text
        except Exception as e:
            title = "無法取得標題"
            logger.error(f"Unable to fetch news title:{e}",exc_info=True,)
        try:
            time = soup.find("time", class_="article-content__time").text
        except Exception as e:
            time = "無法取得時間"
            logger.error(f"Unable to fetch news time:{e}",exc_info=True,)
        try:
            content_section = soup.find("section", class_="article-content__editor")
        except Exception as e:
            content_section = "無法取得內文"
            logger.error(f"Unable to fetch news content:{e}",exc_info=True,)
        return title,time,content_section

    def save(self, news: NewsWithSummary, db: Session):
        db.add(news)
        self._commit_changes(db)
        db.close()

    @staticmethod
    def _commit_changes(db: Session):
        try:
            db.commit()
        except Exception as e:
            logger.error(f"Error:{e}",exc_info=True,)