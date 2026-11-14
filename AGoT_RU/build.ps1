$ErrorActionPreference = 'Stop'
$project = $PSScriptRoot
$patchRepo = Split-Path $project -Parent
if (!(Test-Path (Join-Path $patchRepo 'generated_files.json'))) {
    $patchRepo = Read-Host 'Full path to AGOT-Russian-Localization'
}
$manifest = Join-Path $patchRepo 'generated_files.json'
if (!(Test-Path $manifest)) { throw 'generated_files.json not found' }
$files = (Get-Content $manifest -Raw | ConvertFrom-Json)
if ($files.Count -eq 0) { throw 'Empty manifest' }
$stage = Join-Path $project '_payload_stage'
if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
New-Item -ItemType Directory -Path $stage | Out-Null
try {
    Copy-Item $manifest (Join-Path $stage 'generated_files.json')
    foreach ($file in $files.GetEnumerator()) {
        if (!$file.StartsWith('AGameOfThronesTheBoardGame_Data/') -or $file.Contains('..') -or $file.Contains('\')) { throw "Invalid path: $file" }
        $source = Join-Path $patchRepo $file
        if (!(Test-Path $source -PathType Leaf)) { throw "Missing: $source" }
        $dest = Join-Path $stage $file
        New-Item -ItemType Directory -Path (Split-Path $dest -Parent) -Force | Out-Null
        Copy-Item $source $dest
    }
    $zip = Join-Path $project 'Payload.zip'
    if (Test-Path $zip) { Remove-Item $zip -Force }
    Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $zip -CompressionLevel Optimal
}
finally { Remove-Item $stage -Recurse -Force -ErrorAction SilentlyContinue }
$xdelta = 'C:\Tools\xdelta3\xdelta3.exe'
if (!(Test-Path $xdelta)) { throw "xdelta3 not found: $xdelta" }
Copy-Item $xdelta (Join-Path $project 'xdelta3.exe') -Force
& dotnet publish (Join-Path $project 'AGoT_RU.csproj') -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true -p:DebugType=None -o (Join-Path $project 'publish')
if ($LASTEXITCODE -ne 0) { throw 'dotnet publish failed' }
Write-Host "SUCCESS: $(Join-Path $project 'publish\AGoT_RU.exe')"
