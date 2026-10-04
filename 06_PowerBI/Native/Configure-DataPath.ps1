$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$folder = Join-Path $root "02_Cleaned_Data"
if ((Test-Path (Join-Path $folder "fact_order.csv.gz.part001")) -and !(Test-Path (Join-Path $folder "fact_order.csv"))) {
  $target = Join-Path $folder "fact_order.csv"
  $combined = New-Object System.IO.MemoryStream
  Get-ChildItem (Join-Path $folder "fact_order.csv.gz.part*") | Sort-Object Name | ForEach-Object {
    $bytes = [IO.File]::ReadAllBytes($_.FullName); $combined.Write($bytes,0,$bytes.Length)
  }
  $combined.Position = 0
  $gzip = New-Object IO.Compression.GzipStream($combined,[IO.Compression.CompressionMode]::Decompress)
  $output = [IO.File]::Create($target)
  try {$gzip.CopyTo($output)} finally {$output.Dispose();$gzip.Dispose();$combined.Dispose()}
}
$modelFile = (Get-ChildItem (Join-Path $PSScriptRoot "*.SemanticModel/model.bim")).FullName
$model = Get-Content $modelFile -Raw | ConvertFrom-Json
$model.model.expressions[0].expression = '"' + $folder.Replace('"','""') + '" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'
$json = $model | ConvertTo-Json -Depth 100
[IO.File]::WriteAllText($modelFile,$json,(New-Object Text.UTF8Encoding($false)))
Write-Host "Configured data path. Open the PBIP and Refresh."
