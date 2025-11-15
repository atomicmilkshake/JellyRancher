# Final Media Cleanup Script for RavenMaven
param(
    [string]$ExecutorPath = "V:\RavenMaven\jellyfin_safe_executor.py",
    [switch]$DryRun
)

Write-Host "🎃 Starting Final Media Cleanup - Time to finish the job! 🎃"

# Process each cleaned chunk
$processed = 0
$totalFiles = 0

# First count total operations
for ($chunkNum = 1; $chunkNum -le 9; $chunkNum++) {
    $cleanedFile = "V:\RavenMaven\lists\chunk${chunkNum}_cleaned.json"
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
    $cleanedFile = "V:\RavenMaven\lists\chunk${chunkNum}_cleaned.json"

    if (!(Test-Path $cleanedFile)) {
        Write-Warning "⚠️ Cleaned file not found for chunk $chunkNum, skipping..."
        continue
    }

    Write-Host "`n🔄 Processing chunk $chunkNum (using cleaned results)..."

    # Run Safe Executor with actual moves
    try {
        if ($DryRun) {
            Write-Host "🔍 DRY RUN: Would execute $cleanedFile"
        } else {
            & python $ExecutorPath $cleanedFile
            Write-Host "✅ Safe Executor completed for chunk $chunkNum"
        }
    } catch {
        Write-Warning "⚠️ Safe Executor failed for chunk $chunkNum, skipping..."
    }

    # Count operations in this chunk
    try {
        $content = Get-Content $cleanedFile | ConvertFrom-Json
        $response = $content[0].response
        $oldCount = ($response | Select-String -Pattern "OLD:" -AllMatches).Matches.Count
        $processed += $oldCount
        Write-Host "📊 Progress: $processed / $totalFiles files processed"
    } catch {
        Write-Warning "Could not count operations for chunk $chunkNum"
    }
}

Write-Host "`n🧹 Starting final cleanup of empty directories..."

# Run final cleanup - create a dummy cleanup operation
try {
    # Create a simple cleanup script to remove empty directories
    $cleanupScript = @"
import os
from pathlib import Path

def cleanup_empty_dirs():
    base_path = Path("E:/MOVIES")
    removed = 0
    
    for dirpath in sorted(base_path.rglob('*'), key=lambda x: len(x.parts), reverse=True):
        if dirpath.is_dir():
            try:
                if not any(dirpath.iterdir()):
                    dirpath.rmdir()
                    removed += 1
                    print(f"Removed empty directory: {dirpath}")
            except:
                pass
    
    print(f"Cleanup complete: {removed} empty directories removed")

if __name__ == "__main__":
    cleanup_empty_dirs()
"@

    $cleanupScript | Out-File -FilePath "V:\RavenMaven\cleanup_empty.py" -Encoding UTF8
    & python "V:\RavenMaven\cleanup_empty.py"
    Write-Host "✅ Final cleanup completed"
} catch {
    Write-Warning "⚠️ Final cleanup failed"
}

Write-Host "`n🎃 Final cleanup complete! Check your organized library! 🎃"