from abc import ABC, abstractmethod
from typing import Dict

import requests

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.config import ParserConfig


class BaseApiClient(ABC):
    """
    Абстрактный базовый класс для клиентов внешних API.

    Определяет интерфейс для получения курсов валют и обработки ошибок.
    Все конкретные клиентские классы должны наследоваться от этого класса
    и реализовывать метод `fetch_rates`.
    """
    @abstractmethod
    def fetch_rates(self, config: ParserConfig) -> Dict[str, float]:
        """
        Получает курсы валют с внешнего API.

        Args:
            config: Объект конфигурации ParserConfig.

        Returns:
            Dict[str, float]: Словарь пар валют и их курсов
                (ключ: "FROM_TO", значение: rate).

        Raises:
            ApiRequestError: Если запрос не выполнен или данные не были получены.
        """
        pass


class CoinGeckoClient(BaseApiClient):
    """
    Клиент для работы с API CoinGecko.

    Специализируется на получении курсов криптовалют. Использует
    внутреннюю маппинг таблицу для преобразования тикеров в ID CoinGecko.
    Работает без API ключа (бесплатный тариф с лимитами).
    """
    def fetch_rates(self, config: ParserConfig) -> Dict[str, float]:
        # Формируем список ID криптовалют из маппинга
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
                if vs_currencies.lower() in crypto_data:
                    # Преобразуем ID обратно в тикер для ключа
                    ticker = next((k for k, v in config.CRYPTO_ID_MAP.items()
                                   if v == crypto_code), crypto_code)
                    rates[f"{ticker}_{vs_currencies}"] = {
                        'raw_id': crypto_code,
                        'from_currency': ticker,
                        'to_currency': vs_currencies.upper(),
                        'rate': crypto_data[vs_currencies.lower()],
                    }

            return rates
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"Ошибка CoinGecko: {str(e)}")


class ExchangeRateApiClient(BaseApiClient):
    """
    Клиент для работы с API ExchangeRate-API.

    Специализируется на получении курсов фиатных валют. Требует API ключ.
    Автоматически инвертирует курс, если необходимо хранить конвертацию
    в формате FROM -> TO (например, EUR_USD означает 1 EUR = X USD).
    """
    def fetch_rates(self, config: ParserConfig) -> Dict[str, float]:
        # Формируем список ID криптовалют из маппинга
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
                if fiat_code in data.get("conversion_rates", {}):
                    rate = data["conversion_rates"][fiat_code]
                    rates[f"{fiat_code}_{base}"] = {
                        'raw_id': fiat_code,
                        'from_currency': fiat_code,
                        'to_currency': base.upper(),
                        'rate': 1.0 / rate,
                    }

            return rates
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"Ошибка ExchangeRate-API: {str(e)}")
