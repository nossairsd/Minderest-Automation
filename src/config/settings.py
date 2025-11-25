import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Configuration centralisée"""
    
    # Credentials
    MINDEREST_EMAIL: str = os.getenv("MINDEREST_EMAIL")
    MINDEREST_PASSWORD: str = os.getenv("MINDEREST_PASSWORD")
    MINDEREST_BASE_URL: str = "https://app.minderest.com/fr"
    
    EXPORT_FIELDS = [
        "historical_cli_min_price",
        "historical_cli_max_price",
        "historical_cli_avg_price",
        "historical_cli_avg_stock",
        "cli_category_level_3",
        "cli_category_level_4",
        "historical_cli_offer",
        "historical_cli_stock",
        "historical_comp_offer",
        "historical_comp_stock",
        "historical_cli_price",
        "historical_cli_cost",
        "historical_comp_avg_stock",
    ]
    
    # Période : 365 jours (1 an exact)
    PERIOD_DAYS = int(os.getenv("PERIOD_DAYS", "365"))
    
    # Chemins
    DATA_INPUT = "data/input"
    DATA_OUTPUT = "data/output"
    LOGS_DIR = "logs"
    DATA_HISTORIQUE = "data/historique"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()