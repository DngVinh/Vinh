$ErrorActionPreference = "Stop"
$env:PYTHONDONTWRITEBYTECODE = "1"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$validatorPath = Join-Path $repoRoot "tasks/tools/validate_catalog.py"

if (-not (Test-Path $validatorPath)) {
    Write-Error "Validator script not found at $validatorPath"
    exit 1
}

Write-Host "Running task catalog validator..." -ForegroundColor Cyan
python $validatorPath
$exitCode = $LASTEXITCODE

if ($exitCode -ne 0) {
    Write-Error "Task catalog validation failed with exit code $exitCode"
    exit $exitCode
}

Write-Host "Task catalog validation succeeded." -ForegroundColor Green
exit 0
