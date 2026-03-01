param(
    [string]$ConnectionString = "Host=localhost;Port=5432;Database=ingestv2;Username=postgres;Password=postgres"
)

$ErrorActionPreference = "Stop"

Write-Output "INGEST V2 ? Minimal Migration Runner"

$files = Get-ChildItem -Path "..\ic_v2" -Filter "*.sql" | Sort-Object Name

foreach ($file in $files) {
    Write-Output "Executing $($file.Name)..."
    psql $ConnectionString -f $file.FullName
}

Write-Output "Migrations completed."