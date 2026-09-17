"""Enregistre un parcours réel d'Auto Stock Management (Playwright, mode clair).

Toutes les données sont fictives. Les légendes et le curseur sont superposés
à la page pendant l'enregistrement ; les actions sont de vraies interactions.
"""
import os, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

# Usage : DEMO_OWNER_PASSWORD='...' python3 record_demo.py [--debug]
# Prérequis : seed_demo.py (+ backdate.sql) exécutés, interface servie sur APP_URL.
HERE = Path(__file__).resolve().parent
APP = os.environ.get('APP_URL', 'http://localhost:4200')
PASSWORD = os.environ['DEMO_OWNER_PASSWORD']
W, H = 1600, 900
DEBUG = '--debug' in sys.argv
OUT = str(HERE / 'out')
SHOTS = str(HERE / 'out' / 'steps')
os.makedirs(OUT, exist_ok=True); os.makedirs(SHOTS, exist_ok=True)
TOTAL = 12
T0 = 0.0

OVERLAY = r"""
(() => {
  if (window.__demoOverlay) return; window.__demoOverlay = true;
  const css = `
  #demo-cursor{position:fixed;left:0;top:0;width:22px;height:22px;z-index:2147483647;pointer-events:none;
    transform:translate(-100px,-100px);transition:transform .06s linear}
  #demo-cursor svg{filter:drop-shadow(0 1px 2px rgba(0,0,0,.35))}
  .demo-ripple{position:fixed;width:34px;height:34px;margin:-17px 0 0 -17px;border-radius:50%;
    border:3px solid #d9480f;z-index:2147483646;pointer-events:none;animation:demoRipple .55s ease-out forwards}
  @keyframes demoRipple{from{transform:scale(.3);opacity:1}to{transform:scale(1.6);opacity:0}}
  #demo-caption{position:fixed;left:28px;bottom:26px;max-width:620px;z-index:2147483645;pointer-events:none;
    background:#ffffff;color:#14213a;border:1px solid #d5dbe3;border-left:5px solid #d9480f;border-radius:8px;
    padding:14px 20px 15px;box-shadow:0 10px 30px rgba(20,33,58,.18);font:500 17px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif;
    opacity:0;transform:translateY(10px);transition:opacity .35s ease,transform .35s ease}
  #demo-caption.on{opacity:1;transform:none}
  #demo-caption b{display:block;font-size:12px;letter-spacing:.12em;color:#d9480f;margin-bottom:4px;font-weight:700}
  `;
  const install = () => {
    if (document.getElementById('demo-cursor')) return;
    const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
    const c = document.createElement('div'); c.id = 'demo-cursor';
    c.innerHTML = '<svg width="22" height="22" viewBox="0 0 22 22"><path d="M2 1l16 9-7 1.6L7.5 19z" fill="#14213a" stroke="#fff" stroke-width="1.5" stroke-linejoin="round"/></svg>';
    document.body.appendChild(c);
    const cap = document.createElement('div'); cap.id = 'demo-caption'; document.body.appendChild(cap);
    const pos = JSON.parse(sessionStorage.getItem('demoCursor') || '[800,450]');
    c.style.transform = `translate(${pos[0]}px,${pos[1]}px)`;
    const saved = sessionStorage.getItem('demoCaption');
    if (saved) { cap.innerHTML = saved; cap.classList.add('on'); }
  };
  document.addEventListener('mousemove', e => {
    const c = document.getElementById('demo-cursor'); if (!c) return;
    c.style.transform = `translate(${e.clientX}px,${e.clientY}px)`;
    sessionStorage.setItem('demoCursor', JSON.stringify([e.clientX, e.clientY]));
  }, true);
  document.addEventListener('mousedown', e => {
    const r = document.createElement('div'); r.className = 'demo-ripple';
    r.style.left = e.clientX + 'px'; r.style.top = e.clientY + 'px';
    document.body.appendChild(r); setTimeout(() => r.remove(), 600);
  }, true);
  window.__demoCaption = (html) => {
    const cap = document.getElementById('demo-caption'); if (!cap) return;
    cap.classList.remove('on');
    setTimeout(() => { cap.innerHTML = html; sessionStorage.setItem('demoCaption', html); if (html) cap.classList.add('on'); }, 250);
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install); else install();
})();
"""


