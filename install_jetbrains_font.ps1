# Install JetBrains Mono Font and Configure Cursor
# This script downloads JetBrains Mono, installs it, and configures Cursor to use it

Write-Host "Installing JetBrains Mono font and configuring Cursor..." -ForegroundColor Cyan

# Step 1: Download JetBrains Mono
$downloadUrl = "https://github.com/JetBrains/JetBrainsMono/releases/download/v2.304/JetBrainsMono-2.304.zip"
$downloadPath = "$env:TEMP\JetBrainsMono.zip"
$extractPath = "$env:TEMP\JetBrainsMono"

Write-Host "Downloading JetBrains Mono from GitHub..." -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri $downloadUrl -OutFile $downloadPath -UseBasicParsing
    Write-Host "Download complete!" -ForegroundColor Green
} catch {
    Write-Host "Error downloading font: $_" -ForegroundColor Red
    exit 1
}

# Step 2: Extract the font files
Write-Host "Extracting font files..." -ForegroundColor Yellow
try {
    Expand-Archive -Path $downloadPath -DestinationPath $extractPath -Force
    Write-Host "Extraction complete!" -ForegroundColor Green
} catch {
    Write-Host "Error extracting font: $_" -ForegroundColor Red
    exit 1
}

# Step 3: Find all .ttf font files
$fontFiles = Get-ChildItem -Path $extractPath -Recurse -Filter "*.ttf" | Where-Object { $_.Name -like "*Regular*" -or $_.Name -like "*Bold*" -or $_.Name -like "*Italic*" }

if ($fontFiles.Count -eq 0) {
    Write-Host "No font files found in the extracted archive!" -ForegroundColor Red
    exit 1
}

# Step 4: Install fonts
Write-Host "Installing fonts to system..." -ForegroundColor Yellow
$fontsInstalled = 0
foreach ($fontFile in $fontFiles) {
    try {
        $fontName = $fontFile.Name
        $destination = "$env:LOCALAPPDATA\Microsoft\Windows\Fonts\$fontName"
        
        # Copy font to Fonts directory
        Copy-Item -Path $fontFile.FullName -Destination $destination -Force
        
        # Register font in registry (for current user)
        $regPath = "HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts"
        $regName = $fontName -replace '\.ttf$', ' (TrueType)'
        New-ItemProperty -Path $regPath -Name $regName -Value $fontName -PropertyType String -Force | Out-Null
        
        $fontsInstalled++
        Write-Host "  Installed: $fontName" -ForegroundColor Gray
    } catch {
        Write-Host "  Warning: Could not install $($fontFile.Name): $_" -ForegroundColor Yellow
    }
}

Write-Host "Installed $fontsInstalled font files!" -ForegroundColor Green

# Step 5: Configure Cursor settings
Write-Host "Configuring Cursor settings..." -ForegroundColor Yellow

# Get Cursor settings path
$cursorSettingsPath = "$env:APPDATA\Cursor\User\settings.json"
$workspaceSettingsPath = "$PSScriptRoot\.vscode\settings.json"

# Create workspace .vscode directory if it doesn't exist
$workspaceVscodeDir = "$PSScriptRoot\.vscode"
if (-not (Test-Path $workspaceVscodeDir)) {
    New-Item -ItemType Directory -Path $workspaceVscodeDir -Force | Out-Null
}

# Function to update settings.json
function Update-SettingsFile {
    param(
        [string]$SettingsPath,
        [string]$Description
    )
    
    if (-not (Test-Path $SettingsPath)) {
        # Create new settings file
        $settings = @{
            "editor.fontFamily" = "'JetBrains Mono', 'Courier New', monospace"
            "editor.fontSize" = 14
            "editor.fontLigatures" = true
            "editor.fontWeight" = "400"
            "terminal.integrated.fontFamily" = "'JetBrains Mono', 'Courier New', monospace"
            "terminal.integrated.fontSize" = 14
            "editor.lineHeight" = 1.5
        }
        $settings | ConvertTo-Json -Depth 10 | Set-Content -Path $SettingsPath -Encoding UTF8
        Write-Host "  Created new $Description settings file" -ForegroundColor Green
    } else {
        # Update existing settings file
        try {
            $content = Get-Content -Path $SettingsPath -Raw -Encoding UTF8 | ConvertFrom-Json
            
            # Update font settings
            $content | Add-Member -MemberType NoteProperty -Name "editor.fontFamily" -Value "'JetBrains Mono', 'Courier New', monospace" -Force
            $content | Add-Member -MemberType NoteProperty -Name "editor.fontSize" -Value 14 -Force
            $content | Add-Member -MemberType NoteProperty -Name "editor.fontLigatures" -Value $true -Force
            $content | Add-Member -MemberType NoteProperty -Name "editor.fontWeight" -Value "400" -Force
            $content | Add-Member -MemberType NoteProperty -Name "terminal.integrated.fontFamily" -Value "'JetBrains Mono', 'Courier New', monospace" -Force
            $content | Add-Member -MemberType NoteProperty -Name "terminal.integrated.fontSize" -Value 14 -Force
            $content | Add-Member -MemberType NoteProperty -Name "editor.lineHeight" -Value 1.5 -Force
            
            $content | ConvertTo-Json -Depth 10 | Set-Content -Path $SettingsPath -Encoding UTF8
            Write-Host "  Updated $Description settings file" -ForegroundColor Green
        } catch {
            Write-Host "  Warning: Could not update $Description settings: $_" -ForegroundColor Yellow
            Write-Host "  You may need to manually add font settings to: $SettingsPath" -ForegroundColor Yellow
        }
    }
}

# Update both user and workspace settings
Update-SettingsFile -SettingsPath $cursorSettingsPath -Description "Cursor user"
Update-SettingsFile -SettingsPath $workspaceSettingsPath -Description "workspace"

# Cleanup
Write-Host "Cleaning up temporary files..." -ForegroundColor Yellow
Remove-Item -Path $downloadPath -Force -ErrorAction SilentlyContinue
Remove-Item -Path $extractPath -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "JetBrains Mono has been installed and Cursor has been configured." -ForegroundColor White
Write-Host "Please restart Cursor for the changes to take effect." -ForegroundColor Yellow
Write-Host ""
Write-Host "Settings configured:" -ForegroundColor White
Write-Host "  - Editor font: JetBrains Mono" -ForegroundColor Gray
Write-Host "  - Terminal font: JetBrains Mono" -ForegroundColor Gray
Write-Host "  - Font ligatures: Enabled" -ForegroundColor Gray
Write-Host "  - Font size: 14" -ForegroundColor Gray
Write-Host ""
























