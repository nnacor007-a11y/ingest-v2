param(
    [string]$ConnectionString = "Host=localhost;Port=5432;Database=ingestv2;Username=postgres;Password=postgres"
)

$ErrorActionPreference = "Stop"

Write-Output "INGEST V2 ? Minimal Migration Runner"

$files = Get-ChildItem -Path "..\ic_v2" -Filter "*.sql" | Sort-Object Name

foreach ($file in $files) {

    $checksum = (Get-FileHash $file.FullName -Algorithm SHA256).Hash

    $exists = psql $ConnectionString -t -c "SELECT 1 FROM ic_v2.migration_log WHERE filename = '$($file.Name)';"

    if ($exists.Trim() -eq "1") {
        Write-Output "Skipping $($file.Name) (already executed)"
        continue
    }

    Write-Output "Executing $($file.Name)..."
    psql $ConnectionString -f $file.FullName

    psql $ConnectionString -c "INSERT INTO ic_v2.migration_log (filename, checksum) VALUES ('$($file.Name)', '$checksum');"
}

Write-Output "Migrations completed."