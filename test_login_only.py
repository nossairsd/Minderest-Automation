# test_login_only.py - Fichier à créer à la RACINE du projet
import sys
import os
from datetime import datetime

# Ajouter src au PYTHONPATH
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'src'))

from minderest.scraper import MinderestScraper

# Config logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

def test_login_seul():
    """Test uniquement la connexion + navigation vers exports"""
    logger = logging.getLogger(__name__)
    
    try:
        with MinderestScraper() as scraper:
            logger.info("="*60)
            logger.info("TEST : CONNEXION + NAVIGATION EXPORTS")
            logger.info("="*60)
            
            # Logins
            scraper.login()
            logger.info("✅ Connexion réussie")
            
            # Navigation avec gestion popup
            scraper.navigate_to_exports()
            logger.info("✅ Navigation exports réussie")
            
            # Garder ouvert 3 secondes pour vérifier visuellement
            scraper.page.wait_for_timeout(3000)
            
            logger.info("="*60)
            logger.info("SUCCESS - TOUT FONCTIONNE")
            logger.info("="*60)
            
    except Exception as e:
        logger.exception("ERREUR CRITIQUE")
        sys.exit(1)

if __name__ == "__main__":
    test_login_seul()