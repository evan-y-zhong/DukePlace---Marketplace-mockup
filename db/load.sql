-- Load users
\COPY Users FROM 'Users.csv' WITH (FORMAT csv, HEADER false, DELIMITER ',', NULL 'NULL');
SELECT pg_catalog.setval('public.users_id_seq', (SELECT MAX(id)+1 FROM Users), false);

-- Load other tables as previously described
\COPY Products FROM 'Products.csv' WITH (FORMAT csv, HEADER false, DELIMITER ',', NULL 'NULL');
SELECT pg_catalog.setval('public.products_id_seq', (SELECT MAX(id)+1 FROM Products), false);

\COPY Purchases FROM 'Purchases.csv' WITH (FORMAT csv, HEADER false, DELIMITER ',', NULL '');
SELECT pg_catalog.setval('public.purchases_id_seq', (SELECT MAX(id)+1 FROM Purchases), false);

\COPY Inventory FROM 'Inventory.csv' WITH (FORMAT csv, HEADER false, DELIMITER ',', NULL '');
SELECT pg_catalog.setval('public.inventory_id_seq', (SELECT MAX(id) + 1 FROM Inventory), false);

\COPY Feedback FROM 'Feedback.csv' WITH (FORMAT csv, HEADER false, DELIMITER ',', NULL '');
SELECT pg_catalog.setval('public.feedback_id_seq', (SELECT MAX(id)+1 FROM Feedback), false);

\COPY BalanceHistory FROM 'BalanceHistory.csv' WITH (FORMAT csv, HEADER false, DELIMITER ',', NULL '');
SELECT pg_catalog.setval('public.balancehistory_id_seq', (SELECT MAX(id)+1 FROM BalanceHistory), false);

\COPY Coupons FROM 'Coupons.csv' WITH (FORMAT csv, HEADER false, DELIMITER ',', NULL '');
SELECT pg_catalog.setval('public.coupons_id_seq', (SELECT MAX(id)+1 FROM Coupons), false);

UPDATE Products 
SET available = FALSE
WHERE id NOT IN (
    SELECT DISTINCT product_id
    FROM Inventory
);