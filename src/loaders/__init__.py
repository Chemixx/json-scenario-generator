"""
Загрузчики данных из внешних источников
"""
from .dictionary_loader import DictionaryLoader
from .dictionary_registry import DictionaryRegistry

__all__ = ["DictionaryLoader", "DictionaryRegistry"]