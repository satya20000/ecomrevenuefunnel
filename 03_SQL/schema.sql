-- SQLite 3.25+; populated by pipeline.py, CSV dates are ISO strings.
CREATE TABLE "dim_seller" (
 "seller_id" TEXT,
 "seller_zip_code_prefix" INTEGER,
 "seller_city" TEXT,
 "seller_state" TEXT
);

CREATE TABLE "dim_customer" (
 "customer_id" TEXT,
 "customer_unique_id" TEXT,
 "customer_zip_code_prefix" INTEGER,
 "customer_city" TEXT,
 "customer_state" TEXT
);

CREATE TABLE "dim_product" (
 "product_id" TEXT,
 "product_category_name" TEXT,
 "product_name_lenght" REAL,
 "product_description_lenght" REAL,
 "product_photos_qty" REAL,
 "product_weight_g" REAL,
 "product_length_cm" REAL,
 "product_height_cm" REAL,
 "product_width_cm" REAL
);

CREATE TABLE "fact_payment" (
 "order_id" TEXT,
 "payment_sequential" INTEGER,
 "payment_type" TEXT,
 "payment_installments" INTEGER,
 "payment_value" REAL
);

CREATE TABLE "dim_channel" (
 "origin" TEXT
);

CREATE TABLE "dim_segment" (
 "business_segment" TEXT
);

CREATE TABLE "dim_sdr" (
 "sdr_id" TEXT
);

CREATE TABLE "dim_sales_rep" (
 "sr_id" TEXT
);

CREATE TABLE "fact_lead" (
 "mql_id" TEXT,
 "first_contact_date" TEXT,
 "landing_page_id" TEXT,
 "origin" TEXT,
 "seller_id" TEXT,
 "sdr_id" TEXT,
 "sr_id" TEXT,
 "won_date" TEXT,
 "business_segment" TEXT,
 "lead_type" TEXT,
 "lead_behaviour_profile" TEXT,
 "has_company" TEXT,
 "has_gtin" TEXT,
 "average_stock" TEXT,
 "business_type" TEXT,
 "declared_product_catalog_size" REAL,
 "declared_monthly_revenue" REAL,
 "seller_zip_code_prefix" REAL,
 "seller_city" TEXT,
 "seller_state" TEXT,
 "converted" INTEGER,
 "close_days" REAL,
 "invalid_close_chronology" INTEGER,
 "orders" INTEGER,
 "gmv" REAL,
 "first_sale" TEXT,
 "active" INTEGER,
 "repeat_seller" INTEGER,
 "close_to_first_sale_days" REAL,
 "seller_segment" TEXT,
 "lead_month" TEXT,
 "close_month" TEXT,
 "contact_date" TEXT,
 "close_date" TEXT
);

CREATE TABLE "fact_seller_order" (
 "seller_id" TEXT,
 "order_id" TEXT,
 "order_purchase_timestamp" TEXT,
 "gmv" REAL,
 "purchase_date" TEXT
);

CREATE TABLE "dim_date" (
 "date" TEXT,
 "year" INTEGER,
 "month" TEXT,
 "quarter" INTEGER,
 "month_number" INTEGER
);