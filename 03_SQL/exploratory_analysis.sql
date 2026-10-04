-- name: row_count
SELECT COUNT(*) rows FROM fact_lead;

-- name: date_coverage
SELECT MIN(first_contact_date) first_date,MAX(first_contact_date) last_date FROM fact_lead;

