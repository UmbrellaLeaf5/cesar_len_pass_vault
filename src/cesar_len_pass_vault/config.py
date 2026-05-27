"""
Загрузка конфигурации из .env.
"""

import os

from dotenv import load_dotenv


load_dotenv()

YA_TOKEN: str = os.getenv("YA_TOKEN", "")
REMOTE_PATH: str = "/Приложения/cesar-len-key/vault.enc"
BACKUP_REMOTE_PATH: str = "/Приложения/cesar-len-key/vault_backup.enc"
