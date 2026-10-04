# Release acceptance

## Automated build checks
- [x] JSON schemas checked against Microsoft published schemas.
- [x] Visual field references resolve to model fields and explicit measures.
- [x] Dimensions have unique keys; relationships have compatible types.
- [x] Card baselines reconciled to source CSVs.
- [x] Every visual stays inside the canvas; no peer visual overlap.

## Required Power BI Desktop checks — pending
- [ ] Configure local data path and Refresh without Power Query or relationship errors.
- [ ] Confirm baseline cards against validation.json and execute validation.dax.
- [ ] Test each slicer on a populated subgroup, clear back to All, and confirm all cards/charts/tables reconcile.
- [ ] CX: combine seller/category filters and confirm distinct order grain; compare priority queue with reviewed baselines.
- [ ] B2B: test contact-cohort filters and attributed seller-order scope; no converted-segment comparison is labeled lead conversion.
- [ ] Credit: filter year/grade/term; verify unresolved loans do not enter default/return denominators.
- [ ] Review all pages at Fit to page and 100%: labels, card text, legends, no clipping, keyboard order and contrast.
- [ ] Verify native chart role assignments, long category labels, tooltip denominators, queue measure filters and table sorting.
- [ ] Confirm empty selections show BLANK/empty state, never fabricated zero rates.
- [ ] Save a PBIX and reopen it; recheck report pages.

## Power BI Service checks — pending
- [ ] Publish to an authorized workspace and assign appropriate access.
- [ ] Configure an on-premises gateway for local CSV refresh, or deliberately migrate source queries to governed cloud storage.
- [ ] Test refresh credentials, failure notifications and refresh history; schedule only for a maintained source pipeline.
- [ ] Validate export permissions, accessibility and mobile layout; add RLS only if deploying non-public operational data.
- [ ] Obtain user acceptance before labeling this production-ready.
