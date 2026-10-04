# Relationship map

```mermaid
erDiagram
 dim_channel ||--o{ fact_lead : "origin to origin"
 dim_segment ||--o{ fact_lead : "business_segment to business_segment"
 dim_sdr ||--o{ fact_lead : "sdr_id to sdr_id"
 dim_sales_rep ||--o{ fact_lead : "sr_id to sr_id"
 dim_seller ||--o{ fact_lead : "seller_id to seller_id"
 dim_seller ||--o{ fact_seller_order : "seller_id to seller_id"
 dim_date ||--o{ fact_lead : "date to contact_date"
```

Use 06_PowerBI/relationships.csv for implementation. Logical keys are checked in the loader and duplicate_keys SQL controls. ISO date-only keys relate to dim_date[date].
