"""
Перечисления (enums) для приложения.
"""

from enum import Enum


class VaultState(Enum):
  """Состояния экрана хранилища."""

  LOADED = "loaded"
  LOADING = "loading"
  ERROR = "error"
