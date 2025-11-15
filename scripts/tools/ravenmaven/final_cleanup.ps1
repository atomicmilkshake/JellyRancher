# Final Media Cleanup Script for RavenMaven
param(
    [switch]$DryRun
)

Write-Host "Starting Final Media Cleanup - Time to finish the job!"

# Load configuration
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\")).Path
$configPath = Join-Path $projectRoot "config.json"

if (!(Test-Path $configPath)) {
    Write-Error "config.json not found at $configPath"
    exit 1
}

$config = Get-Content -Path $configPath | ConvertFrom-Json
$ExecutorPath = $config.executor_paths.safe_executor
$listDir = $config.project_paths.ravenmaven_lists

# Process each cleaned chunk
$processed = 0
$totalFiles = 0

# First count total operations
for ($chunkNum = 1; $chunkNum -le 9; $chunkNum++) {
    $cleanedFile = Join-Path $listDir "chunk${chunkNum}_cleaned.json"
    if (Test-Path $cleanedFile) {
        try {
            $content = Get-Content $cleanedFile | ConvertFrom-Json
            # Count operations from the response text
            $response = $content[0].response
            $oldCount = ($response | Select-String -Pattern "OLD:" -AllMatches).Matches.Count
            $totalFiles += $oldCount
        } catch {
            Write-Warning "Could not read $cleanedFile"
        }
    }
}

Write-Host "Found $totalFiles total operations to process"

# Process each chunk
for ($chunkNum = 1; $chunkNum -le 9; $chunkNum++) {
    $cleanedFile = Join-Path $listDir "chunk${chunkNum}_cleaned.json"

    if (!(Test-Path $cleanedFile)) {
        Write-Warning "[SKIP] Cleaned file not found for chunk $chunkNum, skipping..."
        continue
    }

    Write-Host "`n[INFO] Processing chunk $chunkNum (using cleaned results)..."

    # Run Safe Executor with actual moves
    try {
        if ($DryRun) {
            Write-Host "[DRY RUN] Would execute $cleanedFile"
        } else {
            & python $ExecutorPath $cleanedFile
            Write-Host "[OK] Safe Executor completed for chunk $chunkNum"
        }
    } catch {
        Write-Warning "[ERROR] Safe Executor failed for chunk $chunkNum, skipping..."
    }

    # Count operations in this chunk
    try {
        $content = Get-Content $cleanedFile | ConvertFrom-Json
        $response = $content[0].response
        $oldCount = ($response | Select-String -Pattern "OLD:" -AllMatches).Matches.Count
        $processed += $oldCount
        Write-Host "[INFO] Progress: $processed / $totalFiles files processed"
    } catch {
        Write-Warning "Could not count operations for chunk $chunkNum"
    }
}

Write-Host "`n[INFO] Starting final cleanup of empty directories..."

# Run final cleanup using standalone script
try {
    $cleanupScriptPath = (Resolve-Path (Join-Path $projectRoot "scripts\tools\cleanup_empty_dirs.py")).Path
    $moviePath = $config.media_paths.movies[0]  # Use first configured movie path

    if (Test-Path $cleanupScriptPath) {
        & python $cleanupScriptPath --path $moviePath
        Write-Host "[OK] Final cleanup completed"
    } else {
        Write-Warning "[ERROR] Cleanup script not found at $cleanupScriptPath"
    }
} catch {
    Write-Warning "[ERROR] Final cleanup failed: $_"
}

Write-Host "`n[OK] Final cleanup complete! Check your organized library!"