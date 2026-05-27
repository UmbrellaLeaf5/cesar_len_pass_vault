"""
Попап для добавления новой записи в хранилище.
"""

import json
from typing import cast

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager

from cesar_len_pass_vault import PasswordEntry


Builder.load_file("app/screens/add_entry.kv")


class AddEntryPopup(Popup):
  """
  Попап для добавления новой записи в хранилище.
  """

  service_input = ObjectProperty(None)
  login_input = ObjectProperty(None)
  password_input = ObjectProperty(None)
  notes_input = ObjectProperty(None)
  error_label = ObjectProperty(None)

  def save(self) -> None:
    """Валидирует поля и вставляет запись в JSON редактора."""

    service = self.service_input.text.strip()
    login = self.login_input.text.strip()
    password = self.password_input.text
    notes = self.notes_input.text

    if not service or not login:
      self.error_label.text = "Сервис и логин обязательны"
      self.error_label.opacity = 1

      return

    entry = PasswordEntry(
      service=service,
      login=login,
      password=password,
      notes=notes,
    )

    app = App.get_running_app()

    assert app is not None

    sm = cast(ScreenManager, app.root)

    vault_screen = sm.get_screen("vault")
    current_json = vault_screen.editor.text.strip()

    if current_json:
      try:
        data = json.loads(current_json)

      except json.JSONDecodeError:
        self.error_label.text = "Ошибка JSON в редакторе"
        self.error_label.opacity = 1

        return

    else:
      data = {"version": 1, "entries": []}

    data.setdefault("entries", []).append(
      {
        "service": entry.service,
        "login": entry.login,
        "password": entry.password,
        "notes": entry.notes,
      }
    )

    vault_screen.editor.text = json.dumps(data, ensure_ascii=False, indent=2)

    self.dismiss()

  def on_open(self) -> None:
    """Сброс полей при открытии."""

    self.service_input.text = ""
    self.login_input.text = ""
    self.password_input.text = ""
    self.notes_input.text = ""
    self.error_label.text = ""
    self.error_label.opacity = 0
    self.service_input.focus = True
