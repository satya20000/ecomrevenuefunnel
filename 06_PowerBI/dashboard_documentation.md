# Power BI build package

No Power BI Desktop was run. No .pbix or Power BI screenshot is claimed. Python previews are labeled explicitly.

## Import and types
Create a text parameter `DataFolder` pointing to 02_Cleaned_Data. Create function `LoadTable` from power_query.m. For every cleaned CSV create a query `LoadTable("fact_lead")`, replacing the table name. All CSVs are final cleaned exports, not raw data; major transformations live in Python. Apply types from column_types.json; parse dates with locale en-US. Hide row keys. Set numerical attributes to Do not summarize unless measures are used. Mark dim_date as date table.

## Relationships
Use relationships.csv. Single-direction filters only. Verify one-side uniqueness before activation.

Revenue cards use fact_lead[gmv] and therefore describe observed downstream value of the selected lead cohorts. The seller-order table is separate: channel/SDR selections do not propagate to it through single-direction relationships. Use a dedicated sales-date dimension linked to fact_seller_order[purchase_date] for calendar sales trends; for channel-scoped order metrics apply TREATAS from filtered fact_lead[seller_id] to fact_seller_order[seller_id]. Do not divide won deals by rep assignments because lost-lead assignments are missing.

## Layout and interactions
Each page is 1280 x 720, white background, 24 px margins. Header at y=20, page title 24 pt. At most 5 KPI cards in a 96 px row. Use two or three charts below; axes 11 pt minimum. Synced slicers on left for dates and relevant dimension. Add denominator and coverage tooltips to rates. Chart selections cross-filter charts on the same page. Provide reset filters bookmark and accessible alt text. No red/green-only encoding. Use Top N 15 plus detail drillthrough rather than overcrowded bars.

## Page and visual specifications

### Executive Funnel

| Visual | DAX measures | Business question | Source/axis |
|---|---|---|---|
| KPI cards | Total MQLs; Closed Deals; Conversion Rate; Active Sellers; Attributed GMV | How much of acquisition translates to observed value? | fact_lead |
| Funnel | Total MQLs; Closed Deals; Active Sellers; Repeat Sellers | Where do observable stages lose sellers? | fact_lead |
| Line | Total MQLs; Conversion Rate | Which acquisition cohorts convert? | dim_date[month] |
| Bar | Attributed GMV | Which channels generate item value? | dim_channel[origin] |

### Marketing Channel Performance

| Visual | DAX measures | Business question | Source/axis |
|---|---|---|---|
| Matrix | Total MQLs; Conversion Rate; Activation Rate; GMV per Lead | Which channels trade volume for value? | dim_channel[origin] |
| Scatter | Conversion Rate; GMV per Lead | Which channels merit a controlled spend test? | dim_channel[origin] |
| Bar | GMV per Lead | Where is value per acquisition strongest? | dim_channel[origin] |

### Sales Team Performance

| Visual | DAX measures | Business question | Source/axis |
|---|---|---|---|
| Bar | Closed Deals; Average Close Days | Which representatives close more and faster? | dim_sales_rep[sr_id] |
| Bar | Attributed GMV; GMV per Converted Seller | Which representatives acquire valuable sellers? | dim_sales_rep[sr_id] |
| Matrix | Closed Deals; Attributed GMV | How do SDR won-lead outcomes differ? | dim_sdr[sdr_id] |

### Seller Value

| Visual | DAX measures | Business question | Source/axis |
|---|---|---|---|
| KPI | Top 10 Percent GMV Share | How concentrated is item value? | fact_lead |
| Bar | Attributed GMV | Which value-frequency segments matter? | fact_lead[seller_segment] |
| Table | Attributed GMV; Seller Order Pairs | Which merchants warrant account review? | dim_seller[seller_id] |
| Bar | Attributed GMV | Where are acquired seller accounts located? | dim_seller[seller_state] |

## Acceptance checks
Match all unfiltered cards to 03_SQL/results/portfolio_kpis.csv (KKBOX uses monthly_subscription.csv). Test a single dimension, two combined filters and an empty selection. Verify rates recalculate from numerator/denominator, rather than mean of group rates. For CX compare distinct orders before/after bridge selection. For loans active outcomes must stay out of default denominators. Drillthrough to underlying rows and reset filters. DAX and Power Query assets have not been executed in Power BI Desktop.
