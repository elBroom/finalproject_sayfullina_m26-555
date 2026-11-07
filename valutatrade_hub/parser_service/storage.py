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

    def save_history(self, pair: str, rate: float, timestamp: str, source: str, meta: Dict[str, Any]):
        """Сохраняет запись в историю (exchange_rates.json)."""
        try:
            if not os.path.exists(self.history_file):
                data = {"history": []}
            else:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

            if "history" not in data:
                data["history"] = []

            record_id = f"{pair}_{timestamp}"
            record = {
                "id": record_id,
                "from_currency": pair.split("_")[0],
                "to_currency": pair.split("_")[1],
                "rate": rate,
                "timestamp": timestamp,
                "source": source,
                "meta": meta
            }

            # Проверка на дубликаты (по ID)
            existing = next((r for r in data["history"] if r["id"] == record_id), None)
            if not existing:
                data["history"].append(record)

            # Атомарная запись
            temp_file = f"{self.history_file}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            shutil.move(temp_file, self.history_file)

        except Exception as e:
            raise Exception(f"Ошибка записи истории: {e}")

    def save_cache(self, rates: Dict[str, float], last_refresh: str):
        """Сохраняет актуальные курсы в rates.json."""
        try:
            pairs_data = {}
            for pair, rate in rates.items():
                parts = pair.split("_")
                if len(parts) == 2:
                    pairs_data[pair] = {
                        "rate": rate,
                        "updated_at": last_refresh,
                        "source": "Parser Service"
                    }

            cache_data = {
                "pairs": pairs_data,
                "last_refresh": last_refresh
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