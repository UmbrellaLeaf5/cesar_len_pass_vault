"""
Попап с настройками хранилища.
"""

from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup


# --------------------------------------------------------------------------------------

Builder.load_file("app/popups/settings.kv")

# --------------------------------------------------------------------------------------


class SettingsPopup(Popup):
  """
  Попап с настройками хранилища.
  """

  backup_callback = ObjectProperty(None)

  # --------------------------------------------------------------------------------------

  def trigger_backup(self) -> None:
    """Вызвать callback загрузки backup и закрыть попап."""

    if self.backup_callback:
      self.backup_callback()

    self.dismiss()
