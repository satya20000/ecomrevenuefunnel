// Query parameter DataFolder: text, absolute path to 02_Cleaned_Data.
// Function query name: LoadTable
(TableName as text) as table =>
let
    Source = Csv.Document(File.Contents(DataFolder & "/" & TableName & ".csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Nulls = Table.TransformColumns(Headers, List.Transform(Table.ColumnNames(Headers), (column) => {column, each if _ = "" then null else _, type nullable text}))
in Nulls
