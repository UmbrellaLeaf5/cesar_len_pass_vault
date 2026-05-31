"""
Точка входа Kivy-приложения.

Использует ScreenManager для навигации между экранами.
"""

import os
import sys


# Android (Buildozer/p4a): src/ лежит в app bundle, но не на sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import NoTransition, ScreenManager

from app.screens.setup import SetupScreen
from app.screens.unlock import UnlockScreen
from app.screens.vault import VaultScreen
from app.utils import resource_path
from app.widgets.toolbar import Toolbar  # noqa: F401 - registers class with Kivy Factory
from cesar_len_pass_vault.config import is_configured


# --------------------------------------------------------------------------------------

Builder.load_file(resource_path("app/main.kv"))

# --------------------------------------------------------------------------------------


class CesarVaultApp(App):
  """
  Основной класс приложения.
  """

  master_password: str = ""

  # --------------------------------------------------------------------------------------

  def build(self) -> ScreenManager:
    """Создаёт корневой виджет с ScreenManager."""

    self.icon = resource_path("images/leaves.png")
    self.title = "CesarLen PassVault"

    sm = ScreenManager(transition=NoTransition())
    sm.add_widget(SetupScreen(name="setup"))
    sm.add_widget(UnlockScreen(name="unlock"))
    sm.add_widget(VaultScreen(name="vault"))

    # Роутинг: если не настроено → Setup, иначе → Unlock
    sm.current = "setup" if not is_configured() else "unlock"

    return sm


# --------------------------------------------------------------------------------------


def main() -> None:
  """Точка входа для CLI / pyproject.scripts."""

  CesarVaultApp().run()


# --------------------------------------------------------------------------------------

if __name__ == "__main__":
  main()
