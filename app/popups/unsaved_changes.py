"""
Попап предупреждения о несохранённых изменениях при закрытии.
"""

from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup

from app.utils import resource_path


# ----------------------------------------------------------------------------------------

Builder.load_file(resource_path("app/popups/unsaved_changes.kv"))

# ----------------------------------------------------------------------------------------


class UnsavedChangesPopup(Popup):
  """
  Попап: сохранить изменения перед закрытием?
  """

  on_save_close = ObjectProperty(None)
  on_discard = ObjectProperty(None)

  # --------------------------------------------------------------------------------------

  def save_and_close(self) -> None:
    """Сохранить изменения и закрыть приложение."""

    if self.on_save_close:
      self.on_save_close()

  # --------------------------------------------------------------------------------------

  def discard_and_close(self) -> None:
    """Закрыть без сохранения."""

    if self.on_discard:
      self.on_discard()
