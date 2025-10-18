"""
Конфигурация pytest для всего проекта
Этот файл автоматически добавляет корень проекта в PYTHONPATH
"""
import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print(f"✅ PYTHONPATH обновлен: {project_root}")  # Для отладки
