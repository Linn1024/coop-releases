param(
    [string]$RomPath,
    [string]$InstallDirectory,
    [switch]$NonInteractive,
    [switch]$NoShortcuts
)
$ErrorActionPreference = 'Stop'
try {
    if (-not [Environment]::Is64BitOperatingSystem) { throw '64-bit Windows is required.' }
    $package = Split-Path $PSScriptRoot -Parent
    $game = Get-Content -LiteralPath (Join-Path $package 'game.json') -Raw | ConvertFrom-Json
    $payload = Join-Path $package 'payload'
    foreach ($relative in @($game.exe, $game.core, 'source.zip', 'README.md', 'THIRD_PARTY_NOTICES.md', $game.license)) {
        if (-not (Test-Path -LiteralPath (Join-Path $payload $relative) -PathType Leaf)) { throw "Missing package file: $relative. Extract the entire download first." }
    }
    if (-not $RomPath) {
        if ($NonInteractive) { throw 'Specify -RomPath.' }
        Add-Type -AssemblyName System.Windows.Forms
        $picker = New-Object System.Windows.Forms.OpenFileDialog
        $picker.Title = "Select your original $($game.title) USA ROM"
        $picker.Filter = 'Game ROMs (*.nes;*.smc;*.sfc)|*.nes;*.smc;*.sfc|All files (*.*)|*.*'
        try {
            if ($picker.ShowDialog() -ne 'OK') { exit 0 }
            $RomPath = $picker.FileName
        } finally { $picker.Dispose() }
    }
    $RomPath = (Resolve-Path -LiteralPath $RomPath).Path
    if ((Get-FileHash -LiteralPath $RomPath -Algorithm SHA256).Hash -ne $game.sha256) {
        throw 'This is not the supported original USA ROM. Extract compressed ROMs first. See START-HERE.txt for the required checksum.'
    }
    if (-not $InstallDirectory) { $InstallDirectory = Join-Path $env:LOCALAPPDATA ("Programs\" + $game.id) }
    $InstallDirectory = [IO.Path]::GetFullPath($InstallDirectory).TrimEnd('\')
    if ($InstallDirectory.StartsWith($package.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase) -or $InstallDirectory -eq $package) {
        throw 'Choose an installation folder outside the extracted setup folder.'
    }
    $null = New-Item -ItemType Directory -Path $InstallDirectory -Force
    foreach ($file in Get-ChildItem -LiteralPath $payload -Recurse -File) {
        $destination = Join-Path $InstallDirectory $file.FullName.Substring($payload.Length + 1)
        $null = New-Item -ItemType Directory -Path (Split-Path $destination -Parent) -Force
        Copy-Item -LiteralPath $file.FullName -Destination $destination -Force
    }
    $installedRom = Join-Path $InstallDirectory $game.rom
    if ($RomPath -ne $installedRom) { Copy-Item -LiteralPath $RomPath -Destination $installedRom -Force }
    if (-not $NoShortcuts) {
        $shell = New-Object -ComObject WScript.Shell
        foreach ($folder in @([Environment]::GetFolderPath('DesktopDirectory'), [Environment]::GetFolderPath('Programs'))) {
            $shortcut = $shell.CreateShortcut((Join-Path $folder ($game.title + '.lnk')))
            $shortcut.TargetPath = Join-Path $InstallDirectory $game.exe
            $shortcut.WorkingDirectory = $InstallDirectory
            $shortcut.Save()
        }
    }
    Write-Host "Installed $($game.title) to $InstallDirectory"
    if (-not $NonInteractive) {
        Add-Type -AssemblyName System.Windows.Forms
        $null = [System.Windows.Forms.MessageBox]::Show("Installed! Open $($game.title) from your desktop or Start menu.`n`nControls and current prototype limitations: README.md in the game folder.`n`n$InstallDirectory", $game.title)
    }
} catch {
    Write-Host "Installation failed: $($_.Exception.Message)" -ForegroundColor Red
    if (-not $NonInteractive) {
        Add-Type -AssemblyName System.Windows.Forms
        $null = [System.Windows.Forms.MessageBox]::Show($_.Exception.Message, 'Installation failed')
    }
    exit 1
}
