param(
  [string]$ApiUrl = "https://699cb5430037a8a18f1c.sgp.appwrite.run/"
)

$ErrorActionPreference = "Stop"

$releaseDir = Join-Path $PSScriptRoot "..\build\windows\x64\runner\Release"
$imagesDir = Join-Path $releaseDir "Images"

# Work around intermittent msix cleanup race on Release\Images.
if (Test-Path $imagesDir) {
  Remove-Item -Recurse -Force $imagesDir
}

Push-Location (Join-Path $PSScriptRoot "..")
try {
  dart run msix:create --store --windows-build-args "--dart-define=API_URL=$ApiUrl"
} finally {
  Pop-Location
}
