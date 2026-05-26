"""
Загрузчики данных из внешних источников
"""
from .dictionary_loader import DictionaryLoader
from .json_dictionary_loader import JsonDictionaryLoader
from .dictionary_registry import DictionaryRegistry

__all__ = ["DictionaryLoader", "JsonDictionaryLoader", "DictionaryRegistry"]