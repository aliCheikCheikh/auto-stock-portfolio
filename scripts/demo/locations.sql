-- Support de démonstration uniquement : exécuter après Flyway sur une base vide.
-- Aucun client, compte utilisateur ou produit réel n'est ajouté.
BEGIN;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM shop) OR EXISTS (SELECT 1 FROM storage_location) THEN
        RAISE EXCEPTION 'Initialisation refusée : magasin ou emplacements déjà présents';
    END IF;
END $$;
INSERT INTO shop (id, name, address) VALUES
('10000000-0000-4000-8000-000000000001', 'Magasin de démonstration', 'Adresse fictive');
INSERT INTO storage_location (id, shop_id, location_type, label, low_stock_indicator) VALUES
('20000000-0000-4000-8000-000000000001', '10000000-0000-4000-8000-000000000001', 'SHOP_FLOOR', 'Surface de démonstration', 3),
('20000000-0000-4000-8000-000000000002', '10000000-0000-4000-8000-000000000001', 'BACKSTOCK', 'Réserve de démonstration', 3);
COMMIT;
