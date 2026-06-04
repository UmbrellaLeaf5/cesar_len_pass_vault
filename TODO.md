# TODO - Roadmap

## Список записей вместо голого JSON

**Суть:** заменить TextInput с JSON на RecycleView с отформатированным списком записей. Редактирование — через попап по тапу на элемент. Сохранить raw JSON как read-only toggle.

### Поток данных (новый)

```
download → Vault ──┬── RecycleView (список сервисов)
                   └── Raw-режим: vault_to_json() → readonly TextInput
upload   ← Vault ←── popup edit/delete ← RecycleView (тап по элементу)
upload   ← Vault ←── json_to_vault(editor.text) ← Raw-режим (если редактировали)
```

### Новые файлы

#### `app/popups/edit_entry.py` + `edit_entry.kv` — EditEntryPopup

- Поля: `service`, `login`, `password`, `notes` — предзаполнены из существующей записи
- Кнопка **Show**/**Hide** рядом с password — per-entry show/hide (текст, не смайлик)
- Кнопки внизу: **OK** (закрыть без изменений), **Save** (обновить запись в Vault), **Delete** (красная, удалить запись)
- Gen **нет** — только в AddEntryPopup
- Свойства:
  - `entry_index: int` — индекс записи в `Vault.entries`
  - `entry: PasswordEntry` — копия записи для редактирования
  - `on_save: ObjectProperty` — callback `(index: int, entry: PasswordEntry) -> None`
  - `on_delete: ObjectProperty` — callback `(index: int) -> None`
- `on_open()`: предзаполнить поля, сбросить ошибки, пароль в masked-режиме
- `save()`: валидация (service+login не пустые), вызвать `on_save`, закрыть
- `delete_entry()`: подтверждение? или сразу `on_delete` + закрыть
- `_toggle_password()`: переключить `password_input.password` и текст кнопки Show/Hide
- ESC = dismiss (как в AddEntryPopup)

### Изменяемые файлы

#### 1. `app/screens/vault.kv` — два режима: список ↔ raw JSON

**Режим списка** (по умолчанию):

- `RecycleView` с `viewclass: VaultEntryItem` внутри ScrollView
- Поверх `RecycleView` — `ScrollView` для скролла (как сейчас)
- Каждый item (`VaultEntryItem`): горизонтальный BoxLayout
  - `Label`: `service` (жирный, `text_size` с обрезкой)
  - `Label`: `›` (серая стрелка справа, индикатор что можно нажать)
- `on_touch_down` / кнопка → `root._edit_entry(index)`
- item высота: `'48dp'`, фон: тёмный прямоугольник через canvas

VaultEntryItem:

```
<VaultEntryItem@BoxLayout>:
  orientation: "horizontal"
  size_hint_y: None
  height: '48dp'
  padding: '8dp', 0
  canvas.before:
    Color:
      rgba: 0.12, 0.12, 0.12, 1
    Rectangle:
      pos: self.pos
      size: self.size
  CustomLabel:
    text: root.service
    font_size: '18sp'
    halign: "left"
    valign: "middle"
    text_size: self.width - dp(24), None
    shorten: True
  CustomLabel:
    text: ">"
    font_size: '16sp'
    color: 0.5, 0.5, 0.5, 1
    size_hint_x: None
    width: '24dp'
    halign: "right"
    valign: "middle"
```

В начале RecycleView.data:

```python
[{"service": e.service, "index": i} for i, e in enumerate(vault.entries)]
```

**Raw-режим:**

- Сохранить текущий ScrollView + TextInput (только primary_scroll с editor)
- `editor.readonly = True` в raw-режиме (только просмотр)
- `editor.readonly = False` только если пользователь специально включит редактирование raw
- При переключении список → raw: `editor.text = vault_to_json(self._primary_vault)`
- При переключении raw → список: читать `editor.text`, `json_to_vault()`, обновить список

**Toolbar:**

- Убрать Show/Hide (теперь per-entry в попапе)
- Убрать Copy (не работает на Android)
- Добавить кнопку **Raw** (переключает список ↔ raw JSON):
  ```
  CustomButton:
    id: raw_button
    text: "Raw"
    width: "56dp"
    size_hint_x: None
    disabled: not toolbar.add_enabled
    opacity: 1 if toolbar.add_enabled else 0.4
    on_release: root._toggle_raw()
  ```
- Кнопки тулбара: Download | Upload | +Entry | Raw | \*

**Split-режим:**

- Два RecycleView бок о бок (primary_scroll/backup_scroll)
- Raw-режим: два ScrollView+TextInput как сейчас
- Размеры: `size_hint_x: 0.5` каждому, скрытие backup через `size_hint_x: 0, opacity: 0`

#### 2. `app/screens/vault.py` — замена JSON-строк на Vault-объекты

**Свойства (удалить):**

- `_primary_visible_json` — заменить на `_primary_vault: Vault`
- `_backup_visible_json` — заменить на `_backup_vault: Vault`
- `_passwords_masked` — удалить (show/hide per-entry)
- `hide_button` — удалить
- `copy_button` — удалить
- `preloaded_text: str` — заменить на `preloaded_vault: Vault | None`

**Свойства (добавить):**

- `_primary_vault: Vault = Vault()`
- `_backup_vault: Vault = Vault()`
- `_raw_mode: bool = False`
- `raw_button = ObjectProperty(None)`
- `primary_list: RecycleView` (в split — `backup_list` тоже)

**Методы (удалить):**

- `_mask_passwords()` — не нужен, пароли не показываются в списке
- `_apply_hide_state()` — не нужен
- `_toggle_passwords()` — не нужен
- `_on_editor_text()` — не нужен
- `_on_backup_editor_text()` — не нужен
- `_validate_editor_json()` — не нужен (валидация в попапах)
- `copy_selection()` — уже удалён

**Методы (изменить):**

`on_enter()`:

```python
def on_enter(self, *args):
    if self.preloaded_vault is not None:
        self._primary_vault = self.preloaded_vault
        self._update_ui_by_state(VaultState.LOADED)
        self.preloaded_vault = None
    else:
        self._update_ui_by_state(VaultState.EMPTY)
```

`download()`:

```python
def download(self):
    self._update_ui_by_state(VaultState.LOADING)
    try:
        vault, count = download_primary(self._get_password())
        self._primary_vault = vault
        self._collapse_backup_editor()
        self._update_ui_by_state(VaultState.LOADED)
        self.status_label.text = f"Loaded ... - {count} entries"
    except ...
```

`_download_backup()`:

```python
def _download_backup(self):
    self._update_ui_by_state(VaultState.LOADING)
    try:
        vault, count = download_backup(self._get_password())
        self._backup_vault = vault
        self._update_ui_by_state(VaultState.SPLIT)
        self.status_label.text = f"Loaded backup ... - {count} entries"
    except ...
```

`_do_upload()`:

```python
def _do_upload(self):
    if self._raw_mode:
        # В raw-режиме читаем из editor.text
        try:
            primary_vault = json_to_vault(self.editor.text.strip())
        except json.JSONDecodeError as e:
            self.status_label.text = f"JSON error: ..."
            return
        backup_vault = json_to_vault(self.backup_editor.text.strip()) if is_split else primary_vault
    else:
        primary_vault = self._primary_vault
        backup_vault = self._backup_vault if is_split else primary_vault

    self._update_ui_by_state(VaultState.LOADING)
    try:
        upload_vault(primary_vault, backup_vault, pw)
        self._primary_vault = primary_vault
        if is_split:
            self._backup_vault = backup_vault
        self.status_label.text = f"Saved ... - {len(primary_vault.entries)} entries"
        self._update_ui_by_state(VaultState.SPLIT if is_split else VaultState.LOADED)
    except ...
```

Сравнение primary↔backup в `upload()`:

```python
if self._state == VaultState.SPLIT:
    primary_json = vault_to_json(self._primary_vault)
    backup_json = vault_to_json(self._backup_vault)
    if primary_json != backup_json:
        self.open_sync()
        return
```

`open_add_entry()`:

```python
def open_add_entry(self):
    popup = AddEntryPopup()
    popup.on_entry_added = self._on_entry_added
    popup.open()
```

**Методы (новые):**

`_refresh_list()`:

```python
def _refresh_list(self):
    """Перестроить данные RecycleView из _primary_vault / _backup_vault."""
    data = [{"service": e.service, "index": i} for i, e in enumerate(self._primary_vault.entries)]
    self.primary_list.data = data
    if self._state == VaultState.SPLIT:
        backup_data = [{"service": e.service, "index": i} for i, e in enumerate(self._backup_vault.entries)]
        self.backup_list.data = backup_data
```

`_toggle_raw()`:

```python
def _toggle_raw(self):
    """Переключить режим список ↔ raw JSON."""
    self._raw_mode = not self._raw_mode
    self.raw_button.text = "List" if self._raw_mode else "Raw"

    if self._raw_mode:
        # Заполнить editor из Vault
        self.editor.text = vault_to_json(self._primary_vault)
        self.editor.readonly = True
        if self._state == VaultState.SPLIT:
            self.backup_editor.text = vault_to_json(self._backup_vault)
            self.backup_editor.readonly = True
        # Скрыть RecycleView, показать TextInput
        self.primary_scroll.children[0] = self.editor  # или через opacity/disabled
        ...
    else:
        # Прочитать editor.text, обновить Vault
        try:
            self._primary_vault = json_to_vault(self.editor.text.strip())
        except json.JSONDecodeError:
            self.status_label.text = "JSON error - cannot switch to list"
            self._raw_mode = True
            return
        if self._state == VaultState.SPLIT:
            try:
                self._backup_vault = json_to_vault(self.backup_editor.text.strip())
            except json.JSONDecodeError:
                ...
        self._refresh_list()
```

На самом деле проще — в `.kv` сделать два контейнера с `opacity: 0/1`:

```
BoxLayout:
    orientation: "horizontal"
    BoxLayout:  # list container
        id: list_container
        opacity: 1
        RecycleView:
            id: primary_list
            ...
    BoxLayout:  # raw container
        id: raw_container
        opacity: 0
        ScrollView:
            id: primary_scroll
            CustomTextInput:
                id: editor
                readonly: True
                ...
```

И переключать `opacity` + `disabled` у контейнеров.

В split-режиме — два набора контейнеров:

```
BoxLayout:
    orientation: "horizontal"
    BoxLayout:  # primary
        BoxLayout:  # list
            opacity: 1 if not root._raw_mode else 0
            disabled: root._raw_mode
            RecycleView: id: primary_list
        BoxLayout:  # raw
            opacity: 1 if root._raw_mode else 0
            disabled: not root._raw_mode
            ScrollView: ...
    BoxLayout:  # backup
        size_hint_x: 0 if root._state != "split" else 0.5
        ...
```

`_edit_entry(index: int)`:

```python
def _edit_entry(self, index):
    """Открыть EditEntryPopup для записи по индексу."""
    vault = self._backup_vault if (self._state == VaultState.SPLIT and ...) else self._primary_vault
    entry = vault.entries[index]

    popup = EditEntryPopup()
    popup.entry_index = index
    popup.entry = PasswordEntry(service=entry.service, login=entry.login, password=entry.password, notes=entry.notes)
    popup.on_save = self._on_entry_saved
    popup.on_delete = self._on_entry_deleted
    popup.open()

    # В split-режиме нужно знать, какой vault редактируем
    # Можно через target_vault или переключать по фокусу RecycleView
```

Для split-режима: нужно знать, из какого списка нажали. Варианты:

- `primary_list` и `backup_list` имеют разные callback'и: `_edit_primary_entry` / `_edit_backup_entry`
- Или передавать `source: str = "primary"` в callback

`_on_entry_saved(index: int, entry: PasswordEntry)`:

```python
def _on_entry_saved(self, index, entry):
    """Обновить запись в Vault после сохранения в EditEntryPopup."""
    self._primary_vault.entries[index] = entry
    if self._state == VaultState.SPLIT:
        self._backup_vault.entries[index] = entry  # или отдельный target
    self._refresh_list()
```

`_on_entry_deleted(index: int)`:

```python
def _on_entry_deleted(self, index):
    """Удалить запись из Vault."""
    del self._primary_vault.entries[index]
    if self._state == VaultState.SPLIT:
        del self._backup_vault.entries[index]
    self._refresh_list()
```

`_on_entry_added(entry: PasswordEntry)`:

```python
def _on_entry_added(self, entry):
    """Добавить запись в Vault из AddEntryPopup."""
    self._primary_vault.entries.append(entry)
    if self._state == VaultState.SPLIT:
        self._backup_vault.entries.append(entry)
    self._refresh_list()
```

`_handle_sync_choice(choice)`:

```python
def _handle_sync_choice(self, choice):
    if choice == "primary":
        self._backup_vault = Vault(entries=list(self._primary_vault.entries))
    elif choice == "backup":
        self._primary_vault = Vault(entries=list(self._backup_vault.entries))
    self._do_upload()
```

**State machine (изменения):**

`_update_ui_by_state()`:

- LOADED: `_refresh_list()`
- SPLIT: показать backup editor/list, `_refresh_list()`
- EMPTY: скрыть backup, очистить list data
- LOADING: без изменений

#### 3. `app/services/vault_ops.py` — возвращать Vault

`download_primary(password) -> tuple[Vault, int]`:

```python
def download_primary(password: str) -> tuple[Vault, int]:
    blob = download()
    vault = unpack_vault(blob, password, primary=True)
    return vault, len(vault.entries)
```

Убрать `vault_to_json()` из этой функции (VaultScreen сам вызовет при переходе в raw-режим).

`download_backup(password) -> tuple[Vault, int]`:
Аналогично.

`upload_vault(primary_vault, backup_vault, password)`:
Без изменений — уже принимает Vault.

#### 4. `app/popups/add_entry.py` — callback вместо target_editor

- Убрать `target_editor = ObjectProperty(None)`
- Убрать логику `json.loads(current_json)`, `data.setdefault(...)`, `json.dumps(..., indent=2)`
- Убрать `self.target_editor.text = json.dumps(...)`
- Добавить `on_entry_added = ObjectProperty(None)` — callback `(entry: PasswordEntry) -> None`
- `save()`:
  1. Валидация service + login не пустые
  2. Создать `PasswordEntry(service=..., login=..., password=..., notes=...)`
  3. Вызвать `self.on_entry_added(entry)`
  4. Закрыть попап

#### 5. `app/screens/unlock.py` — передавать Vault

- `vault_screen.preloaded_vault = vault` (вместо `preloaded_text = json_str`)
- `vault_screen.preloaded_vault = None` (вместо `preloaded_text = ""` для FileNotFoundError)
- Получать `vault` из `vault_ops.download_primary()` (теперь возвращает `tuple[Vault, int]`)

### Что остаётся без изменений

- Тулбар: Download, Upload, +Entry, \* (Settings)
- State machine (EMPTY/LOADED/LOADING/SPLIT) — логика та же, обновляется только UI
- SettingsPopup, SyncPopup
- Encryption/decryption (pack_vault, unpack_vault) — без изменений
- Авто-сортировка на upload — без изменений (в `upload_vault`)

### Что уходит

- Глобальный Show/Hide (заменён per-entry в попапе)
- Глобальное маскирование паролей через regex (`_mask_passwords`)
- Прямое редактирование JSON как основной режим
- `_visible_json` строки (заменены на Vault объекты)
- `_validate_editor_json()` (валидация в попапах)
- `_on_editor_text()` / `_on_backup_editor_text()` (нет прямого редактирования текста)

### Порядок реализации

1. `edit_entry.py` + `edit_entry.kv` — новый попап
2. `vault_ops.py` — возвращать Vault
3. `vault.py` — замена \_visible_json на \_vault, новый \_refresh_list, \_edit_entry, \_on_entry_saved/deleted/added
4. `vault.kv` — RecycleView + raw-контейнеры
5. `add_entry.py` — callback вместо target_editor
6. `unlock.py` — preloaded_vault

### Риски

- **RecycleView** в Kivy требует `viewclass` и правильной структуры `data`. Надо протестировать, что тапы работают внутри ScrollView + RecycleView на Android.
- **Split-режим**: нужно чётко различать, из какого списка (primary/backup) пришёл тап, чтобы редактировать правильный Vault.
- **Raw-режим**: при переключении raw → список нужно парсить JSON — возможны ошибки, надо показывать статус и не давать переключиться при битом JSON.
- **Обратная совместимость**: preloaded_text меняется на preloaded_vault — нужно проверить unlock flow.

**Сложность:** высокая — ~200 строк .py, ~100 строк .kv, затрагивает 5+ файлов.

---

## Поиск по сервисам (обновлено под список)

**Что сделать:** над списком записей — однострочное поле поиска. При вводе текста фильтруются записи в RecycleView по полю `service` (case-insensitive). При пустом поле — показываются все записи.

**Реализация:**

- `CustomTextInput` с `multiline: False` над RecycleView в `vault.kv`
- Метод `_filter_services(text: str)` в `vault.py` — фильтрует `data` списка по `service`
- Срабатывает на `on_text` поискового поля
- В split-режиме — фильтр применяется к обоим спискам

**Сложность:** низкая — ~10 строк Python + 1 TextInput в `.kv`

---

## Смена мастер-пароля

**Что сделать:**

- Отдельный попап `ChangePasswordPopup`
- Поля: `current_password`, `new_password`, `confirm_new_password`
- Логика:
  1. Проверить текущий пароль (попробовать расшифровать vault)
  2. Перешифровать оба хранилища (primary + backup) новым паролем
  3. Загрузить на Yandex Disk
  4. Обновить in-memory мастер-пароль в приложении

**Реализация:**

- Новый файл `app/popups/change_password.py` + `.kv`
- Сервисная функция в `app/services/vault_ops.py`: `change_password(old_pw, new_pw) -> None`
- Кнопка в `SettingsPopup` → открывает `ChangePasswordPopup`

**Сложность:** средняя-высокая

- Нужно корректно обработать оба хранилища (primary + backup)
- Риск потери данных при ошибке — нужна транзакционность (сначала загрузить новое, потом старое)
- Обновить `app.master_password` после успешной смены
- Обработка ошибок сети и неверного текущего пароля
