import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

CFG = yaml.safe_load((Path(__file__).resolve().parents[1] / "config" / "app.yaml").read_text(encoding="utf-8"))

class Settings:
    def __init__(self):
        env_path = Path('~/env/.env').expanduser()
        load_dotenv(dotenv_path=env_path, override=True)

        print(f'Loading from : {CFG["llm"]["api_key"]}')
        self.llm_api_key = os.getenv(CFG["llm"]["api_key"], "")
        print(f"Environment : {self.llm_api_key}")

settings = Settings()
