param(
  [string]$HostName = "root@82.21.72.233",
  [string]$KeyPath = "$HOME\.ssh\athena_content_ed25519",
  [string]$RemotePath = "/opt/athena-content"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$tempArchive = Join-Path $env:TEMP "athena-content-deploy.tar"

Write-Host "Syncing repo to server..."

if (Test-Path $tempArchive) {
  Remove-Item $tempArchive -Force
}

tar.exe `
  --exclude=".git" `
  --exclude=".env" `
  --exclude=".next" `
  --exclude="*.log" `
  --exclude="*.err.log" `
  --exclude="*.db" `
  --exclude="__pycache__" `
  --exclude="apps/web/node_modules" `
  --exclude="apps/api/venv" `
  --exclude="apps/api/.venv" `
  --exclude="apps/api/content_autopilot_api.egg-info" `
  --exclude=".logs" `
  --exclude=".tmp" `
  -cf $tempArchive `
  -C $repoRoot .

scp -i $KeyPath $tempArchive "${HostName}:/tmp/athena-content-deploy.tar"
ssh -i $KeyPath $HostName @"
set -e
mkdir -p $RemotePath /tmp/athena-content-deploy
rm -rf /tmp/athena-content-deploy/*
tar -xf /tmp/athena-content-deploy.tar -C /tmp/athena-content-deploy
if [ -f $RemotePath/.env ]; then cp $RemotePath/.env /tmp/athena-content.env.backup; fi
find $RemotePath -mindepth 1 -maxdepth 1 ! -name '.env' -exec rm -rf {} +
cp -a /tmp/athena-content-deploy/. $RemotePath/
if [ -f /tmp/athena-content.env.backup ]; then mv /tmp/athena-content.env.backup $RemotePath/.env; fi
rm -rf /tmp/athena-content-deploy /tmp/athena-content-deploy.tar
"@

Remove-Item $tempArchive -Force

Write-Host "Rebuilding web and api..."
ssh -i $KeyPath $HostName "cd $RemotePath && docker compose build api web && docker compose up -d postgres redis && docker compose run --rm api alembic upgrade head && docker compose up -d web api"

Write-Host "Checking health..."
ssh -i $KeyPath $HostName "for i in 1 2 3 4 5 6 7 8 9 10; do curl -fsS http://127.0.0.1:8000/api/health >/dev/null 2>&1 && curl -fsS http://127.0.0.1:3000 >/dev/null 2>&1 && exit 0; sleep 5; done; exit 1"
