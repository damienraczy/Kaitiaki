# kai_kite/utils/config.py
import yaml
from pathlib import Path

def get_config():
    """Charge la configuration depuis le fichier config.yaml."""
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)
