"""
Точка входа Kivy-приложения.

Использует ScreenManager для навигации между экранами.
"""

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import NoTransition, ScreenManager

from app.screens.unlock import UnlockScreen
from app.screens.vault import VaultScreen
from app.utils import resource_path
from app.widgets.toolbar import Toolbar  # noqa: F401 - registers class with Kivy Factory


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
    sm.add_widget(UnlockScreen(name="unlock"))
    sm.add_widget(VaultScreen(name="vault"))

    return sm


# --------------------------------------------------------------------------------------


def main() -> None:
  """Точка входа для CLI / pyproject.scripts."""

  CesarVaultApp().run()


# --------------------------------------------------------------------------------------

if __name__ == "__main__":
  main()
