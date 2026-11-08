import json
import os
import shutil
from typing import Any, Dict

from valutatrade_hub.parser_service.config import ParserConfig


class RatesStorage:
    """
    Слой хранения данных для курсов валют.

    Управляет чтением и записью двух типов данных:
    1. Актуальный кэш курсов (rates.json) для Core Service.
    2. История всех обновлений (exchange_rates.json).

    Обеспечивает атомарность операций записи с помощью временных файлов.
    """
    def __init__(self, config: ParserConfig):
        """
         Инициализация хранилища.

         Args:
             config: Объект конфигурации ParserConfig.
         """
        self.config = config
        self.history_file = config.HISTORY_FILE_PATH
        self.cache_file = config.RATES_FILE_PATH

        # Создаем папку data, если нет
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)

    def save_history(self, timestamp: str, source: str, status_code: int,
                     rates: dict):
        """
            Сохраняет запись в историю обновлений курсов.

            Каждая запись содержит пару валют, курс, время обновления,
            источник данных и метаданные (например, ID монеты CoinGecko).

            Args:
                timestamp: ISO-строка времени обновления.
                source: Название источника данных (CoinGecko или ExchangeRate-API).
                status_code: Код ответа апи.
                rates: Текущий курс конвертации.
        """
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
                "status_code": status_code,
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

    def save_cache(self, api_data: list, last_refresh: str):
        """
        Сохраняет актуальные курсы в файл кэша.

        Формат включает пары валют со значениями курсов, временем
        последнего обновления и источником данных.

        Args:
            api_data: Массив курсов.
            last_refresh: ISO-строка времени обновления кэша.
        """
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

    def load_cache(self) -> Dict[str, Any]:
        """
        Загружает текущий кэш курсов из файла.
        """
        if not os.path.exists(self.cache_file):
            return {"pairs": {}, "last_refresh": None}

        with open(self.cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
