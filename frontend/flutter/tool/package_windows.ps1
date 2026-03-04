param(
  [string]$ApiUrl = "https://699cb5430037a8a18f1c.sgp.appwrite.run/",
  [string]$LocalCertPassword = "SchoolPlannrLocalTest123!"
)

$ErrorActionPreference = "Stop"

$projectRoot = Join-Path $PSScriptRoot ".."
$releaseDir = Join-Path $projectRoot "build\windows\x64\runner\Release"
$packagesDir = Join-Path $projectRoot "build\windows\packages"
$imagesDir = Join-Path $releaseDir "Images"
$certsDir = Join-Path $projectRoot "tool\certs"
$publisher = "CN=D4F3DD68-2C2F-49BC-8561-F742F3D6E84A"
$localPfxPath = Join-Path $certsDir "schoolplannr-local-test.pfx"
$localCerPath = Join-Path $certsDir "schoolplannr-local-test.cer"
$certPasswordSecure = ConvertTo-SecureString $LocalCertPassword -AsPlainText -Force

function Ensure-LocalTestCertificate {
  if (-not (Test-Path $certsDir)) {
    New-Item -Path $certsDir -ItemType Directory | Out-Null
  }

  if (-not (Test-Path $localPfxPath) -or -not (Test-Path $localCerPath)) {
    $cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject $publisher -KeyAlgorithm RSA -KeyLength 2048 -HashAlgorithm SHA256 -CertStoreLocation "Cert:\CurrentUser\My" -NotAfter (Get-Date).AddYears(3)
    Export-PfxCertificate -Cert $cert -FilePath $localPfxPath -Password $certPasswordSecure | Out-Null
    Export-Certificate -Cert $cert -FilePath $localCerPath | Out-Null
  }

  Import-Certificate -FilePath $localCerPath -CertStoreLocation "Cert:\CurrentUser\TrustedPeople" | Out-Null
  Import-Certificate -FilePath $localCerPath -CertStoreLocation "Cert:\CurrentUser\Root" | Out-Null

  $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  if ($isAdmin) {
    Import-Certificate -FilePath $localCerPath -CertStoreLocation "Cert:\LocalMachine\TrustedPeople" | Out-Null
    Import-Certificate -FilePath $localCerPath -CertStoreLocation "Cert:\LocalMachine\Root" | Out-Null
  } else {
    Write-Host "[Info] Not running as Administrator. If MSIX install shows certificate trust errors, run this once in elevated PowerShell:"
    Write-Host "Import-Certificate -FilePath '$localCerPath' -CertStoreLocation 'Cert:\LocalMachine\TrustedPeople'"
    Write-Host "Import-Certificate -FilePath '$localCerPath' -CertStoreLocation 'Cert:\LocalMachine\Root'"
  }
}

Write-Host "[1/5] Getting Flutter dependencies..."
Push-Location $projectRoot
try {
  flutter pub get

  if (-not (Test-Path $packagesDir)) {
    New-Item -Path $packagesDir -ItemType Directory | Out-Null
  }

  Write-Host "[2/5] Building Windows release executable..."
  flutter build windows --release --dart-define="API_BASE_URL=$ApiUrl"

  Write-Host "[3/5] Preparing local test certificate..."
  Ensure-LocalTestCertificate

  if (Test-Path $imagesDir) {
    Remove-Item -Recurse -Force $imagesDir
  }

  Write-Host "[4/5] Creating local-test MSIX package..."
  dart run msix:create --build-windows false --output-name "SchoolPlannr-local-test" --publisher "$publisher" --certificate-path "$localPfxPath" --certificate-password "$LocalCertPassword" --install-certificate false --windows-build-args "--dart-define=API_BASE_URL=$ApiUrl"
  Copy-Item (Join-Path $releaseDir "SchoolPlannr-local-test.msix") (Join-Path $packagesDir "SchoolPlannr-local-test.msix") -Force

  if (Test-Path $imagesDir) {
    Remove-Item -Recurse -Force $imagesDir
  }

  Write-Host "[5/5] Creating store MSIX package..."
  dart run msix:create --store --build-windows false --output-name "SchoolPlannr-store" --sign-msix false --install-certificate false --windows-build-args "--dart-define=API_BASE_URL=$ApiUrl"
  Copy-Item (Join-Path $releaseDir "SchoolPlannr-store.msix") (Join-Path $packagesDir "SchoolPlannr-store.msix") -Force

  Write-Host "[6/6] Preparing portable EXE runtime in packages folder..."
  $portableItems = @(
    "SchoolPlannr.exe",
    "flutter_windows.dll",
    "Webview2Loader.dll",
    "data"
  )

  foreach ($item in $portableItems) {
    $target = Join-Path $packagesDir $item
    if (Test-Path $target) {
      Remove-Item -Path $target -Recurse -Force
    }
    Copy-Item -Path (Join-Path $releaseDir $item) -Destination $target -Recurse -Force
  }

  $pluginDlls = Get-ChildItem -Path $releaseDir -Filter "*_plugin.dll" -File
  foreach ($plugin in $pluginDlls) {
    Copy-Item -Path $plugin.FullName -Destination (Join-Path $packagesDir $plugin.Name) -Force
  }

  Write-Host ""
  Write-Host "Artifacts:"
    Get-Item (Join-Path $packagesDir "SchoolPlannr.exe"),
      (Join-Path $packagesDir "flutter_windows.dll"),
      (Join-Path $packagesDir "data"),
      (Join-Path $packagesDir "SchoolPlannr-local-test.msix"),
      (Join-Path $packagesDir "SchoolPlannr-store.msix") |
    Select-Object FullName, Length, LastWriteTime |
    Format-List
} finally {
  Pop-Location
}
