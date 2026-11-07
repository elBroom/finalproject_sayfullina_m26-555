import json
import os
import shutil
from typing import Any, Dict

from valutatrade_hub.parser_service.config import ParserConfig


class RatesStorage:
    def __init__(self, config: ParserConfig):
        self.config = config
        self.history_file = config.HISTORY_FILE_PATH
        self.cache_file = config.RATES_FILE_PATH

        # Создаем папку data, если нет
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)

    def save_history(self, timestamp: str, source: str, status_code: int,
                     rates: dict):
        """Сохраняет запись в историю (exchange_rates.json)."""
        try:
            data = []
            if os.stat(self.history_file).st_size > 0:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

            for row in rates.values():
                from_currency = row['from_currency']
                to_currency = row['to_currency']
                rate = row['rate']
                data.append({
                    "id": f"{from_currency}_{to_currency}_{timestamp}",
                    "from_currency": from_currency,
                    "to_currency": to_currency,
                    "rate": rate,
                    "timestamp": timestamp,
                    "source": source,
                    "meta": {
                        "raw_id": row['raw_id'],
                    },
                })

            # Атомарная запись
            temp_file = f"{self.history_file}.tmp"
            with open(temp_file, 'w+', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            shutil.move(temp_file, self.history_file)

        except Exception as e:
            raise Exception(f"Ошибка записи истории: {e}")

    def save_cache(self, api_data: list, last_refresh: str):
        """Сохраняет актуальные курсы в rates.json."""
        try:
            cache_data = {}
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            cache_data["updated_at"] = "Parser Service"
            cache_data["updated_at"] = last_refresh
            for row in api_data:
                from_currency = row['from_currency']
                to_currency = row['to_currency']
                rate = row['rate']

                key = f"{from_currency}_{to_currency}"
                cache_data[key] = {
                    "rate": rate,
                    "updated_at": last_refresh,
                }

            temp_file = f"{self.cache_file}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            shutil.move(temp_file, self.cache_file)

        except Exception as e:
            raise Exception(f"Ошибка записи кэша: {e}")

    def load_cache(self) -> Dict[str, Any]:
        if not os.path.exists(self.cache_file):
            return {"pairs": {}, "last_refresh": None}

        with open(self.cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)