# AGENTS.md

## Table of Contents

- [Project & Profile](#project--profile)
- [Operational Rules & Critical Restrictions](#operational-rules--critical-restrictions)
- [Workflow & Verification Commands](#workflow--verification-commands)
- [Software Architecture & Design Patterns](#software-architecture--design-patterns)
- [Testing Strategy](#testing-strategy)
- [Environment & Configuration](#environment--configuration)

## Project & Profile

`cesar-len-pass-vault` is a cross-platform Kivy password vault for Windows and Android. It stores encrypted vault data on Yandex Disk and has two independent encrypted representations:

- **Primary cipher:** `cesar_len_key.CryptedLines`.
- **Backup cipher:** custom multi-round Caesar cipher with SHA-256 key stretching and integer-only shift calculation.

The backup cipher exists to ensure cross-platform floating-point differences in the primary cipher cannot lock a user out. Both representations must remain supported and synchronized.

### Code style

You MUST strictly follow the project's coding standards, naming conventions, and language-specific rules.

Before generating, refactoring, or modifying any code, you are REQUIRED to read and apply the guidelines defined in the external style guide:

- **File Path:** [`./CODE-STYLE.md`](./CODE-STYLE.md)

_Instruction for Agent:_ If you haven't read `./CODE-STYLE.md` in the current session, use your file-reading tool to fetch its content before writing any code. Do not hallucinate styles.

### Project layout

```text
src/cesar_len_pass_vault/  # vault domain, crypto, storage, Yandex Disk sync
app/                       # Kivy screens, popups, widgets, KV presentation files
tests/                     # unit and Yandex Disk integration tests
main.py                    # desktop application entry point
```

- `src/cesar_len_pass_vault/` contains domain models, serialization, encryption, configuration, and remote synchronization.
- `app/` is the presentation layer. It must coordinate UI state and delegate vault operations to `app/services/vault_ops.py`.
- `app/services/vault_ops.py` is the only presentation-layer module allowed to import `cesar_len_pass_vault.sync` or root-level vault pack/unpack APIs.
- Each popup in `app/popups/` has a matching `.kv` file. Each screen in `app/screens/` has a matching `.kv` file where applicable.
- Do not create a `model.py` dumping ground. Keep domain types in purpose-specific modules such as `models.py`, `enums.py`, and `exceptions.py`.

## Operational Rules & Critical Restrictions

**UNDER NO CIRCUMSTANCES may you commit, push, amend, rebase, or modify the git history without an EXPLICIT instruction to do so.** This is the most important rule in this document. Violating it may result in lost work and broken branches.

This specifically includes:

- `git commit` / `git commit --amend` / `git commit -m "..."`
- `git push` / `git push --force` / `git push --force-with-lease`
- `git add` (stage for commit — prefer working-tree-only edits)
- `git rebase` / `git reset` / `git checkout` (to modify branches)
- Any other command that creates or alters commits

**NEVER commit while Git is in detached `HEAD` state.** Before any commit, verify that the repository is on the intended working branch (for example with `git branch --show-current` or `git status`). If the current branch is empty, ambiguous, or not clearly the user's active working branch, stop and ask the user which branch to use before committing.

If the user asks "what should the commit message be?" — **suggest a message but do NOT commit**. Wait for an explicit directive such as:

- "commit"
- "commit and push"
- "закоммить"
- "сделай коммит"

**If the user says "обнови AGENTS.md" or similar — this is NOT a commit instruction. Do NOT add or commit files unless told to.**

### Security restrictions

- Never log, print, display in errors, or include in test snapshots: `YA_TOKEN`, master passwords, decrypted vault JSON, encryption salts, or derived keys.
- Never write an unencrypted vault to local storage, temporary files, build artifacts, or application logs.
- Never change the primary/backup cipher protocol, salts, key derivation, or serialization compatibility without tests proving existing vaults remain decryptable.
- Do not silently choose one representation when primary and backup vaults differ. Preserve the explicit user choice flow.
- Remote tests must use a dedicated test remote path. They must never read, overwrite, or delete the user's configured production vault.

## Workflow & Verification Commands

### Time limit (HARD REQUIREMENT)

**Every non-interactive bash command MUST complete within 60 seconds.** All non-interactive commands must be invoked through the timeout wrapper with captured output:

```bash
time-d -c "<your command>"
```

Use `time-d -c` by default for every non-interactive command. Use plain `time-d` without `-c` only for genuinely interactive commands that require a TTY, such as `vim`, `python -i`, REPLs, or terminal UI tools.

For commands that are expected to legitimately take longer than 60 seconds (full builds, full test suites, dependency syncs, large format/lint runs), use an explicit timeout:

```bash
time-d -c --sec <seconds> "<your command>"
```

Choose the smallest reasonable timeout for the command. Do not use a longer timeout to hide a hung process.

Long-running daemons must use `nohup ... >/dev/null 2>&1 &` so the wrapper returns immediately.

`time-d` is part of the `timeout-dead` package. Install once:

```bash
uv tool install timeout-dead   # or: pip install timeout-dead
time-d --version               # verify installation
```

### Setup

```bash
time-d -c --sec 300 "uv sync"
```

### Run the desktop application

```bash
time-d -c --sec 300 "uv run cesar-vault"
```

### Verify after changes

Run **all** checks in this order — treat errors as blockers:

```bash
time-d -c "uv run ruff check ."
time-d -c "uv run ruff format --check ."
time-d -c "uv run pyright ."
time-d -c --sec 300 "uv run pytest tests/ -v"
```

### Fix formatting & imports

```bash
time-d -c "uv run ruff check --fix . && uv run ruff format ."
```

**LSP is mandatory.** Configure `pyright-langserver` and `ruff server` in your editor. After every change, confirm lint, format, and type-check show **0 errors**. `ruff format` is the single source of truth for formatting — no `black`, no `isort`.

### Run a single test

```bash
time-d -c "uv run pytest tests/test_file.py::test_name -v"
```

### Build release artifacts

Build a Windows executable:

```bash
time-d -c --sec 300 "uv run pyinstaller pyinstaller.spec"
```

Build an Android APK only from a supported Linux environment. Follow `README.md` and `buildozer.spec`; do not modify build/release workflows unless explicitly requested.

### Mandatory testing

**Every change must be verified by running the relevant test suite.** No exceptions. If any test fails, fix the issue before considering the change complete.

## Software Architecture & Design Patterns

### Documentation

- **Standalone Markdown documentation pages** → `SCREAMING_SNAKE_CASE` names (e.g., `CONFIG.md`, `ARCHITECTURE.md`, `CODE-STYLE.md`). Keep conventional repository files such as `README.md` unchanged unless explicitly requested.

### Separation of concerns

- Domain logic in `src/cesar_len_pass_vault/` must not depend on Kivy screens, widgets, popups, or `.kv` files.
- Kivy screens own presentation state, button availability, and user-visible status/error messages. They must not perform encryption, remote synchronization, or direct vault packing/unpacking.
- `app/services/vault_ops.py` is the adapter between the UI and domain/remote APIs. It accepts primitives or model objects and raises typed domain exceptions.
- Screens call service functions, handle typed exceptions, and update UI state in `try`/`except` blocks.
- Use `ObjectProperty` callbacks to return popup results to the caller. Do not traverse `ScreenManager` from a popup to mutate a screen directly.

### Kivy UI boundaries

- Popup launcher methods belong to the screen that needs them, for example a vault screen opens an add-entry popup.
- A popup class belongs in `app/popups/` with a matching KV file. Screens follow the same Python/KV pairing rule.
- Keep Kivy callbacks thin. Parse user input, call a service/domain operation, then render the result or an explicit error state.
- The vault screen state machine (`EMPTY`, `LOADING`, `LOADED`, `SPLIT`) is authoritative. Do not bypass it by enabling widgets or mutating the editor directly.

### Vault and encryption invariants

- A vault has primary and backup encrypted representations. Uploading or synchronizing must preserve both representations.
- The backup remote path is derived from the primary remote path unless explicitly configured for backward compatibility.
- Primary and backup vaults must be compared before a split-mode upload. When they differ, request an explicit synchronization choice rather than discarding either version.
- The Android token-storage format and legacy plaintext-token compatibility are part of the persisted-data contract. Do not break them without a migration and regression tests.
- Sort entries by `service` before writing a vault when the existing upload contract requires it.

### Exceptions

- Define and use a custom exception hierarchy rooted in `BaseError` or the existing project equivalent.
- Use typed exceptions for domain and integration failures, including `YaConnectionError`, `DecryptionError`, and `json.JSONDecodeError` where appropriate.
- UI code catches typed exceptions and converts them to safe user-facing messages. Never expose tracebacks, tokens, passwords, or decrypted vault data.
- CLI and application entry points catch unexpected exceptions, log only safe context, and return a non-zero exit code where applicable.

```python
class BaseError(Exception):
  """Базовая ошибка приложения."""

# --------------------------------------------------

class NotFoundError(BaseError):
  """Ресурс не найден."""

# --------------------------------------------------

class ConflictError(BaseError):
  """Конфликт состояния ресурса."""
```

### Dependency management

- Use **`uv`** for dependency management.
- **Never edit `uv.lock` manually.** It is regenerated by `uv lock` or `uv sync` when dependencies change.
- Dependencies are declared in `pyproject.toml`.
- Build configuration for PyInstaller and Buildozer is part of the release contract. Preserve bundled KV/image resources and platform-specific Kivy settings.

## Testing Strategy

- Use `pytest` as the test framework. See [`./CODE-STYLE.md`](./CODE-STYLE.md) for style rules (fixtures, parametrize, mocking, skipping, naming).

### Unit tests

- Tests live in `tests/`, mirroring the source structure where practical.
- Test files are named `test_<module>.py`.
- Test pure domain behavior without Kivy or network dependencies whenever possible: models, serialization, primary/backup cipher round trips, masking, and vault comparison.

```bash
time-d -c --sec 300 "uv run pytest tests/ -v --ignore=tests/test_sync.py"
```

### Yandex Disk integration tests

- `tests/test_sync.py` requires a valid `YA_TOKEN` in `.env` and is skipped when no token is configured.
- The suite must patch the remote path to its dedicated test vault before every remote operation and clean it up before and after each test.
- Do not weaken the production-vault isolation for convenience.

```bash
time-d -c --sec 300 "uv run pytest tests/test_sync.py -v"
```

### Coverage

- Aim for high coverage of crypto, serialization, and state-transition logic. Use `pytest-cov` when installed:

```bash
time-d -c --sec 300 "uv run pytest tests/ --cov=src/cesar_len_pass_vault --cov-report=term-missing"
```

## Environment & Configuration

- Load settings from `.env` into typed configuration. Do not hardcode environment-specific values in source code.
- `.env.example` is a **committed template** — never use it directly at runtime. `.env` is the actual local runtime file and is git-ignored.
- `YA_TOKEN` and `REMOTE_PATH` are required deployment/runtime values. Missing values must produce an explicit configuration error, not a silent fallback.
- `SALT_SIZE`, `ITERATIONS`, and `ROUNDS` are security-sensitive compatibility values. Do not change defaults or introduce new fallbacks without a documented migration and compatibility tests.
- `BACKUP_REMOTE_PATH` is derived from `REMOTE_PATH` unless explicitly set for backward compatibility.
- Absolute paths are forbidden in code under all circumstances. Never hardcode machine-specific paths such as `/home/user/project`, `C:\\Users\\user\\project`, or `/tmp/data.csv` in source code, tests, generated configs, or examples intended to be copied into code. Build paths from relative paths, `Path.cwd()`, environment variables, CLI arguments, or configuration values instead. Absolute paths are allowed only in console commands or shell snippets that a user runs manually.
