"""
Script principal pour tester Phase 1 : Minderest uniquement
Usage: python main.py --phase minderest
"""

import logging
import sys
import os
from src.minderest.scraper import MinderestScraper

# Forcer UTF-8 sur Windows
if os.name == 'nt':
    os.environ['PYTHONUTF8'] = '1'

def setup_logging():
    """Configuration du logging SANS emojis pour Windows"""
    os.makedirs("logs", exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f"logs/minderest_{datetime.now().strftime('%Y%m%d')}.log", encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ],
        force=True  # Réinitialise les handlers existants
    )
    return logging.getLogger(__name__)

def test_minderest():
    """Test complet du scraper Minderest"""
    logger = setup_logging()
    logger.info("="*60)
    logger.info("TEST PHASE 1 : MINDEREST ONLY")
    logger.info("="*60)
    
    try:
        with MinderestScraper() as scraper:
            success, result = scraper.run_full_process()
            
            if success:
                logger.info("SUCCESS : %s", result)
                print("\n[SUCCESS] Phase 1 terminee avec succes !")
                print(f"   - Le scraper s'est connecte a Minderest")
                print(f"   - La requete a ete soumise")
                print(f"   - Verifiez vos emails dans ~10 minutes")
            else:
                logger.error("ECHEC : %s", result)
                print("\n[ERROR] Phase 1 echouee. Consultez les logs.")
                sys.exit(1)
                
    except Exception as e:
        logger.exception("ERREUR CRITIQUE: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    from datetime import datetime
    test_minderest()