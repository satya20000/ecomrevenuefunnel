-- CTEs, ranks, lag/lead and running totals.

-- name: seller_pareto
WITH ranked AS (SELECT seller_id,origin,gmv,orders,ROW_NUMBER() OVER(ORDER BY gmv DESC,seller_id) seller_rank,COUNT(*) OVER() n,SUM(gmv) OVER() total FROM fact_lead WHERE active=1) SELECT *,SUM(gmv) OVER(ORDER BY seller_rank ROWS UNBOUNDED PRECEDING)/NULLIF(total,0) cumulative_gmv_share,CASE WHEN seller_rank<=CAST(n*0.1+0.999999 AS INTEGER) THEN 1 ELSE 0 END top10_flag FROM ranked ORDER BY seller_rank;

-- name: monthly_gmv_growth
WITH m AS (SELECT substr(order_purchase_timestamp,1,7) month,SUM(gmv) gmv FROM fact_seller_order GROUP BY 1) SELECT *,LAG(gmv) OVER(ORDER BY month) prior_gmv,SUM(gmv) OVER(ORDER BY month ROWS UNBOUNDED PRECEDING) cumulative_gmv FROM m ORDER BY month;

-- name: seller_order_sequence
SELECT seller_id,order_id,order_purchase_timestamp,gmv,ROW_NUMBER() OVER(PARTITION BY seller_id ORDER BY order_purchase_timestamp,order_id) purchase_number,LAG(order_purchase_timestamp) OVER(PARTITION BY seller_id ORDER BY order_purchase_timestamp,order_id) previous_sale FROM fact_seller_order;

