import os
import re
from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential, wait_fixed
import logging
from src.config.settings import settings

logger = logging.getLogger(__name__)


class MinderestScraper:
    """Scraper pour Minderest - Gère popup, zoom, et navigation complète"""
    
    def __init__(self, email: str = None, password: str = None):
        self.email = email or settings.MINDEREST_EMAIL
        self.password = password or settings.MINDEREST_PASSWORD
        self.browser = None
        self.context = None
        self.page = None
    
    def __enter__(self):
        """Context manager optimisé pour Windows (plein écran + anti-detection)"""
        logger.info("=== DEMARRAGE NAVIGATEUR PLAYWRIGHT ===")
        
        playwright = sync_playwright().start()
        
        # === CORRECTIF ZOOM/DPI WINDOWS (100% garanti) ===
        self.browser = playwright.chromium.launch(
            headless=False,                       # Changer à True pour headless (lancé programme sans affichage UI)
            slow_mo=100,
            args=[
                '--start-maximized',              # Plein écran
                '--force-device-scale-factor=1',  # Force zoom 100%
                '--high-dpi-support=1',           # Support DPI correct
                '--disable-dev-shm-usage',        # Évite erreurs mémoire
                '--no-sandbox',                   # Windows compatibility
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',  # Anti-detection
            ],
            ignore_default_args=[
                '--enable-automation',
                '--disable-default-apps',
            ]
        )
        
        # === CORRECTIF VIEWPORT : Forcer résolution exacte ===
        self.context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},  # FULL HD strict
            screen={'width': 1920, 'height': 1080},
            device_scale_factor=1,  # Désactive scaling DPI
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # === ANTI-DETECTION SUPPLÉMENTAIRE ===
        self.context.set_extra_http_headers({
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
        })
        
        self.page = self.context.new_page()
        
        # Désactiver la détection WebDriver
        self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.chrome = {
                runtime: {}
            };
        """)
        
        logger.info("Navigateur lancé en plein écran / zoom 100%")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ferme le navigateur proprement"""
        logger.info("=== FERMETURE NAVIGATEUR ===")
        if self.browser:
            self.browser.close()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def login(self):
        """Se connecter avec gestion popup et détection bouton"""
        logger.info("CONNEXION MINDEREST")
        
        # Navigation
        logger.info("  [1] Navigation page login...")
        self.page.goto(f"{settings.MINDEREST_BASE_URL}/user/login", wait_until='networkidle')
        
        # Username
        logger.info("  [2] Remplissage username...")
        self.page.fill('input[id="username"]', self.email)
        logger.info("  [3] Username rempli")
        
        # Continuer
        logger.info("  [4] Clic bouton Continuer...")
        self.page.click('button:has-text("Continuer")')
        logger.info("  [5] Continuer clique")
        
        # Mot de passe
        logger.info("  [6] Remplissage mot de passe...")
        self.page.fill('input[type="password"]', self.password)
        logger.info("  [7] Mot de passe rempli")
        
        # Sign In (avec timeout plus long et multi-sélecteurs)
        logger.info("  [8] Recherche bouton Sign In...")
        try:
            signin_btn = self.page.wait_for_selector(
                'button[type="submit"], button:has-text("Sign in"), button:has-text("Connexion")',
                timeout=5000
            )
            signin_btn.click()
            logger.info("  [9] Sign In clique")
        except:
            # Fallback : si le bouton n'est pas trouvé, essayer Enter
            logger.warning("Bouton Sign In non trouve, tentative avec Enter...")
            self.page.press('input[type="password"]', 'Enter')
        
        # Attendre dashboard
        logger.info("  [10] Attente dashboard...")
        self.page.wait_for_url(f"{settings.MINDEREST_BASE_URL}/dashboard", timeout=60000)
        logger.info(">>> CONNEXION REUSSIE <<<")
    
    @retry(stop=stop_after_attempt(2), wait=wait_fixed(5000))
    def navigate_to_exports(self):
        """Navigation avec fermeture popup Custom Exports dans iframe"""
        logger.info("NAVIGATION VERS EXPORTS")
        
        # Aller à la page
        self.page.goto(f"{settings.MINDEREST_BASE_URL}/exports/historical", wait_until='networkidle')
        
        # === GESTION DU POPUP CUSTOM EXPORTS (Iframe) ===
        logger.info("  Detection popup Custom Exports...")
        
        try:
            # Sélecteur EXACT du popup (depuis codegen)
            # On entre dans l'iframe puis on cherche le bouton Close
            close_btn = self.page.frame_locator('[data-test-id="interactive-frame"]') \
                               .get_by_role("button", name="Close")
            
            # Vérifier si le bouton existe et est visible
            if close_btn.is_visible(timeout=3000):  # Timeout court
                close_btn.click()
                logger.info("  >>> POPUP FERME via iframe <<<")
            else:
                logger.info("  Pas de popup detecte (normal)")
        
        except Exception as e:
            logger.info("  Pas de popup ou erreur : %s", str(e))
        
        # Vérifier qu'on est bien sur la bonne page
        self.page.wait_for_selector('h1:has-text("Export historique")', timeout=10000)
        logger.info("Navigation reussie")
        
    
    def fill_export_form(self):
        """Remplit le formulaire avec sélecteurs robustes + calendrier stable"""
        logger.info("="*60)
        logger.info("REMPLISSAGE FORMULAIRE EXPORT")
        logger.info("="*60)

        # 1. NOM DU FICHIER
        now = datetime.now()
        file_name = f"Exports_Minderset_{now:%d-%m-%Y_%Hh%M}s"
        logger.info("  [1] Nom : %s", file_name)

        name_field = self.page.get_by_role("textbox", name="Entrez un nom")
        name_field.wait_for(state='visible')
        name_field.fill(file_name)
        logger.info("  [2] Nom saisi")
        
        # Cliquer sur "Types d'exportation" , choisissez le type "Lignes"
        logger.info("  [2.1] Choix Type d'exportation : Lignes")
        self.page.get_by_role("button", name="Lignes").click()
        logger.info("  [2.2] Type d'exportation 'Lignes' choisi")

        # 2. LISTE DES CHAMPS (inchangé)
        logger.info("  [3] Ouverture liste champs...")
        list_opener = self.page.get_by_text("items selected")
        list_opener.wait_for(state='visible', timeout=10_000)
        list_opener.click()
        self.page.wait_for_selector(".vue-recycle-scroller__item-view", timeout=5_000)
        self.page.wait_for_timeout(500)

        field_selectors = {
            "historical_cli_min_price": "#historical_cli_min_price",
            "historical_cli_max_price": "#historical_cli_max_price",
            "historical_cli_avg_price": "#historical_cli_avg_price",
            "historical_cli_avg_stock": "#historical_cli_avg_stock",
            "cli_category_level_3": "#cli_category_level_3",
            "cli_category_level_4": "#cli_category_level_4",
            "historical_cli_offer": "#historical_cli_offer",
            "historical_cli_stock": "#historical_cli_stock",
            "historical_comp_offer": "#historical_comp_offer",
            "historical_comp_stock": "#historical_comp_stock",
            "historical_cli_price": "#historical_cli_price",
            "historical_cli_cost": "#historical_cli_cost",
            "historical_comp_avg_stock": "#historical_comp_avg_stock",
            "my_price_before_offer": 'div.filter:has-text("My Price before offer")',
            "my_stock": 'div.filter:has-text("My Stock")',
            "stock": 'div.filter:has-text("Stock")',
        }
        for field_name in settings.EXPORT_FIELDS:
            try:
                sel = field_selectors.get(field_name, f"#{field_name}")
                el  = self.page.locator(sel).first
                if not el.is_visible(timeout=1_000):
                    logger.warning("    [INVISIBLE] %s", field_name)
                    continue
                if el.is_disabled():
                    logger.info("    [GRISÉ] %s (ignoré)", field_name)
                    continue
                try:
                    if el.is_checked():
                        logger.debug("    [DÉJÀ COCHÉ] %s", field_name)
                        continue
                except Exception:
                    pass
                el.check()
                logger.info("    [✓] %s coché", field_name)
                if field_name in ["my_price_before_offer", "my_stock", "stock"]:
                    self.page.press('body', 'ArrowDown')
            except Exception as e:
                logger.warning("    [✗] %s : %s", field_name, str(e))

        self.page.keyboard.press("Escape")
        logger.info("  [7] Liste fermée")

        # === 6. SÉLECTION DES DATES (codegen exact : 11 prev + 11 next) ===
        logger.info("  [8] Sélection période (11 mois glissants exacts)")

        today      = datetime.now()
        start_date = today - timedelta(days=365)   # même jour, -1 an
        end_date   = today - timedelta(days=1)     # hier

        DAY_START  = today.day        # 25 par exemple
        DAY_END    = end_date.day     # 24

        # 1. Ouvrir le calendrier
        self.page.locator("#export-historical-calendar").click()
        self.page.wait_for_selector(".prev > span", timeout=5_000)

        # 2. REVENIR de 11 mois (prev)
        for _ in range(11):
            self.page.locator(".prev > span").click()
            self.page.wait_for_timeout(150)

        # 3. Cliquer sur le jour d’aujourd’hui (dans le passé)
        self.page.get_by_role("cell", name=str(DAY_START)).first.click()

        # 4. AVANCER de 11 mois (next)
        for _ in range(11):
            self.page.locator(".next > span").click()
            self.page.wait_for_timeout(150)

        # 5. Cliquer sur le jour d’hier
        self.page.get_by_role("cell", name=str(DAY_END)).nth(1).click()

        # 6. Appliquer
        self.page.get_by_role("button", name="Appliquer").click()
        logger.info("  [9] Dates sélectionnées (%s → %s)",
                    start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))

        return file_name
    
    def _navigate_to_month(self, target: datetime):
        """Navigue mois par mois jusqu’à afficher le mois cible."""
        month_abbr = {
            1: ("janv", "jan"), 2: ("févr", "feb"), 3: ("mars", "mar"),
            4: ("avr", "apr"),   5: ("mai", "may"), 6: ("juin", "jun"),
            7: ("juil", "jul"),  8: ("août", "aug"), 9: ("sept", "sep"),
            10: ("oct", "oct"), 11: ("nov", "nov"), 12: ("déc", "dec"),
        }
        tgt = month_abbr[target.month]

        for _ in range(24):  # 24 mois max
            # ---- mois affiché (header) ----
            # chez Minderest le titre est : <div class="calendar-title">nov. 2025</div>
            hdr = self.page.locator('.calendar-title, .datepicker-title').first
            if hdr.is_visible(timeout=1_000):
                txt = hdr.text_content().lower()
                if any(m in txt for m in tgt):
                    return  # on est arrivé

            # ---- clic sur la bonne flèche ----
            current_num = self._month_number(hdr.text_content())
            if current_num and current_num > target.month:
                self.page.locator(".prev > span").click()
            else:
                self.page.locator(".next > span").click()
            self.page.wait_for_timeout(300)

        logger.warning("Impossible d'atteindre le mois %s", tgt[0])

    @staticmethod
    def _month_number(text: str) -> int | None:
        mapping = {
            "janv": 1, "jan": 1, "févr": 2, "feb": 2, "mars": 3, "mar": 3,
            "avr": 4, "apr": 4, "mai": 5, "may": 5, "juin": 6, "jun": 6,
            "juil": 7, "jul": 7, "août": 8, "aug": 8, "sept": 9, "sep": 9,
            "oct": 10, "nov": 11, "déc": 12, "dec": 12,
        }
        for abbr, num in mapping.items():
            if abbr in text.lower():
                return num
        return None
    
    def submit_request(self):
        """Soumettre la requête d'export"""
        logger.info("SOUMISSION REQUÊTE")
        
        request_btn = self.page.locator('button:has-text("Requête"), button:has-text("Exporter")').first
        request_btn.wait_for(state='visible')
        request_btn.click()
        
        self.page.wait_for_selector('.alert-success, .toast-success', timeout=30000)
        logger.info("  ✅ Requête validée")
        
    
    def run_full_process(self):
        """Execute le processus complet"""
        logger.info("="*60)
        logger.info("DEBUT PROCESSUS COMPLET MINDEREST")
        logger.info("="*60)
        
        try:
            self.login()
            self.navigate_to_exports()
            file_name = self.fill_export_form()
            # self.submit_request()         décommenter la ligne suivante pour envoyer la requête
            
            logger.info("="*60)
            logger.info("PROCESSUS TERMINE : %s", file_name)
            logger.info("="*60)
            
            # Attendre 20 seconds avant de fermer la page pour s'assurer que tout est bien pris en compte
            logger.info("Attente 60 s avant fermeture du navigateur...")
            import time
            time.sleep(20)
            return True, file_name
        
        except Exception as e:
            logger.error("ERREUR PROCESSUS : %s", e)
            screenshot_path = f"logs/error_process_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            self.page.screenshot(path=screenshot_path)
            logger.error("Screenshot : %s", screenshot_path)
            return False, str(e)