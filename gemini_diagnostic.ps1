# Gemini CLI & Code Assist Diagnostic Script
# Tests all reported issues from gemini-piece-of-shit-confirmation.md

Write-Host "=== Gemini CLI & Code Assist Diagnostic ===" -ForegroundColor Cyan
Write-Host ""

# Test 1: Check Gemini CLI Installation
Write-Host "[TEST 1] Checking Gemini CLI Installation..." -ForegroundColor Yellow
try {
    $version = gemini --version 2>&1
    Write-Host "  ✓ Gemini CLI version: $version" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Gemini CLI not found or error: $_" -ForegroundColor Red
}

# Test 2: Check Authentication
Write-Host ""
Write-Host "[TEST 2] Checking Authentication..." -ForegroundColor Yellow
try {
    $auth = gemini auth list 2>&1
    if ($auth -match "cached credentials" -or $auth -match "authenticated") {
        Write-Host "  ✓ Authentication appears valid" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Authentication status unclear: $auth" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ✗ Authentication check failed: $_" -ForegroundColor Red
}

# Test 3: Test Shell Command Execution (the main failure)
Write-Host ""
Write-Host "[TEST 3] Testing Shell Command Execution..." -ForegroundColor Yellow
Write-Host "  Attempting simple PowerShell command via Gemini CLI..." -ForegroundColor Gray

# Create a test file to see if we can interact
$testFile = "gemini_test_temp.txt"
"test content" | Out-File -FilePath $testFile -Encoding utf8

try {
    # Try to get Gemini to read a file (this should work)
    $result = gemini "read the file gemini_test_temp.txt and tell me what it says" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Basic file read command succeeded" -ForegroundColor Green
    } else {
        Write-Host "  ✗ File read command failed" -ForegroundColor Red
        Write-Host "    Error: $result" -ForegroundColor Red
    }
} catch {
    Write-Host "  ✗ Command execution failed: $_" -ForegroundColor Red
}

# Cleanup
Remove-Item $testFile -ErrorAction SilentlyContinue

# Test 4: Check VS Code/Cursor Extensions
Write-Host ""
Write-Host "[TEST 4] Checking VS Code/Cursor Extensions..." -ForegroundColor Yellow
$extensions = @(
    "$env:USERPROFILE\.cursor\extensions\google.geminicodeassist-*",
    "$env:USERPROFILE\.vscode\extensions\google.geminicodeassist-*"
)

foreach ($pattern in $extensions) {
    $found = Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) {
        Write-Host "  ✓ Found extension: $($found.Name)" -ForegroundColor Green
        Write-Host "    Location: $($found.FullName)" -ForegroundColor Gray
    }
}

# Test 5: Check Configuration Files
Write-Host ""
Write-Host "[TEST 5] Checking Configuration Files..." -ForegroundColor Yellow
$configPaths = @(
    "$env:USERPROFILE\.gemini",
    "$env:USERPROFILE\.config\configstore\update-notifier-@google"
)

foreach ($path in $configPaths) {
    if (Test-Path $path) {
        Write-Host "  ✓ Found config directory: $path" -ForegroundColor Green
        $files = Get-ChildItem -Path $path -File -ErrorAction SilentlyContinue
        foreach ($file in $files) {
            Write-Host "    - $($file.Name)" -ForegroundColor Gray
        }
    }
}

# Test 6: Check for Log Files
Write-Host ""
Write-Host "[TEST 6] Checking for Log Files..." -ForegroundColor Yellow
$logPaths = @(
    "$env:USERPROFILE\.gemini\*.log",
    "$env:LOCALAPPDATA\Google\Gemini\*.log",
    "$env:APPDATA\Google\Gemini\*.log"
)

$foundLogs = $false
foreach ($pattern in $logPaths) {
    $logs = Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue
    if ($logs) {
        $foundLogs = $true
        Write-Host "  ✓ Found log files:" -ForegroundColor Green
        foreach ($log in $logs) {
            Write-Host "    - $($log.FullName) ($([math]::Round($log.Length/1KB, 2)) KB)" -ForegroundColor Gray
        }
    }
}

if (-not $foundLogs) {
    Write-Host "  ⚠ No log files found in standard locations" -ForegroundColor Yellow
}

# Test 7: Check Network Connectivity (for web_fetch issues)
Write-Host ""
Write-Host "[TEST 7] Testing Network Connectivity..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://worldclockapi.com/api/json/utc/now" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "  ✓ Network connectivity OK" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Network request returned status: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ✗ Network connectivity test failed: $_" -ForegroundColor Red
}

# Test 8: Check Python Environment (for CLI tool issues)
Write-Host ""
Write-Host "[TEST 8] Checking Python Environment..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ System Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ⚠ Python not found in PATH" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "=== Diagnostic Summary ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Based on the documented issues:" -ForegroundColor White
Write-Host "  1. Shell command execution: 100% failure rate" -ForegroundColor Red
Write-Host "  2. Code editing: Regex stack overflow on large files" -ForegroundColor Red
Write-Host "  3. Network operations: Complete failure" -ForegroundColor Red
Write-Host "  4. File operations: No append mode (only overwrite)" -ForegroundColor Red
Write-Host ""
Write-Host "Recommendations:" -ForegroundColor Yellow
Write-Host "  - Use Cursor's built-in AI (Claude/GPT) instead of Gemini CLI" -ForegroundColor White
Write-Host "  - Check for Gemini CLI updates: npm update -g @google/generative-ai-cli" -ForegroundColor White
Write-Host "  - Report issues to Google: https://github.com/google/generative-ai-cli" -ForegroundColor White
Write-Host ""





