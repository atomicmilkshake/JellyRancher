# Load OPENAI-related environment variables from the system/user scopes into the current PowerShell session.
# Usage (dot-source so variables are set in your current session):
# . .\scripts\load_system_env.ps1
# After dot-sourcing, $env:OPENAI_API_KEY and $env:OPENAI_BASE_URL will be available in this session (if set in system/user vars).

function Get-EnvMulti {
    param(
        [string]$name
    )
    # Try Process, then User, then Machine (System)
    $val = [System.Environment]::GetEnvironmentVariable($name, 'Process')
    if ([string]::IsNullOrEmpty($val)) {
        $val = [System.Environment]::GetEnvironmentVariable($name, 'User')
    }
    if ([string]::IsNullOrEmpty($val)) {
        $val = [System.Environment]::GetEnvironmentVariable($name, 'Machine')
    }
    return $val
}

$base = Get-EnvMulti -name 'OPENAI_BASE_URL'
$key  = Get-EnvMulti -name 'OPENAI_API_KEY'

if ($base) {
    $env:OPENAI_BASE_URL = $base
}
if ($key) {
    $env:OPENAI_API_KEY = $key
}

# Print presence and masked length only (do not leak secrets)
if ($env:OPENAI_BASE_URL) {
    Write-Output "OPENAI_BASE_URL set in session: True ; length: $($env:OPENAI_BASE_URL.Length)"
} else {
    Write-Output "OPENAI_BASE_URL set in session: False"
}

if ($env:OPENAI_API_KEY) {
    Write-Output "OPENAI_API_KEY set in session: True ; length: $($env:OPENAI_API_KEY.Length)"
} else {
    Write-Output "OPENAI_API_KEY set in session: False"
}

# Helpful note
# Print a friendly instruction; compute script path then print a single-line suggestion
$scriptPath = Join-Path -Path $PSScriptRoot -ChildPath 'scripts\load_system_env.ps1'
Write-Output "To make this automatic in future terminals, dot-source this script in your profile. Example to add to your profile (one line):"
Write-Output ". '$scriptPath'"
