"""
Перечисления (enums) для приложения.
"""

from enum import Enum


class VaultState(Enum):
  """Состояния экрана хранилища."""

  EMPTY = "empty"
  LOADED = "loaded"
  LOADING = "loading"
  SPLIT = "split"
