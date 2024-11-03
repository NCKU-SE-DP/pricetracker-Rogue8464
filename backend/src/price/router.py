from fastapi import APIRouter, Query
import requests
from src.price.config import PRICE_API_URL

router = APIRouter()

@router.get("/necessities-price")
def get_necessities_prices(
        category=Query(None), commodity=Query(None)
):
    return requests.get(
        PRICE_API_URL,
        params={"CategoryName": category, "Name": commodity},
    ).json()