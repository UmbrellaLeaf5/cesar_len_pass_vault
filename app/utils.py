import os
import sys


def resource_path(relative_path):
  """
  Возвращает абсолютный путь к ресурсу.
  Автоматически определяет базу: откуда бы ни вызвали - из main.py или из
  app/screens/unlock.py.
  """
  if getattr(sys, "frozen", False):
    # EXE: _MEIPASS - это _internal/
    base = sys._MEIPASS  # type: ignore
  elif is_android_platform():
    # Android: p4a устанавливает CWD в корень приложения
    base = os.getcwd()
  else:
    current = os.path.dirname(os.path.abspath(__file__))

    # Поднимаемся по папкам, пока не найдём main.py
    while current and not os.path.exists(os.path.join(current, "main.py")):
      parent = os.path.dirname(current)
      if parent == current:  # Дошли до корня диска
        break

      current = parent

    base = current

  return os.path.join(base, relative_path)


def is_android_platform() -> bool:
  """True на Android (Buildozer/p4a), False на desktop."""

  try:
    from android.storage import app_storage_path  # type: ignore  # noqa: F401, PLC0415

    return True
  except ImportError:
    return False
