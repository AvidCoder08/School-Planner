param(
  [string]$ApiUrl = "https://699cb5430037a8a18f1c.sgp.appwrite.run/"
)

$ErrorActionPreference = "Stop"

$releaseDir = Join-Path $PSScriptRoot "..\build\windows\x64\runner\Release"
$imagesDir = Join-Path $releaseDir "Images"

function Clear-ImagesDirectory {
  param(
    [int]$MaxAttempts = 6,
    [int]$DelaySeconds = 2
  )

  for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
    if (-not (Test-Path $imagesDir)) {
      return
    }

    try {
      Remove-Item -Recurse -Force $imagesDir
      return
    } catch {
      if ($attempt -eq $MaxAttempts) {
        throw
      }
      Start-Sleep -Seconds $DelaySeconds
    }
  }
}

Push-Location (Join-Path $PSScriptRoot "..")
try {
  flutter pub get
  flutter build windows --release --dart-define="API_BASE_URL=$ApiUrl"
  Clear-ImagesDirectory
  dart run msix:create --store --build-windows false --windows-build-args "--dart-define=API_BASE_URL=$ApiUrl"
} finally {
  Pop-Location
}
