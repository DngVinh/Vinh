# Security and Supply-Chain Verification Script for Campus 24/7 (SEC-SDLC-009, SEC-SDLC-013)
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Write-Host "==> Starting Security & Supply-Chain Scan..." -ForegroundColor Cyan

# 1. Verify Lockfiles Exist
Write-Host "--> [1/3] Verifying pinned lockfiles..." -ForegroundColor Yellow
$pyLock = "uv.lock"
$webLock = "pnpm-lock.yaml"

if (-not (Test-Path $pyLock)) { throw "Missing Python lockfile: $pyLock" }
if (-not (Test-Path $webLock)) { throw "Missing Web lockfile: $webLock" }

# 2. Compute SHA-256 for SBOM Integrity
Write-Host "--> [2/3] Generating lockfile SBOM SHA-256 hashes..." -ForegroundColor Yellow
$pyHash = (Get-FileHash -Path $pyLock -Algorithm SHA256).Hash
$webHash = (Get-FileHash -Path $webLock -Algorithm SHA256).Hash

Write-Host "    [SBOM] $pyLock SHA-256: $pyHash"
Write-Host "    [SBOM] $webLock SHA-256: $webHash"

# 3. Canary and Secret Scanning
Write-Host "--> [3/3] Checking for unmasked secret canaries in source code..." -ForegroundColor Yellow
python -m pytest -q tests/security/test_no_sensitive_egress.py
if ($LASTEXITCODE -ne 0) { throw "Secret canary scan failed" }

Write-Host "==> Security and supply-chain scan passed successfully (exit code 0)." -ForegroundColor Green
exit 0
