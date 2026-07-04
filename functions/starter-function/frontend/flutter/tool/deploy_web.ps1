param(
  [string]$ApiUrl = "https://699cb5430037a8a18f1c.sgp.appwrite.run/",
  [string]$BaseHref = "/",
  [ValidateSet("release", "profile", "debug")]
  [string]$BuildMode = "release",
  [string]$DeployDir = "",
  [bool]$DeployToVercel = $true,
  [bool]$VercelProd = $true,
  [string]$VercelToken = "",
  [string]$VercelScope = ""
)

$ErrorActionPreference = "Stop"

$projectRoot = Join-Path $PSScriptRoot ".."
$webBuildDir = Join-Path $projectRoot "build\web"
$artifactsDir = Join-Path $projectRoot "build\web_artifacts"
$stagingDir = Join-Path $artifactsDir "site"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$zipPath = Join-Path $artifactsDir "schoolplannr-web-$timestamp.zip"

function Normalize-BaseHref {
  param([string]$Value)

  if ([string]::IsNullOrWhiteSpace($Value)) {
    return "/"
  }

  $normalized = $Value.Trim()

  if (-not $normalized.StartsWith("/")) {
    $normalized = "/$normalized"
  }

  if (-not $normalized.EndsWith("/")) {
    $normalized = "$normalized/"
  }

  return $normalized
}

function Add-VercelSpaConfig {
  param([string]$TargetDir)

  $vercelConfigPath = Join-Path $TargetDir "vercel.json"
  $vercelConfig = @'
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
'@

  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($vercelConfigPath, $vercelConfig, $utf8NoBom)
}

function Invoke-VercelDeploy {
  param(
    [string]$ProjectRoot,
    [string]$TargetDir,
    [bool]$IsProd,
    [string]$Token,
    [string]$Scope
  )

  $vercel = Get-Command vercel -ErrorAction SilentlyContinue
  if (-not $vercel) {
    throw "Vercel CLI not found. Install it with: npm i -g vercel"
  }

  $linkedProjectPath = Join-Path $ProjectRoot ".vercel\project.json"
  if (-not (Test-Path $linkedProjectPath)) {
    throw "No linked Vercel project found at $linkedProjectPath. Run 'vercel link' from $ProjectRoot once to connect your existing app."
  }

  $args = @("deploy", $TargetDir, "--yes")
  if ($IsProd) {
    $args += "--prod"
  }
  if (-not [string]::IsNullOrWhiteSpace($Token)) {
    $args += @("--token", $Token)
  }
  if (-not [string]::IsNullOrWhiteSpace($Scope)) {
    $args += @("--scope", $Scope)
  }

  & $vercel.Source @args
  if ($LASTEXITCODE -ne 0) {
    throw "Vercel deployment failed with exit code $LASTEXITCODE"
  }
}

$normalizedBaseHref = Normalize-BaseHref -Value $BaseHref

Write-Host "[1/5] Getting Flutter dependencies..."
Push-Location $projectRoot
try {
  flutter pub get

  Write-Host "[2/5] Building web bundle ($BuildMode)..."
  flutter build web --$BuildMode --base-href "$normalizedBaseHref" --dart-define="API_BASE_URL=$ApiUrl"

  if (-not (Test-Path $webBuildDir)) {
    throw "Expected Flutter web output not found at $webBuildDir"
  }

  if (-not (Test-Path $artifactsDir)) {
    New-Item -Path $artifactsDir -ItemType Directory | Out-Null
  }

  if (Test-Path $stagingDir) {
    Remove-Item -Recurse -Force $stagingDir
  }

  Write-Host "[3/5] Preparing deploy artifacts..."
  Copy-Item -Path $webBuildDir -Destination $stagingDir -Recurse -Force
  Add-VercelSpaConfig -TargetDir $stagingDir

  if (Test-Path $zipPath) {
    Remove-Item -Force $zipPath
  }

  Compress-Archive -Path (Join-Path $stagingDir "*") -DestinationPath $zipPath -CompressionLevel Optimal -Force

  if (-not [string]::IsNullOrWhiteSpace($DeployDir)) {
    $resolvedDeployDir = if ([System.IO.Path]::IsPathRooted($DeployDir)) {
      $DeployDir
    } else {
      Join-Path $projectRoot $DeployDir
    }

    if (-not (Test-Path $resolvedDeployDir)) {
      New-Item -Path $resolvedDeployDir -ItemType Directory | Out-Null
    }

    # Mirror generated web files into the target hosting directory.
    Copy-Item -Path (Join-Path $webBuildDir "*") -Destination $resolvedDeployDir -Recurse -Force
    Add-VercelSpaConfig -TargetDir $resolvedDeployDir
    Write-Host "[Info] Deployed web files to: $resolvedDeployDir"
  }

  if ($DeployToVercel) {
    Write-Host "[4/5] Deploying to linked Vercel app..."
    Invoke-VercelDeploy -ProjectRoot $projectRoot -TargetDir $stagingDir -IsProd $VercelProd -Token $VercelToken -Scope $VercelScope
  } else {
    Write-Host "[4/5] Skipping Vercel deployment (--DeployToVercel:$DeployToVercel)."
  }

  Write-Host "[5/5] Done."
  Write-Host ""
  Write-Host "Artifacts:"
  Get-Item $stagingDir, $zipPath | Select-Object FullName, Length, LastWriteTime | Format-List
} finally {
  Pop-Location
}
