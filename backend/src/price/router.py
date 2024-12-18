from fastapi import APIRouter, Query, HTTPException
import requests
from src.price.config import PRICE_API_URL, TIMEOUT
from src.logger_config import logger

router = APIRouter()

@router.get("/necessities-price")
def get_necessities_prices(
        category=Query(None), commodity=Query(None)
):
    try:
        response = requests.get(
            PRICE_API_URL,
            params={"CategoryName": category, "Name": commodity},
            timeout = TIMEOUT,
        )
        return response.json()
    except requests.exceptions.Timeout as timeout_error:
        logger.error(f"Timeout error:{timeout_error}",exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Error happened during price api request:{e}",exc_info=True)
        return None