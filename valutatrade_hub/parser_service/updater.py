import logging
from datetime import datetime, timezone

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.api_clients import (
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.storage import RatesStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RatesUpdater:
    def __init__(self, config: ParserConfig):
        self.config = config
        self.storage = RatesStorage(config)
        self.coin_client = CoinGeckoClient()
        self.exchange_client = ExchangeRateApiClient()

    def run_update(self, source_filter: str = None):
        """
        source_filter: 'coingecko', 'exchangerate' или None (все).
        """
        logger.info("Starting rates update...")
        last_refresh = datetime.now(timezone.utc).isoformat()

        all_rates = {}
        errors = []

        # 1. Обновление криптовалют
        if source_filter is None or source_filter == "coingecko":
            try:
                logger.info("Fetching from CoinGecko...")
                rates = self.coin_client.fetch_rates(self.config)
                for pair, rate in rates.items():
                    all_rates[pair] = rate
                    # Сохраняем в историю
                    self.storage.save_history(
                        pair, rate, last_refresh,
                        "CoinGecko",
                        {"raw_id": "bitcoin", "status_code": 200}
                    )
                logger.info(f"CoinGecko OK ({len(rates)} rates)")
            except ApiRequestError as e:
                logger.error(f"Failed to fetch from CoinGecko: {e}")
                errors.append("CoinGecko")

        # 2. Обновление фиатных валют
        if source_filter is None or source_filter == "exchangerate":
            try:
                logger.info("Fetching from ExchangeRate-API...")
                rates = self.exchange_client.fetch_rates(self.config)
                for pair, rate in rates.items():
                    all_rates[pair] = rate
                    self.storage.save_history(
                        pair, rate, last_refresh,
                        "ExchangeRate-API",
                        {"status_code": 200}
                    )
                logger.info(f"ExchangeRate-API OK ({len(rates)} rates)")
            except ApiRequestError as e:
                logger.error(f"Failed to fetch from ExchangeRate-API: {e}")
                errors.append("ExchangeRate-API")

        # 3. Сохранение кэша
        if all_rates:
            self.storage.save_cache(all_rates, last_refresh)
            logger.info(f"Writing {len(all_rates)} rates to {self.config.RATES_FILE_PATH}...")

        if errors:
            logger.warning(f"Update completed with errors. Sources failed: {', '.join(errors)}")
            return False

        logger.info(f"Update successful. Total rates updated: {len(all_rates)}. Last refresh: {last_refresh}")
        return True