# Auto Stock Management — page de présentation

Site statique qui présente le projet Auto Stock Management (Java / Spring Boot / Angular / PostgreSQL) : vidéo de démonstration, captures, architecture, tests et statut. Aucune dépendance, aucun build : HTML, CSS et JavaScript.

## Contenu

```text
docs/                    site publié (dossier source de GitHub Pages)
├── index.html
├── style.css, app.js
├── config.js            liens GitHub / LinkedIn / e-mail, visibilité des dépôts
├── images/              captures en mode clair (données fictives)
├── video/               démo MP4 (H.264) + WebM (VP9) + affiche
├── CNAME                domaine personnalisé
├── .nojekyll
└── 404.html
scripts/demo/            reproduire les données et la vidéo
├── locations.sql        magasin et emplacements fictifs (base vide)
├── seed_demo.py         catalogue, clients, ventes, remboursement, transfert, vendeur (via l’API)
├── backdate.sql         étale ces opérations sur les semaines passées
├── catalogue-initial.csv, arrivage-septembre.csv
└── record_demo.py       enregistre le parcours avec Playwright (légendes + curseur)
```

L’ancien dossier `dist/` et `scripts/create_demo_video.py` correspondent à la première version (diaporama de captures) ; ils ne sont plus utilisés par le site.

## Aperçu local

```bash
cd docs
python3 -m http.server 8000
```

Ouvrir http://localhost:8000. Le serveur Python ne gère pas les requêtes partielles : l’avance rapide dans la vidéo peut ne pas fonctionner en local, contrairement à GitHub Pages.

## Réglages

Dans `docs/config.js` :

- `reposPublic: true` affiche les boutons et liens vers le code. **À n’activer qu’après avoir rendu les dépôts publics**, sinon les visiteurs tombent sur une page 404.
- `linkedin` et `email` : laisser vide pour masquer le lien.

## Publication gratuite avec GitHub Pages et autostockapp.com

1. Créer un dépôt **public** (par exemple `auto-stock-portfolio`) et y pousser ce dossier.
2. GitHub → Settings → Pages → Source : *Deploy from a branch*, branche `main`, dossier `/docs`.
3. OVHcloud → Web Cloud → Noms de domaine → `autostockapp.com` → Zone DNS :
   - supprimer les anciens enregistrements `A` / `AAAA` de `autostockapp.com` et `www` qui pointaient vers le VPS ;
   - ajouter 4 enregistrements `A` pour le domaine nu : `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153` ;
   - ajouter un `CNAME` pour `www` vers `alicheikcheikh.github.io.` ;
   - ne pas toucher aux enregistrements `MX`, `SPF`/`TXT` de messagerie.
4. GitHub → Settings → Pages → Custom domain : `autostockapp.com`, attendre la vérification DNS puis cocher *Enforce HTTPS*.

L’hébergement GitHub Pages est gratuit pour un dépôt public. Le nom de domaine reste payant à son renouvellement (échéance affichée : juin 2027). Sans renouvellement, retirer `docs/CNAME` : le site restera accessible gratuitement à l’adresse `https://alicheikcheikh.github.io/auto-stock-portfolio/`.

## Refaire la vidéo

Prérequis : API et interface lancées localement (voir les README backend et frontend), base PostgreSQL vide, Python 3 avec `requests` et `playwright`, ffmpeg.

```bash
psql -h localhost -U <utilisateur> -d <base> -f scripts/demo/locations.sql
# Se connecter une fois avec owner@example.test et remplacer le mot de passe temporaire.
export DEMO_OWNER_PASSWORD='<nouveau mot de passe>'
python3 scripts/demo/seed_demo.py http://localhost:8080
psql -h localhost -U <utilisateur> -d <base> -f scripts/demo/backdate.sql

APP_URL=http://localhost:4200 python3 scripts/demo/record_demo.py --debug   # captures de contrôle
APP_URL=http://localhost:4200 python3 scripts/demo/record_demo.py           # enregistrement WebM

ffmpeg -i scripts/demo/out/<fichier>.webm -vf format=yuv420p -c:v libx264 -crf 23 \
  -movflags +faststart -an docs/video/auto-stock-demo.mp4
ffmpeg -i docs/video/auto-stock-demo.mp4 -c:v libvpx-vp9 -b:v 0 -crf 40 -an docs/video/auto-stock-demo.webm
```

Le script écrit dans la base (réception, import, vente, transfert, remboursement, vendeur, famille) : repartir d’une base réinitialisée avant chaque enregistrement. Les horodatages des chapitres sont écrits dans `scripts/demo/out/chapters.txt` ; reporter les valeurs dans `docs/index.html`.

Toutes les personnes, entreprises et numéros sont fictifs. Aucune donnée du client n’est utilisée.
