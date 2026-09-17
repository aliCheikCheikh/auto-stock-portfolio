"""Remplit une base de démonstration VIDE d'Auto Stock Management via l'API.

Prérequis :
  - API démarrée (profil dev) avec le propriétaire initial owner@example.test ;
  - locations.sql exécuté sur la base (magasin + surface + réserve) ;
  - mot de passe temporaire du propriétaire déjà remplacé (DEMO_OWNER_PASSWORD).

Toutes les données sont fictives. Les numéros commencent par +235 10, une plage
non attribuée aux mobiles, pour ne cibler personne.

Usage : DEMO_OWNER_PASSWORD='...' python3 seed_demo.py [http://localhost:8080]
"""
import os
import sys
import uuid
from pathlib import Path

import requests

API = (sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8080').rstrip('/') + '/api/v1'
HERE = Path(__file__).resolve().parent
EMAIL = os.environ.get('DEMO_OWNER_EMAIL', 'owner@example.test')
PASSWORD = os.environ['DEMO_OWNER_PASSWORD']

s = requests.Session()
s.trust_env = False


def ok(response):
    if response.status_code >= 300:
        raise SystemExit(f'{response.request.method} {response.url} -> {response.status_code}\n{response.text[:500]}')
    return response.json() if response.text else None


def idem():
    return {'Idempotency-Key': str(uuid.uuid4())}


ok(s.post(f'{API}/auth/login', json={'email': EMAIL, 'password': PASSWORD}))
ctx = ok(s.get(f'{API}/context'))
shop = ctx['shopId']
loc = {l['type']: l['locationId'] for l in ctx['locations']}

if ok(s.get(f'{API}/products', params={'size': 1}))['page']['totalElements'] > 0:
    raise SystemExit('La base contient déjà des produits : ce script attend une base vide.')

# 1. Catalogue initial (34 références) par l'import CSV.
csv = (HERE / 'catalogue-initial.csv').read_bytes()
preview = ok(s.post(f'{API}/stock-receipts/import-preview', params={'shopId': shop},
                    files={'file': ('catalogue-initial.csv', csv, 'text/csv')}))
lines = [str(r['lineNumber']) for r in preview['rows'] if not r['issues']]
ok(s.post(f'{API}/stock-receipts/import-executions',
          data={'importId': str(uuid.uuid4()), 'shopId': shop, 'selectedLineNumbers': lines},
          files={'file': ('catalogue-initial.csv', csv, 'text/csv')}))
products = {p['reference']: p['productId'] for p in ok(s.get(f'{API}/products', params={'size': 100}))['content']}

# 2. Clients fictifs.
def customer(given, father, phone):
    return ok(s.post(f'{API}/customers', json={'givenName': given, 'fatherName': father, 'phoneNumber': phone}))['customerId']

mahamat = customer('Mahamat', 'Abakar', '+235 10 00 00 01')
achta = customer('Achta', 'Brahim', '+235 10 00 00 02')
garage = customer('Garage', 'Démo', '+235 10 00 00 03')

# 3. Ventes comptant et à crédit.
def sale(lines, customer_id=None, paid=None):
    body = {'shopId': shop, 'lines': [{'productId': products[ref], 'quantity': q} for ref, q in lines]}
    if customer_id:
        body |= {'customerId': customer_id, 'amountPaid': paid}
    return ok(s.post(f'{API}/sales', json=body, headers=idem()))

sale([('PNE-195-1410', 2)])
sale([('MOT-BGI-6620', 4), ('ELC-AMP-1310', 2)])
sale([('FLT-HUI-2210', 2), ('FRN-LIQ-4420', 1)])
sale([('ELC-BAT-1301', 1)], achta, 25000)
sale([('FRN-PLQ-4401', 1), ('SUS-AMO-8801', 2)], mahamat, 40000)
sale([('FLT-AIR-1042', 3), ('FLT-HUI-2210', 3), ('MOT-CRR-6601', 1)], garage, 0)

# 4. Un remboursement, un transfert, un vendeur.
debt = next(d for d in ok(s.get(f'{API}/debts'))['content'] if d['customerGivenName'] == 'Mahamat')
ok(s.post(f'{API}/sales/{debt["saleId"]}/payments', json={'amount': 20000}))
ok(s.post(f'{API}/stock-transfers', headers=idem(), json={
    'productId': products['MOT-BGI-6620'], 'sourceLocationId': loc['BACKSTOCK'],
    'destinationLocationId': loc['SHOP_FLOOR'], 'quantity': 6}))
ok(s.post(f'{API}/users', json={'displayName': 'Oumar Vendeur', 'email': 'vendeur@example.test'}))

print('Données fictives créées : 34 produits, 3 clients, 6 ventes, 1 remboursement, 1 transfert, 1 vendeur.')
print('Optionnel : psql ... -f backdate.sql pour étaler ces opérations sur les semaines passées.')
