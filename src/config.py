import json
import os
from datetime import date, timedelta

CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CONFIG_PATH = os.path.join(CONFIG_DIR, "user_config.json")

YESTERDAY = (date.today() - timedelta(days=1)).isoformat()

DEFAULT_CONFIG = {
    "tickers": ["AAPL", "VWCE.MI", "BTC-USD", "^GSPC"],
    "start_date": "2010-01-01",
    "end_date": YESTERDAY,
    "risk_free_rate": 4.0,
    "initial_investment": 10000,
    "use_cache": True,
    "ui_mode": "beginner",
}


def load_config() -> dict:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            cfg = json.load(f)
        for k, v in DEFAULT_CONFIG.items():
            cfg.setdefault(k, v)
        return cfg
    return DEFAULT_CONFIG.copy()


def save_config(config: dict) -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def update_config(**kwargs) -> dict:
    cfg = load_config()
    cfg.update(kwargs)
    save_config(cfg)
    return cfg
