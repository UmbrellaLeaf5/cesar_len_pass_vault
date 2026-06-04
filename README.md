# CesarLen PassVault

[![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python)](https://python.org)
[![Kivy](https://img.shields.io/badge/Kivy-2.3+-green?logo=kivy)](https://kivy.org)
[![python-dotenv](https://img.shields.io/badge/dotenv-1.0+-yellow)](https://github.com/theskumar/python-dotenv)
[![YandexDisk](https://img.shields.io/badge/Yandex.Disk-REST-red)](https://yandex.ru/dev/disk/)
[![GitHub release](https://img.shields.io/github/v/release/UmbrellaLeaf5/cesar_len_pass_vault?label=latest%20release)](https://github.com/UmbrellaLeaf5/cesar_len_pass_vault/releases/latest)
[![License](https://img.shields.io/badge/License-Unlicense-lightgrey)](https://unlicense.org)

<!-- [![Tests](https://github.com/UmbrellaLeaf5/cesar_len_pass_vault/workflows/Tests/badge.svg)](https://github.com/UmbrellaLeaf5/cesar_len_pass_vault/actions/workflows/tests.yml)
[![Ruff](https://github.com/UmbrellaLeaf5/cesar_len_pass_vault/workflows/Ruff/badge.svg)](https://github.com/UmbrellaLeaf5/cesar_len_pass_vault/actions/workflows/ruff.yml)
[![Pyright](https://github.com/UmbrellaLeaf5/cesar_len_pass_vault/workflows/Pyright/badge.svg)](https://github.com/UmbrellaLeaf5/cesar_len_pass_vault/actions/workflows/pyright.yml) -->

<img align="right" height="256" src="https://raw.githubusercontent.com/UmbrellaLeaf5/cesar_len_pass_vault/main/images/leaves.png"/>

A **cross-platform password vault** with a Kivy-based GUI. Stores your passwords as AES-free, custom-encrypted JSON on [Yandex.Disk](https://yandex.ru/dev/disk/). No local vault files - everything lives in the cloud and is decrypted on the fly with your master password. Available for **Windows** (`.exe`) and **Android** (`.apk`), with both builds published automatically via GitHub Actions on every tagged release. The vault is protected by two independent encryption layers so that floating-point drift across platforms never locks you out.

## Dual encryption

Every vault is stored **twice** with independent algorithms so that a drifting floating-point formula on one platform never locks you out:

| Version | Library                                                             | Cipher                                                                                                       |
| ------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Primary | [**cesar_len_key**](https://github.com/UmbrellaLeaf5/cesar_len_key) | `CryptedLines` - word-level Caesar shuffle with trig‑based key expansion                                     |
| Backup  | `cipher_wrapper.py`                                                 | Multi‑round Caesar with SHA‑256 key stretching, HMAC subkeys, and integer‑only shift computation (no floats) |

Both versions share the same master password but derive keys differently. They also use independent cryptographic salts, so the same plaintext produces completely different cipher_texts for each path.

The primary cipher (`cesar_len_key`) is fast and compact. The backup cipher is deliberately over‑engineered - multiple rounds, derived subkeys, forbidden zero‑shifts - specifically to avoid the floating‑point pitfalls that could cause the primary cipher to produce different output on different hardware.

## How it works

### First launch

Enter your Yandex.Disk OAuth token and vault path on the **Setup** screen. Settings are saved to `.env` (desktop) or encrypted `settings.json` (Android). Subsequent launches skip this step.

### Unlock & editor

Type your master password - the vault is downloaded, decrypted, and displayed as formatted JSON. By default all passwords are masked (`***`) and the editor is locked. Press **Show** to reveal and edit, **Hide** to mask again.

### Toolbar

**Download** | **Upload** | **+ Entry** | **Show**/**Hide** | **\*** | **Backup**. Buttons enable/disable based on the current state:

| State                             | Download | Upload | + Entry | Show/Hide | \*  | Backup |
| --------------------------------- | -------- | ------ | ------- | --------- | --- | ------ |
| **Empty** — nothing loaded        | +        | -      | -       | -         | +   | -      |
| **Loaded** — primary vault shown  | +        | +      | +       | +         | +   | +      |
| **Loading** — network in progress | -        | -      | -       | -         | +   | -      |
| **Split** — two editors visible   | +        | +      | +       | +         | +   | +      |

**\*** opens the settings menu. **Backup** downloads the backup vault for split‑mode comparison.

### Adding entries

**+ Entry** opens a popup (Service, Login, Password, Notes). A **Gen** button next to Password generates a 20‑char secure random password and copies it to clipboard. **+ Entry** auto‑switches to Show mode, then back to Hide after saving. On **Upload**, entries are auto‑sorted alphabetically by `service`.

### Split mode

Download the backup vault via the settings gear - two editors side‑by‑side. If they differ on Upload, a popup asks which version to keep. Both are then synced and sorted.

### Error recovery

Network failures return the editor to **Empty** - only Download remains active. Retry at any time.

### Token protection (Android)

On Android the `YA_TOKEN` is encrypted in `settings.json` using a multi‑round Caesar cipher with SHA‑256 key stretching - the same algorithm that protects the backup vault. Format: `salt:encrypted_token` (base64). Older plaintext tokens are still accepted.

## State machine

The vault screen behaves as a deterministic state machine driven by the `VaultState` enum:

```
         ┌──────────────┐
         │    EMPTY     │  only Download active
         │              │  editor: readonly, empty
         └──────┬───────┘
                │ download (primary)
                │
         ┌──────▼───────┐
  ┌──────│    LOADED    │  all buttons active
  │      │              │  editor: passwords masked by default, Show to edit
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
  │      │   LOADING    │  all buttons disabled during
  │      │              │  network operation
  │      └──────┬───────┘
  │             │ success → LOADED or SPLIT
  │             │ error → EMPTY
  └─────────────┘
```

## Quick start

```bash
git clone https://github.com/UmbrellaLeaf5/cesar_len_pass_vault
cd cesar_len_pass_vault
uv sync
uv run cesar-vault
```

On first launch, the **Setup** screen will ask for your Yandex.Disk token and remote path. The settings are saved to `.env` and reused automatically.

### How to get a Yandex.Disk OAuth token

1. Go to [Yandex OAuth](https://oauth.yandex.ru/) and create a new application.
2. Grant it the **Yandex.Disk REST API** permission (`cloud_api:disk`).
3. Copy the token and paste it into `YA_TOKEN=` in your `.env` file.

### `.env` reference

| Variable      | Default  | Description                               |
| ------------- | -------- | ----------------------------------------- |
| `YA_TOKEN`    | -        | Yandex.Disk OAuth token (**required**)    |
| `REMOTE_PATH` | -        | Primary vault path on Disk (**required**) |
| `SALT_SIZE`   | `32`     | Salt length in bytes                      |
| `ITERATIONS`  | `100000` | SHA‑256 key stretching rounds             |
| `ROUNDS`      | `3`      | Encryption rounds for backup cipher       |

`BACKUP_REMOTE_PATH` is computed automatically as `REMOTE_PATH + ".backup"`. Specify it explicitly in `.env` only if you need a custom backup location (backward compatibility is preserved).

> **Tip:** All values can be set through the **Setup** screen on first launch. Manual `.env` editing is optional.

## Building

### Windows `.exe`

```bash
uv run pyinstaller pyinstaller.spec
# Output: dist/CesarLen-PassVault/
```

The spec uses `--onedir` with the ANGLE backend. All `.kv` and image files are bundled automatically.

### Android `.apk`

```bash
pip install buildozer cython
buildozer android release
# Output: bin/*.apk
```

Requires Linux. On Android the settings are saved as `settings.json` in the app's private directory (no `.env` files).

### [Automated releases](https://github.com/UmbrellaLeaf5/cesar_len_pass_vault/releases)

All automated builds are published as official releases. Every CI run triggered by a tag produces ready-to-use artifacts:

- `build-exe.yml` - Windows `.exe` (zip archive)
- `build-apk.yml` - Android `.apk`

Visit the [releases page](https://github.com/UmbrellaLeaf5/cesar_len_pass_vault/releases) to download the latest versions.

## License

[Unlicense](LICENSE) - public domain.
