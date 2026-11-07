from datetime import datetime, timezone

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.api_clients import (
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.storage import RatesStorage


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
        print("Starting rates update...")
        last_refresh = datetime.now(timezone.utc).isoformat()

        all_rates = []
        errors = []

        # 1. Обновление криптовалют
        if source_filter is None or source_filter == "coingecko":
            try:
                print("Fetching from CoinGecko...")
                rates = self.coin_client.fetch_rates(self.config)
                for row in rates.values():
                    all_rates.append(row)

                # Сохраняем в историю
                self.storage.save_history(
                    timestamp=last_refresh,
                    source="CoinGecko",
                    status_code=200,
                    rates=rates,
                )
                print(f"CoinGecko OK ({len(rates)} rates)")
            except ApiRequestError as e:
                print(f"Failed to fetch from CoinGecko: {e}")
                errors.append("CoinGecko")

        # 2. Обновление фиатных валют
        if source_filter is None or source_filter == "exchangerate":
            try:
                print("Fetching from ExchangeRate-API...")
                rates = self.exchange_client.fetch_rates(self.config)
                for row in rates.values():
                    all_rates.append(row)

                # Сохраняем в историю
                self.storage.save_history(
                    timestamp=last_refresh,
                    source="ExchangeRate-API",
                    status_code=200,
                    rates=rates,
                )
                print(f"ExchangeRate-API OK ({len(rates)} rates)")
            except ApiRequestError as e:
                print(f"Failed to fetch from ExchangeRate-API: {e}")
                errors.append("ExchangeRate-API")

        # 3. Сохранение кэша
        if all_rates:
            self.storage.save_cache(all_rates, last_refresh)
            print(f"Writing {len(all_rates)} rates to {self.config.RATES_FILE_PATH}...")

        if errors:
            print(f"Update completed with errors. Sources failed: {', '.join(errors)}")
            return False

        print(
            f"Update successful. "
            f"Total rates updated: {len(all_rates)}. "
            f"Last refresh: {last_refresh}")
        return len(all_rates)
