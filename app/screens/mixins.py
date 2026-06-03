"""
Общие миксины для экранов.
"""

from kivy.properties import ListProperty, ObjectProperty


class ErrorScreenMixin:
  """Миксин с общим функционалом отображения ошибок."""

  error_label = ObjectProperty(None)
  _bg_color = ListProperty([0, 0, 0, 1])

  # --------------------------------------------------------------------------------------

  def _set_error(self, error_text: str) -> None:
    """Включить красный фон ошибки с текстом."""

    self._bg_color = [0.4, 0.05, 0.05, 1]  # Бледно-красный
    self.error_label.opacity = 1
    self.error_label.text = error_text

  # --------------------------------------------------------------------------------------

  def _clear_error(self) -> None:
    """Сбросить состояние ошибки к исходному."""

    self.error_label.text = ""
    self.error_label.opacity = 0
    self._bg_color = [0, 0, 0, 1]
