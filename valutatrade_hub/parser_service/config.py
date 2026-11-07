import os
from dataclasses import dataclass


@dataclass
class ParserConfig:
    # API Ключи (загружаются из переменных окружения)
    EXCHANGERATE_API_KEY: str = os.getenv("EXCHANGERATE_API_KEY", "TEST")

    # Эндпоинты
    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"

    # Списки валют
    BASE_CURRENCY: str = "USD"
    FIAT_CURRENCIES: tuple = ("EUR", "GBP", "RUB")
    CRYPTO_CURRENCIES: tuple = ("BTC", "ETH", "SOL")

    # Карта соответствия ID CoinGecko и тикеров
    CRYPTO_ID_MAP: dict = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
    }

    # Пути к файлам
    RATES_FILE_PATH: str = "data/rates.json"
    HISTORY_FILE_PATH: str = "data/exchange_rates.json"

    # Сетевые параметры
    REQUEST_TIMEOUT: int = 10
    TTL_SECONDS: int = 3600  # 1 час для актуальности кэша