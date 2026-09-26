# Local & CI Preflight Verification Script for Campus 24/7 (SEC-SDLC-003)
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Write-Host "==> Starting CI Preflight Verification..." -ForegroundColor Cyan

# 1. Validate Task Catalog
Write-Host "--> [1/3] Validating task catalog..." -ForegroundColor Yellow
python tasks/tools/validate_catalog.py
if ($LASTEXITCODE -ne 0) { throw "Task catalog validation failed" }

# 2. Validate OpenAPI Contracts
Write-Host "--> [2/3] Validating OpenAPI contracts..." -ForegroundColor Yellow
python contracts/tools/validate_openapi.py
if ($LASTEXITCODE -ne 0) { throw "OpenAPI validation failed" }

# 3. Run Automated Regression Test Suite
Write-Host "--> [3/3] Running pytest regression suite..." -ForegroundColor Yellow
python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Pytest regression suite failed" }

Write-Host "==> All CI preflight checks passed successfully (exit code 0)." -ForegroundColor Green
exit 0
