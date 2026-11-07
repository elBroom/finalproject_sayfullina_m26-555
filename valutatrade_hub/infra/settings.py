import tomllib
from pathlib import Path
from typing import Any, Dict, Optional

# Путь к корню проекта (для поиска pyproject.toml)
PROJECT_ROOT = Path(__file__).parent.parent.parent


class SettingsLoader:
    """
    Singleton: Единая точка конфигурации приложения.

    Гарантирует, что в приложении существует ровно один экземпляр настроек.
    Использует метод __new__ для контроля создания экземпляров.
    """

    _instance: Optional['SettingsLoader'] = None
    _config: Dict[str, Any] = {}
    _config_path: Optional[str] = None

    def __new__(cls, *args, **kwargs):
        """
        Метод __new__ контролирует создание экземпляра.
        Если экземпляр уже существует, возвращаем его.
        Это гарантирует Singleton.
        """
        if cls._instance is None:
            # Создаем новый экземпляр
            instance = super().__new__(cls)
            instance._config = {}
            instance._config_path = None
            cls._instance = instance
        return cls._instance

    def __init__(self):
        """
        Инициализация происходит только один раз (при первом вызове).
        Загружает конфигурацию из pyproject.toml или config.json.
        """
        # Проверяем, не был ли уже загружен конфиг
        # (чтобы не перезагружать при каждом вызове)
        if not self._config:
            self._load_config()

    def _load_config(self):
        """
        Загружает конфигурацию из файла pyproject.toml.
        """
        config = {}

        # 1. Пытаемся загрузить из pyproject.toml
        pyproject_path = PROJECT_ROOT / "pyproject.toml"
        if pyproject_path.exists():
            try:
                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)

                # Проверяем наличие секции [tool.valutatrade]
                if "tool" in data and "valutatrade" in data["tool"]:
                    config = data["tool"]["valutatrade"]
                    self._config_path = "pyproject.toml"
                    self._config = config
                    return
            except Exception:
                pass

        # Дефолтные значения, если файлы не найдены
        self._config = {
            "data_dir": "data",
            "rates_ttl_seconds": 300,  # 5 минут
            "default_base_currency": "USD",
            "log_level": "INFO",
            "log_path": "logs"
        }
        self._config_path = "default"

    def reload(self):
        """
        Перезагрузка конфигурации (сброс кэша и повторная загрузка).
        """
        self._config = {}
        self._config_path = None
        self._load_config()

    def get(self, key: str, default: Any = None) -> Any:
        """
        Получение значения по ключу.
        :param key: Ключ конфигурации.
        :param default: Значение по умолчанию, если ключ не найден.
        :return: Значение или default.
        """
        return self._config.get(key, default)

    def get_all(self) -> Dict[str, Any]:
        """Возвращает полную копию конфигурации."""
        return self._config.copy()

    def __repr__(self):
        return f"SettingsLoader(config_source={self._config_path})"


# Глобальная переменная для удобного доступа
settings = SettingsLoader()