class Demo:
    def __init__(self, page):
        self.p = page
        self.x, self.y = 800, 450
        self.n = 0

    def pause(self, s):
        self.p.wait_for_timeout(int(s * (0.15 if DEBUG else 1) * 1000))

    def caption(self, step, text, hold=0.6):
        if not DEBUG:
            with open(f'{OUT}/chapters.txt', 'a') as fh:
                fh.write(f'{time.monotonic() - T0:.1f}\t{step}\t{text}\n')
        label = f'{step:02d} / {TOTAL}' if step else 'AUTO STOCK MANAGEMENT'
        self.p.evaluate('h => window.__demoCaption && window.__demoCaption(h)', f'<b>{label}</b>{text}')
        self.pause(hold)

    def shot(self, name):
        self.n += 1
        if DEBUG:
            self.p.screenshot(path=f'{SHOTS}/{self.n:02d}-{name}.png')

    def move_to(self, loc, dx=0.5, dy=0.5):
        loc.scroll_into_view_if_needed()
        box = loc.bounding_box()
        tx, ty = box['x'] + box['width'] * dx, box['y'] + box['height'] * dy
        steps = max(8, int(((tx - self.x) ** 2 + (ty - self.y) ** 2) ** 0.5 / 18))
        self.p.mouse.move(tx, ty, steps=1 if DEBUG else steps)
        self.x, self.y = tx, ty

    def click(self, loc, pause=0.5, **kw):
        loc = loc.first
        loc.wait_for(state='visible')
        self.move_to(loc, **kw)
        # Attendre qu'une notification ne recouvre plus la cible.
        for _ in range(40):
            covered = loc.evaluate('''(el, pt) => { const t = document.elementFromPoint(pt[0], pt[1]);
                return !!t && !(el === t || el.contains(t) || t.contains(el)); }''', [self.x, self.y])
            if not covered: break
            self.p.wait_for_timeout(250)
        self.pause(0.25)
        self.p.mouse.down(); self.p.mouse.up()
        self.pause(pause)

    def type(self, loc, text, delay=70, clear=True):
        self.click(loc, pause=0.2)
        if clear:
            loc.first.fill('')
        loc.first.press_sequentially(text, delay=5 if DEBUG else delay)
        self.pause(0.3)

    def scroll(self, dy, steps=12):
        for _ in range(steps):
            self.p.mouse.wheel(0, dy / steps)
            self.p.wait_for_timeout(35)
        self.pause(0.4)

    def dismiss_toasts(self):
        btns = self.p.locator('app-toast-container button:visible')
        for _ in range(btns.count()):
            b = btns.first
            if not b.is_visible(): break
            self.move_to(b); self.p.mouse.down(); self.p.mouse.up(); self.pause(0.35)

    def nav(self, label):
        self.dismiss_toasts()
        self.click(self.p.locator('nav.app-nav a', has_text=label), pause=1.0)
        self.p.wait_for_load_state('networkidle')


def run():
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(
            viewport={'width': W, 'height': H}, color_scheme='light', locale='fr-FR',
            timezone_id='Europe/Paris',
            record_video_dir=None if DEBUG else OUT, record_video_size={'width': W, 'height': H})
        ctx.add_init_script("try{localStorage.setItem('auto-stock-theme','light')}catch(e){}")
        ctx.add_init_script(OVERLAY)
        page = ctx.new_page()
        global T0; T0 = time.monotonic()
        d = Demo(page)
        p = page
        try:
            _steps(p, d)
        except Exception:
            p.screenshot(path=f'{SHOTS}/zz-failure.png'); raise
        video = page.video
        ctx.close(); browser.close()
        if video:
            print('VIDEO', video.path())


