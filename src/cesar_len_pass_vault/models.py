"""
Модели данных хранилища паролей.
"""

from dataclasses import dataclass, field


@dataclass
class PasswordEntry:
  """
  Запись в хранилище паролей.
  """

  service: str
  login: str
  password: str
  notes: str = ""


@dataclass
class Vault:
  """
  Хранилище паролей.
  Только один Vault на всё приложение.
  """

  entries: list[PasswordEntry] = field(default_factory=list)
