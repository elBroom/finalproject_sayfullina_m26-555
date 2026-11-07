from abc import ABC, abstractmethod
from typing import Dict

import requests

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.config import ParserConfig


class BaseApiClient(ABC):
    @abstractmethod
    def fetch_rates(self, config: ParserConfig) -> Dict[str, float]:
        pass


class CoinGeckoClient(BaseApiClient):
    def fetch_rates(self, config: ParserConfig) -> Dict[str, float]:
        ids = ",".join([
            config.CRYPTO_ID_MAP[c]
            for c in config.CRYPTO_CURRENCIES
            if c in config.CRYPTO_ID_MAP
        ])
        vs_currencies = config.BASE_CURRENCY

        url = f"{config.COINGECKO_URL}?ids={ids}&vs_currencies={vs_currencies}"

        try:
            response = requests.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            rates = {}
            for crypto_code, crypto_data in data.items():
                if vs_currencies in crypto_data:
                    # Преобразуем ID обратно в тикер для ключа
                    ticker = next((k for k, v in config.CRYPTO_ID_MAP.items()
                                   if v == crypto_code), crypto_code)
                    rates[f"{ticker}_{vs_currencies}"] = crypto_data[vs_currencies]

            return rates
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"Ошибка CoinGecko: {str(e)}")


class ExchangeRateApiClient(BaseApiClient):
    def fetch_rates(self, config: ParserConfig) -> Dict[str, float]:
        if not config.EXCHANGERATE_API_KEY:
            raise ApiRequestError("API ключ ExchangeRate-API не настроен.")

        url = (f"{config.EXCHANGERATE_API_URL}/{config.EXCHANGERATE_API_KEY}"
               f"/latest/{config.BASE_CURRENCY}")

        try:
            response = requests.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            if data.get("result") != "success":
                raise ApiRequestError("Ошибка API: Не удалось получить курсы.")

            rates = {}
            base = config.BASE_CURRENCY

            for fiat_code in config.FIAT_CURRENCIES:
                if fiat_code in data.get("rates", {}):
                    rate = data["rates"][fiat_code]
                    # Формат: FIAT_USD (например, EUR_USD)
                    # Если базовая валюта USD, то EUR_USD = 0.927 (1 USD = 0.927 EUR)
                    # Но обычно нам нужен курс конвертации FROM -> TO.
                    # В данном примере мы сохраняем курс относительно BASE_CURRENCY.
                    # Если BASE_CURRENCY = USD, то EUR_USD означает "сколько USD за 1 EUR"?
                    # Нет, API возвращает: 1 USD = X EUR.
                    # Чтобы получить курс EUR -> USD, нужно 1 / X.
                    # Однако, для простоты кэширования в Core Service, часто хранят именно то, что вернул API.
                    # Давайте будем хранить как "BASE_CURRENCY_TO_FIAT" или "FIAT_TO_BASE_CURRENCY"?
                    # В задании сказано: "from_currency: EUR, to_currency: USD, rate: 0.927".
                    # Это значит 1 USD = 0.927 EUR.
                    # Но в rates.json мы хотим хранить пары.
                    # Давайте стандартизируем: "BASE_TO_FIAT" или "FIAT_TO_BASE".
                    # Для удобства Core Service, пусть ключ будет "FIAT_BASE" (например, EUR_USD),
                    # а значение — курс 1 USD = X EUR.
                    # Если Core Service хочет курс EUR -> USD, он сделает 1/rate.
                    # Или, чтобы было понятнее, сохраним как "USD_EUR" (1 USD = 0.927 EUR).
                    # Но в задании пример: "EUR_USD": 1.0786 (это 1 EUR = 1.0786 USD).
                    # Значит, нам нужно инвертировать ответ API, если мы хотим хранить "FROM_TO".

                    # Интерпретация задания: "from_currency: EUR, to_currency: USD, rate: 0.927"
                    # Это 1 USD = 0.927 EUR.
                    # Если мы хотим хранить "EUR_USD" как курс конвертации EUR -> USD, то это 1/0.927 = 1.0786.

                    # Реализуем сохранение в формате "BASE_TO_FIAT" (1 USD = X EUR) для простоты,
                    # но в задании пример rates.json показывает "EUR_USD": 1.0786.
                    # Значит, нам нужно инвертировать.

                    inverted_rate = 1.0 / rate
                    rates[f"{fiat_code}_{base}"] = inverted_rate

            return rates
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"Ошибка ExchangeRate-API: {str(e)}")
