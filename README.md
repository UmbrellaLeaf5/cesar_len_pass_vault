# CesarLen PassVault

[![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python)](https://python.org)
[![Kivy](https://img.shields.io/badge/Kivy-2.3+-black?logo=kivy)](https://kivy.org)
[![python-dotenv](https://img.shields.io/badge/dotenv-1.0+-yellow)](https://github.com/theskumar/python-dotenv)
[![YandexDisk](https://img.shields.io/badge/Yandex.Disk-REST-red)](https://yandex.ru/dev/disk/)
[![License](https://img.shields.io/badge/License-Unlicense-lightgrey)](https://unlicense.org)

<!-- [![Tests](https://github.com/UmbrellaLeaf5/cesar_len_pass_vault/workflows/Tests/badge.svg)](https://github.com/UmbrellaLeaf5/cesar_len_pass_vault/actions/workflows/tests.yml)
[![Ruff](https://github.com/UmbrellaLeaf5/cesar_len_pass_vault/workflows/Ruff/badge.svg)](https://github.com/UmbrellaLeaf5/cesar_len_pass_vault/actions/workflows/ruff.yml)
[![Pyright](https://github.com/UmbrellaLeaf5/cesar_len_pass_vault/workflows/Pyright/badge.svg)](https://github.com/UmbrellaLeaf5/cesar_len_pass_vault/actions/workflows/pyright.yml) -->

A **Kivy-based GUI password vault** that stores encrypted JSON on
[Yandex.Disk](https://yandex.ru/dev/disk/). No local files - the vault
exists only as an encrypted blob in the cloud.

## Dual encryption

Every vault is stored **twice** with independent algorithms so that a drifting
floating-point formula on one platform never locks you out:

| Version | Library                                                             | Cipher                                                                                                       |
| ------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Primary | [**cesar_len_key**](https://github.com/UmbrellaLeaf5/cesar_len_key) | `CryptedLines` - word-level Caesar shuffle with trig‑based key expansion                                     |
| Backup  | `cipher_wrapper.py`                                                 | Multi‑round Caesar with SHA‑256 key stretching, HMAC subkeys, and integer‑only shift computation (no floats) |

Both versions share the same master password but derive keys differently.
They also use independent cryptographic salts, so the same plaintext produces
completely different ciphertexts for each path.

The primary cipher (`cesar_len_key`) is fast and compact. The backup cipher
is deliberately over‑engineered - multiple rounds, derived subkeys, forbidden
zero‑shifts - specifically to avoid the floating‑point pitfalls that could
cause the primary cipher to produce different output on different hardware.

## How it works - user experience

### 1. Unlock

The app opens to a dark unlock screen with a single password field. Type your
master password and press **Unlock** (or Enter).

Behind the scenes the app immediately reaches Yandex.Disk, downloads the
encrypted vault, and tries to decrypt it with the password you just entered.
If the password is correct, you land on the main editor screen with your data
already displayed - no extra clicks needed.

If the password is **wrong**, the screen background turns pale red and a
message says "Invalid master password". You can retry immediately.

### 2. Main editor

Once unlocked you see:

- A **toolbar** at the top with four buttons: **Download**, **Upload**,
  **+ Entry**, and a **settings gear** (⋆).
- A full‑screen **text editor** showing your vault as formatted JSON.
- A **status bar** at the bottom with timestamps and entry counts.

The toolbar adapts to the current state:

| State                               | Download | Upload | + Entry |
| ----------------------------------- | -------- | ------ | ------- |
| **Empty** - nothing loaded yet      | +        | -      | -       |
| **Loaded** - primary vault is shown | +        | +      | +       |
| **Loading** - network in progress   | -        | -      | -       |
| **Split** - two editors visible     | +        | +      | +       |

### 3. Adding entries

Press **+ Entry** to open a popup with four fields: **Service**, **Login**,
**Password**, and **Notes**. Fill in at least Service and Login, then press
**Save**. The entry is appended as a JSON object to the editor. Press
**Upload** to push the updated vault to the cloud.

### 4. Split mode - comparing ciphers

The vault is encrypted **twice** with different algorithms (see
[Dual encryption](#dual-encryption) below). Normally you only see the primary
version. Press the **gear icon** and choose **Download Backup** to load the
backup version alongside the primary one - two editors side by side.

This is useful when the primary cipher fails to decode correctly (e.g. due to
floating‑point quirks on a different CPU). You can inspect both versions and
pick the one you trust.

In split mode **+ Entry** adds to the right (backup) editor. On **Upload** the
app checks whether the two editors differ. If they do, a popup asks which
version to keep - then **both** cloud files are synchronised with the same
chosen content.

### 5. Error recovery

If a network call fails, the editor drops back to the **Empty** state: a blank
JSON editor with only the **Download** button active. You can retry at any
time.

## State machine

The vault screen behaves as a deterministic state machine driven by the
`VaultState` enum:

```
         ┌──────────────┐
         │    EMPTY     │  download / upload disabled except Download
         │              │  editor: readonly, empty
         └──────┬───────┘
                │ download (primary)
                │
         ┌──────▼───────┐
  ┌──────│    LOADED    │  all operations enabled
  │      │              │  editor: editable, primary vault shown
  │      └──────┬───────┘
  │             │ download (backup)
  │             │
  │      ┌──────▼───────┐
  │      │    SPLIT     │  two editors side by side
  │      │              │  primary (left) + backup (right)
  │      └──────┬───────┘
  │             │ download (primary) - exits split
  │             │ upload - saves both, stays in split
  │             │ add entry - appends to backup editor
  │             │
  │      ┌──────▼───────┐
  │      │   LOADING    │  all buttons disabled while network
  │      │              │  operation is in progress
  │      └──────┬───────┘
  │             │ success → LOADED or SPLIT
  │             │ error → EMPTY
  └─────────────┘
```

Every transition goes through a single method (`_update_ui_by_state`) that
updates toolbar availability, editor read‑only flag, and split‑editor
visibility in one atomic step.

## Quick start

```bash
git clone https://github.com/UmbrellaLeaf5/cesar_len_pass_vault
cd cesar_len_pass_vault
uv sync
cp .env.example .env  # then edit .env - add your Yandex.Disk OAuth token
uv run cesar-vault
```

### How to get a Yandex.Disk OAuth token

1. Go to [Yandex OAuth](https://oauth.yandex.ru/) and create a new application.
2. Grant it the **Yandex.Disk REST API** permission (`cloud_api:disk`).
3. Copy the token and paste it into `YA_TOKEN=` in your `.env` file.

### `.env` reference

| Variable             | Default                                      | Description                            |
| -------------------- | -------------------------------------------- | -------------------------------------- |
| `YA_TOKEN`           | -                                            | Yandex.Disk OAuth token (**required**) |
| `REMOTE_PATH`        | `/Приложения/cesar-len-key/vault.enc`        | Primary vault path on Disk             |
| `BACKUP_REMOTE_PATH` | `/Приложения/cesar-len-key/vault_backup.enc` | Backup vault path on Disk              |
| `SALT_SIZE`          | `32`                                         | Salt length in bytes                   |
| `ITERATIONS`         | `100000`                                     | SHA‑256 key stretching rounds          |
| `ROUNDS`             | `3`                                          | Encryption rounds for backup cipher    |

## License

[Unlicense](LICENSE) - public domain.
