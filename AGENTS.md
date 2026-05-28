# AGENTS.md

## Project

A Kivy-based GUI password vault. Stores encrypted JSON on Yandex Disk
with dual encryption: primary via `cesar_len_key.CryptedLines`, backup
via a custom multi-round Caesar cipher with SHA-256 key stretching.

## Setup

```bash
uv sync                # installs dependencies and creates .venv
```

Copy `.env.example` to `.env` and fill in:

```
YA_TOKEN=<your Yandex Disk OAuth token>
REMOTE_PATH=/Приложения/cesar-len-key/vault.enc
BACKUP_REMOTE_PATH=/Приложения/cesar-len-key/vault_backup.enc
```

## Run

```bash
uv run cesar-vault
```

## Verify after changes

Run **all** checks in this order - treat errors as blockers:

```bash
ruff check .                    # lint
ruff format --check .           # formatting
pyright .                       # type-check (adjust path if necessary)
uv run pytest -v                # unit tests
```

**LSP is mandatory.** Configure `pyright-langserver` and `ruff server` in your
editor. After every change, confirm lint, format, and type-check show **0
errors**.

## Fix formatting & imports

```bash
ruff check --fix . && ruff format .
```

## Run a single test

```bash
uv run pytest tests/test_file.py::test_name -v
```

## State machine (VaultState)

```python
class VaultState(Enum):
    EMPTY   = "empty"    # no vault loaded, download enabled
    LOADED  = "loaded"   # primary vault loaded, all operations enabled
    LOADING = "loading"  # network operation in progress, all disabled
    SPLIT   = "split"    # two editors side-by-side (primary + backup)
```

Transitions:

```
EMPTY  → (download primary) → LOADED
EMPTY  → (download backup)  → SPLIT   (left editor empty)
LOADED → (download backup)  → SPLIT
SPLIT  → (download primary) → LOADED  (exit split)
SPLIT  → (upload)           → SPLIT   (saves both versions)
EMPTY  → (upload)           → LOADED
LOADED → (upload)           → LOADED
Any    → (connection error) → EMPTY
```

## Code style

### Mark convention

Use `# MARK:<label>` and a separator line to group related methods/fields
inside classes and modules. Editors with minimap/minimap support render
MARK labels as section headers.

```python
# MARK: download
# --------------------------------------------------------------------------

def download(self) -> None:
    ...


# MARK: upload
# --------------------------------------------------------------------------

def upload(self) -> None:
    ...
```

Common MARK labels: `download`, `backup`, `upload`, `popup`, `private`,
`state`, `encrypt`, `decrypt`, `converting`, `packing`.

### Popups

- Each popup is a class in `app/popups/` with a matching `.kv` file.
- Popup launcher methods live on the screen that needs them (e.g. `VaultScreen.add_entry()`).
- Use `ObjectProperty` callbacks (not ScreenManager traversal) to communicate
  results back to the caller.
- Example: `AddEntryPopup.target_editor` receives the editor to write to.

### Services

- `app/services/vault_ops.py` is the only module that imports from
  `cesar_len_pass_vault.sync` (download/upload) and `cesar_len_pass_vault`
  (pack/unpack). Screens never import these directly.
- Service functions accept primitives or model objects and raise typed
  exceptions (`YaConnectionError`, `json.JSONDecodeError`, `DecryptionError`).
- Screens call service functions and handle UI updates (state changes,
  status messages) in try/except blocks.

### Indentation & layout

- **2‑space indentation** everywhere.
- **Line length**: 90 characters.
- **2 blank lines** between top‑level definitions (functions, classes) and
  after imports (`lines-after-imports = 2`).
- **Blank line before control flow** - insert a blank line before every `if`,
  `else`, `elif`, `for`, `while`, `try`, `except`, `finally`, `with`, `raise`,
  `assert`, `return`, `continue` that sits at the same indentation level as its
  containing block. Deeply nested one‑liners may omit the blank line.

  ```python
  # Good
  result = compute()

  if result is None:
      return

  for item in items:
      process(item)
  ```

- **Endline after docstrings** - always put an extra blank line after a
  function or class docstring.

  ```python
  def my_func():
      """Docstring."""

      # code starts after a blank line
      ...
  ```

- **Hanging indentation** for long signatures and calls:

  ```python
  def func(
    self,
    arg1: str,
    arg2: int,
  ) -> ReturnType:
      ...
  ```

### Imports

- After editing imports, run `ruff check --fix` to sort them. Ruff's `I` rule
  handles ordering, grouping (stdlib → third‑party → project), and spacing.

### Type annotations

- Every function **must** have a return type annotation.
- `pyright` runs in `basic` mode.

### Exports

- In `__init__.py` files, declare the public API with `__all__`. Ruff respects
  `__all__`, so you don't need `import X as X` or `# noqa` comments.

### Naming

- Prefer specific, descriptive names. Avoid ambiguous abbreviations.
  - Example: `resolved_api_key` rather than `key` when multiple keys exist.

## Testing

- Tests that depend on Yandex Disk (`test_sync.py`) require a valid `YA_TOKEN`
  in `.env` and are auto-skipped if the token is missing or invalid.
- Use `uv run pytest tests/ -v` to run all tests.
- Use `uv run pytest tests/test_file.py::test_name -v` for a single test.

## Miscellaneous

- **Never edit `uv.lock` manually.** It is regenerated by `uv lock` or
  `uv sync` when dependencies change.