def _steps(p, d):
    if True:

        # 0. Connexion
        p.goto(f'{APP}/login'); p.wait_for_load_state('networkidle')
        d.caption(0, 'Application de gestion de stock développée pour un magasin de pièces détachées.<br>Démonstration locale, données fictives.', hold=3.2)
        d.caption(1, 'Connexion avec un compte propriétaire. Les jetons JWT sont stockés dans des cookies HttpOnly.', hold=1.2)
        d.type(p.locator('[formcontrolname=email]'), 'owner@example.test', delay=45)
        d.type(p.locator('[formcontrolname=password]'), PASSWORD, delay=45)
        d.click(p.locator('button[type=submit]'), pause=1.5)
        p.wait_for_url('**/dashboard'); p.wait_for_load_state('networkidle')
        d.shot('dashboard')

        # 1. Tableau de bord
        d.caption(2, 'Tableau de bord : ventes, créances ouvertes, produits sous le seuil et activité récente.', hold=3.2)
        d.scroll(420); d.pause(2.2); d.scroll(-420); d.pause(0.6)

        # 2. Recherche globale
        d.caption(3, 'Recherche tolérante aux fautes (PostgreSQL pg_trgm) : « amortiseur » trouve « Amortisseur ».', hold=1.0)
        search = p.locator('app-product-search input')
        d.type(search, 'amortiseur', delay=110)
        opt = p.locator('app-product-search [role=option]').first
        opt.wait_for(state='visible'); d.pause(1.8)
        d.shot('search')
        d.click(opt, pause=1.2)
        p.wait_for_load_state('networkidle')
        d.caption(3, 'Fiche produit : stock réparti entre la surface de vente et la réserve.', hold=3.2)
        d.shot('product-detail')

        # 3. Catalogue + pagination
        d.nav('Catalogue')
        d.caption(4, 'Catalogue paginé côté serveur (20 produits par page), avec état du stock par référence.', hold=2.0)
        d.scroll(900, steps=20); d.pause(0.8)
        d.click(p.get_by_role('button', name='Suivant'), pause=1.6)
        p.wait_for_load_state('networkidle')
        d.scroll(-900, steps=12); d.pause(1.4)
        d.shot('catalogue-page2')

        # 4. Réception manuelle
        d.nav('Réception')
        d.caption(5, 'Réception manuelle : création d’un nouveau produit et répartition des quantités.', hold=1.2)
        d.type(p.locator('[formcontrolname=reference]').or_(p.get_by_label('Référence produit')), 'REF-PEA-1530', delay=60)
        d.type(p.get_by_label('Nom du produit'), 'Pompe à eau Hilux', delay=55)
        d.click(p.get_by_label('Catégorie'), pause=0.3)
        p.get_by_label('Catégorie').select_option(label='Refroidissement'); d.pause(0.5)
        d.type(p.get_by_label('Prix unitaire'), '32000', delay=80)
        d.type(p.get_by_label('Seuil minimum'), '2', delay=80)
        d.type(p.get_by_label('Surface de vente'), '2', delay=80)
        d.type(p.get_by_label('Réserve'), '3', delay=80)
        d.shot('manual-filled')
        d.click(p.get_by_role('button', name='Enregistrer la réception'), pause=2.4)
        d.shot('manual-saved')

        # 5. Import CSV
        p.goto(f'{APP}/stock-receipts/new'); p.wait_for_load_state('networkidle')
        d.caption(6, 'Import CSV : analyse du fichier, aperçu ligne par ligne, puis confirmation.', hold=1.0)
        d.click(p.get_by_text('Importer un fichier CSV'), pause=0.8)
        p.locator('#stockImportFile').set_input_files(str(HERE / 'arrivage-septembre.csv'))
        d.pause(1.2)
        d.click(p.get_by_role('button', name='Analyser le fichier'), pause=1.8)
        p.wait_for_load_state('networkidle')
        d.shot('csv-preview')
        d.caption(6, 'Aperçu : chaque ligne est validée avant import (catégorie, prix, quantités).', hold=2.6)
        d.click(p.get_by_role('button', name='Confirmer l’import'), pause=1.2)
        d.click(p.get_by_role('dialog').get_by_role('button', name='Importer maintenant'), pause=2.0)
        p.wait_for_load_state('networkidle')
        d.caption(6, 'Rapport d’import : produits créés et quantités reçues, sans doublon en cas de nouvel envoi.', hold=2.8)
        d.shot('csv-report')

        # 6. Vente à crédit
        d.nav('Ventes')
        d.caption(7, 'Nouvelle vente : panier de plusieurs articles, recherche au clavier.', hold=1.0)
        picker = p.locator('app-new-sale-page app-product-picker input, main app-product-picker input').first
        d.type(picker, 'filtre air', delay=90)
        p.locator('main [role=option]').first.wait_for(); d.pause(0.7)
        d.click(p.locator('main [role=option]').first, pause=0.4)
        d.type(p.get_by_label('Quantité'), '2', delay=80)
        d.click(p.get_by_role('button', name='Ajouter'), pause=0.8)
        d.type(picker, 'bougie', delay=90)
        p.locator('main [role=option]').first.wait_for(); d.pause(0.5)
        d.click(p.locator('main [role=option]').first, pause=0.4)
        d.type(p.get_by_label('Quantité'), '4', delay=80)
        d.click(p.get_by_role('button', name='Ajouter'), pause=1.0)
        d.shot('cart')
        d.caption(7, 'Paiement partiel : la vente est rattachée à un client et le reste dû devient une créance.', hold=1.0)
        d.click(p.get_by_role('radio', name='Crédit'), pause=0.8)
        d.click(p.locator('#sale-customer'), pause=0.8)
        p.locator('#sale-customer').press_sequentially('Mahamat', delay=5 if DEBUG else 90)
        p.wait_for_timeout(1200); p.wait_for_load_state('networkidle')
        p.locator('app-customer-picker [role=option]', has_text='Mahamat').first.wait_for(); d.pause(0.6)
        d.click(p.locator('app-customer-picker [role=option]').first, pause=0.8)
        amount = p.locator('app-payment-panel input[inputmode=decimal]')
        d.type(amount, '10000', delay=90)
        d.pause(1.2)
        d.shot('credit-sale')
        d.click(p.get_by_role('button', name='Enregistrer la vente'), pause=2.4)
        d.shot('sale-saved')

        # 7. Historique des ventes
        d.nav('Historique des ventes')
        d.caption(8, 'Historique des ventes : montant, vendeur et reste dû, avec pagination.', hold=3.0)
        d.shot('sales-history')

        # 8. Transfert
        d.nav('Transferts')
        d.caption(9, 'Transfert entre la réserve et la surface : le stock global ne change pas.', hold=1.0)
        d.type(p.locator('main app-product-picker input').first, 'plaquettes avant', delay=80)
        p.locator('main [role=option]').first.wait_for(); d.pause(0.6)
        d.click(p.locator('main [role=option]').first, pause=0.8)
        d.click(p.get_by_label('Emplacement source'), pause=0.2)
        p.get_by_label('Emplacement source').select_option(label='Réserve de démonstration'); d.pause(0.5)
        d.click(p.get_by_label('Emplacement destination'), pause=0.2)
        p.get_by_label('Emplacement destination').select_option(label='Surface de démonstration'); d.pause(0.5)
        d.type(p.get_by_label('Quantité à transférer'), '4', delay=80)
        d.shot('transfer')
        d.click(p.get_by_role('button', name='Enregistrer le transfert'), pause=2.2)

        # 9. Mouvements
        d.nav('Historique des mouvements')
        d.caption(10, 'Historique des mouvements : réceptions, ventes et transferts, regroupés par opération.', hold=3.4)
        d.shot('movements')

        # 10. Créances
        d.nav('Créances')
        d.caption(11, 'Créances : ancienneté, retards et solde restant par client.', hold=2.0)
        d.click(p.get_by_text('Achta Brahim').first, pause=1.6)
        p.wait_for_load_state('networkidle')
        d.shot('debt-detail')
        d.caption(11, 'Encaissement d’un remboursement partiel : le solde est recalculé et l’historique conservé.', hold=1.0)
        d.click(p.get_by_role('button', name='Encaisser'), pause=0.8)
        dlg = p.get_by_role('dialog')
        d.type(dlg.locator('input').first, '15000', delay=90)
        d.pause(0.8)
        d.shot('payment-dialog')
        d.click(dlg.get_by_role('button').last, pause=2.4)
        d.shot('payment-done')
        d.scroll(300); d.pause(1.6); d.scroll(-300)

        # 11. Administration
        d.nav('Utilisateurs')
        d.caption(12, 'Administration : le propriétaire gère les vendeurs, leurs accès et les familles de pièces.', hold=1.2)
        d.click(p.get_by_role('button', name='Ajouter un vendeur'), pause=0.8)
        d.type(p.locator('#seller-display-name'), 'Zara Caissière', delay=60)
        d.type(p.locator('#seller-email'), 'zara@example.test', delay=50)
        d.shot('user-dialog')
        d.click(p.get_by_role('button', name='Ajouter le vendeur'), pause=2.0)
        d.shot('user-created')
        d.caption(12, 'Le mot de passe temporaire n’est affiché qu’une fois ; le vendeur devra le changer à sa première connexion.', hold=3.0)
        d.click(p.get_by_role('button', name='J’ai transmis le mot de passe'), pause=1.0)
        d.caption(12, 'Familles de pièces : création, renommage et suppression contrôlée.', hold=0.4)
        d.nav('Familles')
        d.type(p.locator('#category-name'), 'Carrosserie', delay=80)
        d.click(p.get_by_role('button', name='Créer la famille'), pause=2.0)
        d.shot('categories')

        # Fin : tableau de bord mis à jour
        d.nav('Tableau de bord')
        d.caption(0, 'Tableau de bord actualisé après les opérations.<br>Java 17 · Spring Boot 3.5 · Angular 20 · PostgreSQL', hold=4.5)
        d.shot('end')



if __name__ == '__main__':
    run()

