# ValutaTrade Hub

**ValutaTrade Hub** — это консольное приложение для симуляции торгового терминала с поддержкой мультивалютных портфелей. Проект демонстрирует архитектуру микросервисов, работу с внешними API (CoinGecko, ExchangeRate-API), кэширование данных и управление состоянием пользователя.

## Возможности

- **Аутентификация**: Регистрация и вход пользователей с безопасным хешированием паролей (SHA-256 + salt).
- **Мультивалютные портфели**: Поддержка фиатных (USD, EUR) и криптовалют (BTC, ETH, SOL).
- **Симуляция торговли**: Покупка и продажа валют по актуальным курсам.
- **Курсовая система**:
  - Автоматическое обновление из реальных API (CoinGecko для крипты, ExchangeRate-API для фиата).
  - Умный кэш с сохранением истории изменений.
- **CLI интерфейс**: Удобная командная строка для управления портфелем и курсами.
- **Модульная архитектура**: Разделение логики на слои (Core, Parser Service, CLI, Infra).

## Установка

### Установочные команды

1. **Клонирование репозитория**:
   ```bash
   git clone https://github.com/elBroom/finalproject_sayfullina_m26-555.git
   cd valutatrade_hub
   ```

2. **Установка зависимостей**:
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source .venv/bin/activate
    make build
    make install
    ```

3. **Настройка переменных окружения**:
   ```bash
   export EXCHANGERATE_API_KEY=ваш_ключ_из_exchange_rate_api
   ```

## Использование

### Запуск CLI

```bash
valutatrade-hub
```

### Команды CLI

| Команда | Описание | Обязательные параметры                                                                              |
|---------|----------|-----------------------------------------------------------------------------------------------------|
| `register` | Создать нового пользователя | `--username`, `--password` (мин. 4 символа)                                                         |
| `login` | Войти в систему | `--username`, `--password`                                                                          |
| `show-portfolio` | Отобразить портфель пользователя | `--base` (базовая валюта, опц.)                                                                     |
| `buy` | Купить валюту | `--currency`, `--amount`                                                                            |
| `sell` | Продать валюту | `--currency`, `--amount`                                                                            |
| `get-rate` | Получит-current курс пары валют | `--from`, `--to`                                                                                    |
| `update-rates` | Обновление курсов вручную | `--source` (источник загрузки, опц.) 'coingecko' для крипто валют, 'exchangerate' для фиатных валют |
| `help` | Показать справку | —                                                                                                   |
| `exit` | Выйти из программы | —                                                                                                   |

### Примеры использования

**1. Регистрация и вход:**
```bash
# Регистрация
register --username trader1 --password secret123

# Вход
login --username trader1 --password secret123
```

**2. Управление портфелем:**
```bash
# Купить 0.5 BTC
buy --currency BTC --amount 0.5

# Продать 0.01 BTC
sell --currency BTC --amount 0.01

# Показать портфель в USD
show-portfolio --base USD
```

**3. Проверка курсов:**
```bash
# Получить курс EUR -> USD
get-rate --from EUR --to USD
```

**3. Обновление курсов вручную:**
```bash
# Обновить валюту по апи
update-rates
```

### Демонстрация CLI
```bash
export EXCHANGERATE_API_KEY=cc0a2f897c2416242f84755a
valutatrade-hub
register --username trader2 --password secret123
login --username trader2 --password secret123
buy --currency ABC --amount 0.5
buy --currency BTC --amount 0.03
sell --currency BTC --amount 0.05
sell --currency BTC --amount 0.01
show-portfolio --base USD
get-rate --from EUR --to USD
```

[![asciicast](https://asciinema.org/a/kQrUkVz5bApG0hir](https://asciinema.org/a/kQrUkVz5bApG0hir)

### Демонстрация загрузки валют
```bash
valutatrade-hub
update-rates
```
[![asciicast](https://asciinema.org/a/8Ywd48iyGyqERMBw](https://asciinema.org/a/8Ywd48iyGyqERMBw)





## Архитектура проекта

Проект structuрован по принципу микросервисов:

```
valutatrade_hub/
├── cli/                # Интерфейс командной строки
│   ├── interface.py    # Логика CLI
│   └── __init__.py
├── core/               # Основная бизнес-логика
│   ├── usecases.py     # Репозиторий и сценарии использования
│   ├── models.py       # Модели данных (User, Wallet, Portfolio)
│   ├── utils.py        # Вспомогательные функции
│   └── currencies.py   # Константы валют
├── parser_service/     # Сервис парсинга курсов
│   ├── api_clients.py  # Клиенты API (CoinGecko, ExchangeRate-API)
│   ├── updater.py      # Логика обновления данных
│   ├── scheduler.py    # Планировщик задач
│   ├── storage.py      # Сохранение кэша и истории
│   └── config.py       # Конфигурация
├── infra/              # инфраструктуры (базы данных, логирование)
│   ├── database.py
│   └── logging_config.py
├── data/               # Файлы данных (создаются при запуске)
│   ├── users.json
│   ├── portfolios.json
│   ├── rates.json
│   └── exchange_rates.json
└── valutatrade_hub/    # Корневой пакет
    └── __init__.py
```

### Основные компоненты

#### 1. Core Service
- **Модели**: `User` (авторизация), `Wallet` (баланс), `Portfolio` (коллекция кошельков).
- **Use Cases**: Логика регистрации, входа, торговли, отображения портфеля.
- **Утилиты**: Загрузка/сохранение JSON.

#### 2. Parser Service
- **Задача**: Отдельный сервис для сбора и обновления курсов валют.
- **API**:
  - **CoinGecko**: Криптовалюты ( BTC, ETH, SOL...).
  - **ExchangeRate-API**: Фиатные валюты (USD, EUR, GBP, RUB...).
- **Функции**:
  - `fetch_rates()`: Получение данных с API.
  - `save_cache()`: Сохранение актуальных курсов в `rates.json`.
  - `save_history()`: Запись истории изменений в `exchange_rates.json`.
  - `scheduler`: Автоматическое обновление по расписанию (опционально).

#### 3. CLI Interface
- Универсальный интерфейс для взаимодействия с системой.
- Поддержка аргументов командной строки и интерактивного режима.

## Безопасность

- **Пароли**: Хешируются с использованием SHA-256 и уникального `salt` для каждого пользователя.
- **Кэширование**: Данные курсов хранятся локально для уменьшения числа запросов к API.
- **Валидация**: Строгая проверка входных данных (валюты, суммы, имена пользователей).

