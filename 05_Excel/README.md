# Excel analysis scope

The workbook contains complete aggregate/query results for business comparison. Large detailed result sets remain CSVs. Comparison formulas are editable and recalculate from imported source tables. Input tables contain actual calculated values for three projects; KKBOX is a clearly labeled empty input template. No native slicer or PivotTable is claimed. To refresh, rerun Python and use Excel Data > From Text/CSV with the relevant 03_SQL/results files, preserving the comparison formulas. See workbook_builder.mjs for automated authoring using @oai/artifact-tool in the primary runtime.

Automated build: run workbook_builder.mjs with the absolute project-folder path as its first argument. In the ChatGPT runtime, create a temporary node_modules symlink to CODEX_PRIMARY_RUNTIME_NODE_MODULES before execution.
