-- Grain-safe SQLite business queries. Monetary values are source currencies.

-- name: portfolio_kpis
SELECT COUNT(*) leads,SUM(converted) closed_deals,AVG(converted*1.0) conversion_rate,SUM(active) active_sellers,SUM(gmv) gmv,SUM(gmv)/NULLIF(SUM(converted),0) gmv_per_converted_seller,AVG(close_days) close_days FROM fact_lead;

-- name: funnel_stages
SELECT 'MQL' stage,COUNT(*) sellers FROM fact_lead UNION ALL SELECT 'Closed',SUM(converted) FROM fact_lead UNION ALL SELECT 'First delivered sale',SUM(active) FROM fact_lead UNION ALL SELECT 'Repeat seller',SUM(repeat_seller) FROM fact_lead;

-- name: channel_quality
SELECT origin,COUNT(*) leads,SUM(converted) closed_deals,AVG(converted*1.0) conversion_rate,SUM(active) active_sellers,SUM(active)*1.0/NULLIF(SUM(converted),0) activation_rate,SUM(gmv) gmv,SUM(gmv)/COUNT(*) gmv_per_lead,SUM(gmv)/NULLIF(SUM(converted),0) gmv_per_converted,AVG(close_days) close_days FROM fact_lead GROUP BY origin;

-- name: monthly_leads
SELECT lead_month,COUNT(*) leads,SUM(converted) eventual_closed,AVG(converted*1.0) eventual_conversion_rate,SUM(gmv) observed_gmv FROM fact_lead GROUP BY lead_month ORDER BY lead_month;

-- name: monthly_closes
SELECT close_month,COUNT(*) closed_deals,AVG(close_days) close_days FROM fact_lead WHERE converted=1 GROUP BY close_month ORDER BY close_month;

-- name: landing_page_quality
SELECT landing_page_id,COUNT(*) leads,SUM(converted) closed_deals,AVG(converted*1.0) conversion_rate,SUM(gmv)/COUNT(*) gmv_per_lead FROM fact_lead GROUP BY landing_page_id HAVING COUNT(*)>=30;

-- name: segment_value
SELECT business_segment,COUNT(*) closed_deals,SUM(active) active_sellers,SUM(gmv) gmv,AVG(gmv) gmv_per_closed,AVG(close_days) close_days FROM fact_lead WHERE converted=1 GROUP BY business_segment;

-- name: lead_type_value
SELECT lead_type,COUNT(*) closed_deals,SUM(active) active_sellers,SUM(gmv) gmv,AVG(gmv) gmv_per_closed,AVG(close_days) close_days FROM fact_lead WHERE converted=1 GROUP BY lead_type;

-- name: sdr_won_lead_value
SELECT sdr_id,COUNT(*) closed_deals,SUM(active) active_sellers,SUM(gmv) gmv,AVG(gmv) gmv_per_closed,AVG(close_days) close_days FROM fact_lead WHERE converted=1 GROUP BY sdr_id;

-- name: sales_rep_value
SELECT sr_id,COUNT(*) closed_deals,SUM(active) active_sellers,SUM(gmv) gmv,AVG(gmv) gmv_per_closed,AVG(close_days) close_days FROM fact_lead WHERE converted=1 GROUP BY sr_id;

-- name: seller_geography
SELECT seller_state,COUNT(*) closed_deals,SUM(active) active_sellers,SUM(gmv) gmv,AVG(gmv) gmv_per_closed,AVG(close_days) close_days FROM fact_lead WHERE converted=1 GROUP BY seller_state;

-- name: activation_speed
SELECT origin,COUNT(*) activated,AVG(close_to_first_sale_days) first_sale_days,AVG(orders*1.0) orders_per_active_seller FROM fact_lead WHERE active=1 GROUP BY origin;

-- name: seller_segments
SELECT seller_segment,COUNT(*) sellers,SUM(gmv) gmv,AVG(orders*1.0) orders FROM fact_lead GROUP BY seller_segment;

-- name: repeat_sellers
SELECT origin,SUM(repeat_seller) repeat_sellers,SUM(repeat_seller)*1.0/NULLIF(SUM(active),0) repeat_among_active FROM fact_lead GROUP BY origin;

-- name: order_value
SELECT COUNT(DISTINCT order_id) attributed_marketplace_orders,COUNT(*) seller_order_pairs,SUM(gmv) gmv,SUM(gmv)/COUNT(DISTINCT order_id) attributed_item_gmv_per_order FROM fact_seller_order;

-- name: nonactivated_wins
SELECT mql_id,seller_id,origin,won_date,close_days FROM fact_lead WHERE converted=1 AND active=0 ORDER BY won_date;

-- name: channel_volume_quality
SELECT * FROM (SELECT origin,COUNT(*) leads,AVG(converted*1.0) conversion_rate,SUM(gmv)/COUNT(*) gmv_per_lead FROM fact_lead GROUP BY origin) WHERE leads >= (SELECT COUNT(*)*0.05 FROM fact_lead) ORDER BY gmv_per_lead;

