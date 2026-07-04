param(
  [string]$FunctionDomain = "https://699cb5430037a8a18f1c.sgp.appwrite.run",
  [switch]$AllowLocalApi,
  [switch]$SplitPerAbi
)

$ErrorActionPreference = "Stop"

$projectRoot = Join-Path $PSScriptRoot ".."
$apkOutputDir = Join-Path $projectRoot "build\app\outputs\flutter-apk"

Write-Host "[1/3] Getting Flutter dependencies..."
Push-Location $projectRoot
try {
  flutter pub get

  $buildArgs = @(
    "build",
    "apk",
    "--release",
    "--dart-define=API_BASE_URL=$FunctionDomain",
    "--dart-define=FUNCTION_DOMAIN=$FunctionDomain"
  )

  if ($AllowLocalApi.IsPresent) {
    $buildArgs += "--dart-define=ALLOW_LOCAL_API=true"
  }

  if ($SplitPerAbi.IsPresent) {
    $buildArgs += "--split-per-abi"
  }

  Write-Host "[2/3] Building Android APK..."
  flutter @buildArgs

  Write-Host "[3/3] Build complete. APK output:"
  Get-ChildItem -Path $apkOutputDir -Filter "*.apk" -File |
    Select-Object FullName, Length, LastWriteTime |
    Format-List
}
finally {
  Pop-Location
}
