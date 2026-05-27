"""
Попап выбора версии при рассинхроне редакторов.
"""

from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup


# --------------------------------------------------------------------------------------

Builder.load_file("app/popups/sync.kv")

# --------------------------------------------------------------------------------------


class SyncPopup(Popup):
  """
  Попап: какой редактор использовать при рассинхроне.
  """

  on_choice = ObjectProperty(None)

  # --------------------------------------------------------------------------------------

  def choose_primary(self) -> None:
    """Выбрать основной редактор."""

    if self.on_choice:
      self.on_choice("primary")

    self.dismiss()

  # --------------------------------------------------------------------------------------

  def choose_backup(self) -> None:
    """Выбрать backup редактор."""

    if self.on_choice:
      self.on_choice("backup")

    self.dismiss()

  # --------------------------------------------------------------------------------------

  def choose_cancel(self) -> None:
    """Отмена - ничего не делаем."""

    self.dismiss()
