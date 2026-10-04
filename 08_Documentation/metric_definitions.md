# Metric definitions and exclusions

- Marketplace GMV is item price, not Olist commission revenue. Freight and platform take rate are excluded.
- SDR, sales representative, business segment and lead type exist only on won deals. Their conversion rates cannot be computed without assignments for lost leads.
- Activation is the first observed post-close delivered order; active seller and first-order stages cannot be separately identified.
- Recent acquisitions have shorter observation windows. No causal channel comparison, channel ROI, CAC or long-term LTV is claimed.
- Only converted sellers linking to marketplace orders can be monetized. Sellers without matches remain in the activation denominator.
- Negative lead-to-close durations are excluded from closing-speed averages, but those deal records remain in conversion and attribution counts.

Conversion = wins / all MQLs. Activation = sellers with >=1 post-close delivered order / wins. Repeat seller rate = sellers with >=2 orders / active sellers. GMV = item price from delivered orders purchased on or after won_date. Attributed AOV = attributable item GMV / distinct marketplace orders containing an attributed item. Seller-order counts are seller-order pairs, not necessarily marketplace orders. Value-frequency segments use active-seller median GMV and median order frequency, and keep nonactivated separate. Top 10% uses ceiling(n x 0.10), exact seller_id tie-break. No time-adjusted causal channel ranking is implied.
