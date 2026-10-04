-- Source transformations are reproducible in 04_Python. These SQL controls execute on the derived model.
-- name: duplicate_keys
SELECT mql_id,COUNT(*) copies FROM fact_lead GROUP BY mql_id HAVING COUNT(*)>1;

-- name: null_keys
SELECT COUNT(*) invalid_rows FROM fact_lead WHERE mql_id IS NULL;

