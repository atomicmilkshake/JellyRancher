# Rapid Media Cleanup Script for RavenMaven
param(
    [int]$ChunkSize = 75,
    [switch]$DryRun
)

Write-Host "Starting Rapid Media Cleanup"

# Load configuration
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\")).Path
$configPath = Join-Path $projectRoot "config.json"

if (!(Test-Path $configPath)) {
    Write-Error "config.json not found at $configPath"
    exit 1
}

$config = Get-Content -Path $configPath | ConvertFrom-Json
$ListFile = $config.media_paths.media_list_file
$BatchProcessor = $config.executor_paths.batch_processor
$ExecutorPath = $config.executor_paths.safe_executor
$PromptFile = $config.executor_paths.prompt_file
$outputDir = $config.project_paths.ravenmaven_lists

Write-Host "Processing $ListFile in chunks of $ChunkSize files..."

# Check if list file exists
if (!(Test-Path $ListFile)) {
    Write-Error "List file not found: $ListFile"
    exit 1
}

# Read all lines from the list file
$content = Get-Content $ListFile -Encoding UTF8
$totalFiles = $content.Length
Write-Host "Found $totalFiles files to process"

# Split into chunks
$chunkNum = 1
$chunks = @()

for ($i = 0; $i -lt $content.Length; $i += $ChunkSize) {
    $endIndex = [math]::Min($i + $ChunkSize - 1, $content.Length - 1)
    $chunk = $content[$i..$endIndex]
    $chunkFile = Join-Path $config.project_paths.ravenmaven_root "chunk$chunkNum.txt"
    $chunk | Out-File $chunkFile -Encoding UTF8
    $chunks += $chunkFile
    Write-Host "Created chunk $chunkNum with $($chunk.Length) files"
    $chunkNum++
}

Write-Host "Created $($chunks.Length) chunks. Starting processing..."

# Process each chunk (skip batch processing since already done)
$processed = 0
foreach ($chunkFile in $chunks) {
    $chunkName = [System.IO.Path]::GetFileNameWithoutExtension($chunkFile)
    $outputFile = Join-Path $outputDir "$chunkName`_processed.json"

    Write-Host "`n[INFO] Processing $chunkName (using existing results)..."

    # Skip batch processing - use existing JSON
    if (!(Test-Path $outputFile)) {
        Write-Warning "[SKIP] JSON file not found for $chunkName, skipping..."
        continue
    }

    # Run Safe Executor with actual moves
    $jellyfinDir = $config.media_paths.movies[0]  # Use first configured movie path
    $executorArgs = @($outputFile, "--jellyfin-dir", $jellyfinDir)
    if ($DryRun) {
        $executorArgs += "--dry-run"
    }

    try {
        & python $ExecutorPath @executorArgs
        Write-Host "[OK] Safe Executor completed for $chunkName"
    } catch {
        Write-Warning "[ERROR] Safe Executor failed for $chunkName, skipping..."
    }

    # Accurate progress
    $chunkLines = Get-Content $chunkFile | Measure-Object -Line
    $processed += $chunkLines.Lines
    Write-Host "[INFO] Progress: $processed / $totalFiles files processed"
}

Write-Host "`n[OK] Cleanup complete!"
Write-Host "Check $outputDir for processed results"