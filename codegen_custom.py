# codegen_custom.py
from playwright.sync_api import sync_playwright
import subprocess
import sys

# ---------- vos options ----------
VIEWPORT = {'width': 1920, 'height': 1080}
BROWSER_ARGS = [
    '--start-maximized',
    '--force-device-scale-factor=1',
    '--high-dpi-support=1',
    '--disable-dev-shm-usage',
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-blink-features=AutomationControlled',
]
USER_AGENT = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
              'AppleWebKit/537.36 (KHTML, like Gecko) '
              'Chrome/120.0.0.0 Safari/537.36')
# ---------------------------------

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=BROWSER_ARGS,
            ignore_default_args=['--enable-automation', '--disable-default-apps'],
        )

        context = browser.new_context(
            viewport=VIEWPORT,
            screen=VIEWPORT,
            device_scale_factor=1,
            user_agent=USER_AGENT,
            locale='fr-FR',
        )

        page = context.new_page()
        # anti-detection
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = {runtime: {}};
        """)

        # ouverture de la page voulue
        page.goto('https://votre-site-minderest.com/exports/historical')

        # on laisse codegen s’accrocher à ce navigateur
        print("Playwright codegen va se lancer… Ne fermez pas cette fenêtre.")
        print("Copiez-coller la commande suivante dans un autre terminal :")
        print(f"npx playwright codegen --target python -b chromium --channel "
              f"chrome --viewport-size {VIEWPORT['width']}x{VIEWPORT['height']}")
        print("Puis cliquez sur « Record ».")

        # garde le navigateur ouvert
        try:
            page.wait_for_event("close", timeout=0)
        except:
            pass


if __name__ == '__main__':
    main()