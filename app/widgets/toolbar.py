"""
Переиспользуемый виджет панели инструментов.

Горизонтальный BoxLayout с кнопками.
Поддерживает включение/выключение отдельных кнопок.
"""

from kivy.properties import BooleanProperty
from kivy.uix.boxlayout import BoxLayout


class Toolbar(BoxLayout):
  """
  Панель инструментов VaultScreen.
  """

  download_enabled = BooleanProperty(True)
  upload_enabled = BooleanProperty(False)
  add_enabled = BooleanProperty(False)
