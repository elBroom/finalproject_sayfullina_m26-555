import json
import os
from typing import Any


def load_json_file(filepath: str, default=None):
    if not os.path.exists(filepath):
        return default if default is not None else []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default if default is not None else []


def save_json_file(filepath: str, data: Any):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_rate_dummy(from_currency: str, to_currency: str) -> float:
    data = {
        "EUR_USD": 1.0786,
        "BTC_USD":  59337.21,
        "RUB_USD":  0.01016,
        "ETH_USD":  3720.00,
    }
    if from_currency == to_currency:
        return 1.0

    if f'{from_currency}_{to_currency}' in data:
        return data[f'{from_currency}_{to_currency}']

    if f'{to_currency}_{from_currency}':
        return 1.0 / data[f'{to_currency}_{from_currency}']

    raise ValueError('Нет данных')
