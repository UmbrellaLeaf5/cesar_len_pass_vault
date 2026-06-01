"""
Криптографические константы, общие для всех модулей пакета.

Вынесены в отдельный файл чтобы избежать циклических импортов.
"""

import os

from dotenv import load_dotenv


# --------------------------------------------------------------------------------------

load_dotenv()

# --------------------------------------------------------------------------------------

SALT_SIZE: int = int(os.getenv("SALT_SIZE", "32"))
ITERATIONS: int = int(os.getenv("ITERATIONS", "100000"))
ROUNDS: int = int(os.getenv("ROUNDS", "3"))

MAGIC_PRIMARY: bytes = b"CESAR_PRIMARY_V1"
MAGIC_BACKUP: bytes = b"CESAR_VAULT_V001"

SETTINGS_KEY: str = "CesarLenPassVault"
