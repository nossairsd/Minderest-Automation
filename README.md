# Minderest-Automation
## Phase 1 – Export historique 365 jours
```bash
pip install -r requirements.txt
playwright install chromium
cp .env.example .env      # remplir vos identifiants
python main.py --phase minderest
# headless :
HEADLESS=true python main.py --phase minderest