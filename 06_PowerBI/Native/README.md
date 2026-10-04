# Seller acquisition & value — native Power BI project

Open **RevenueFunnel.pbip** in a current Power BI Desktop installation. This package contains an actual semantic model and editable native report pages; the original analysis package remains available beside it.

## First open

1. Clone/download the complete repository, preserving folders.
2. Run `python 06_PowerBI/Native/configure.py`, or run `Configure-DataPath.ps1` from PowerShell. The Customer Experience setup restores its split order CSV automatically if needed.
3. Open `06_PowerBI/Native/RevenueFunnel.pbip`, select **Refresh**, and inspect all four pages. If prompted, enable Power BI project/report developer features supported by your Desktop release.
4. Save a PBIX copy from Desktop when needed. Publish to your own workspace after the release checks below pass.

## Report structure

- Overview: primary outcomes, trajectory, important driver comparison and filter-responsive context.
- Drivers: compatible cohorts/segments with counts and weighted ratios.
- Investigations: explicit sample thresholds and identifiable records for follow-up.
- Definitions & use: snapshot scope, denominators, refresh and acceptance guidance.

Three page-local slicers apply to that page. They intentionally reset scope when changing pages rather than silently carrying a hidden cross-page selection. Native chart selection filters peer visuals; use slicer clear controls to reset. Hover for denominators where provided. Table export includes the current context.

## Semantic model

Import mode, typed CSV sources, explicit DAX measures, and validated many-to-one relationships with single-direction filtering. All numeric raw columns have automatic summarization disabled. Dates use the supplied date dimension; automatic date tables are disabled. CX seller/category selection reaches order-grain measures via KEEPFILTERS/TREATAS, preventing item duplication. LendingClub return uses only resolved funding and resolved net cash. B2B date filters describe lead contact cohorts, not booking/revenue months.

Currency: BRL; return and rate measures are fractions with percentage formatting. No synthetic targets, unobserved spend/ROI, causal conclusions or FICO values are introduced. `Historical lead cohorts • GMV is item merchandise value, not platform revenue • Shorter observation for recent wins`.

## Validation and release status

See `validation.json` and `RELEASE_CHECKLIST.md`. JSON schema, field-binding, geometry, relationship and baseline-data checks run in the build environment. **No Power BI engine or Desktop is available here: report rendering and DAX execution are not certified.** Treat this as a release candidate until Desktop/Service checks pass. No .pbix or Service deployment is claimed.

Power BI project documentation: https://learn.microsoft.com/power-bi/developer/projects/projects-overview
Report format: https://learn.microsoft.com/power-bi/developer/projects/projects-report
Semantic models: https://learn.microsoft.com/power-bi/developer/projects/projects-dataset
