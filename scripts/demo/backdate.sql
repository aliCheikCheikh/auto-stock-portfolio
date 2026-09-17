-- Démonstration uniquement : étale dans le passé les opérations créées par seed_demo.py,
-- pour que le tableau de bord et les créances affichent des anciennetés réalistes.
-- À exécuter une seule fois, juste après seed_demo.py, sur la base fictive.
BEGIN;

UPDATE stock_movement SET occurred_at = now() - interval '45 days' WHERE movement_type = 'ENTRY';
UPDATE stock_movement SET occurred_at = now() - interval '3 days'  WHERE movement_type = 'TRANSFER';

-- Ventes à crédit, identifiées par le client fictif.
UPDATE sale s SET occurred_at = now() - interval '38 days 4 hours'
FROM customer c WHERE c.id = s.customer_id AND c.given_name = 'Achta';
UPDATE sale s SET occurred_at = now() - interval '12 days 2 hours'
FROM customer c WHERE c.id = s.customer_id AND c.given_name = 'Mahamat';
UPDATE sale s SET occurred_at = now() - interval '5 days 1 hour'
FROM customer c WHERE c.id = s.customer_id AND c.given_name = 'Garage';

-- Ventes comptant, dans l'ordre de création.
WITH cash AS (
    SELECT id, row_number() OVER (ORDER BY occurred_at) AS rn FROM sale WHERE customer_id IS NULL
)
UPDATE sale s SET occurred_at = now() - CASE cash.rn
        WHEN 1 THEN interval '20 days 3 hours'
        WHEN 2 THEN interval '9 days 5 hours'
        ELSE interval '1 day 6 hours' END
FROM cash WHERE cash.id = s.id;

-- Sorties de stock et acompte à la date de leur vente ; le remboursement ultérieur six jours avant aujourd'hui.
UPDATE stock_movement m SET occurred_at = s.occurred_at FROM sale s WHERE m.sale_id = s.id;
WITH ranked AS (
    SELECT id, sale_id, row_number() OVER (PARTITION BY sale_id ORDER BY received_at) AS rn FROM payment
)
UPDATE payment p SET received_at = CASE WHEN r.rn = 1 THEN s.occurred_at ELSE now() - interval '6 days' END
FROM ranked r JOIN sale s ON s.id = r.sale_id
WHERE r.id = p.id;

COMMIT;
