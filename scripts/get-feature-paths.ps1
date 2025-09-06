#!/usr/bin/env pwsh
# Get paths for current feature branch without creating anything
# Used by commands that need to find existing feature files
# Usage: .\get-feature-paths.ps1

param(
    [switch]$Help
)

if ($Help) {
    Write-Host "Usage: .\get-feature-paths.ps1"
    exit 0
}

# Source common functions
. "$PSScriptRoot\common.ps1"

try {
    # Get all paths
    $paths = Get-FeaturePaths
    
    # Check if on feature branch
    if (-not (Test-FeatureBranch $paths.CURRENT_BRANCH)) {
        exit 1
    }
    
    # Output paths (don't create anything)
    Write-Host "REPO_ROOT: $($paths.REPO_ROOT)"
    Write-Host "BRANCH: $($paths.CURRENT_BRANCH)"
    Write-Host "FEATURE_DIR: $($paths.FEATURE_DIR)"
    Write-Host "FEATURE_SPEC: $($paths.FEATURE_SPEC)"
    Write-Host "IMPL_PLAN: $($paths.IMPL_PLAN)"
    Write-Host "TASKS: $($paths.TASKS)"
    Write-Host "REQUIREMENTS: $($paths.REQUIREMENTS)"
    Write-Host "DESIGN: $($paths.DESIGN)"
    Write-Host "FEASIBILITY: $($paths.FEASIBILITY)"
}
catch {
    Write-Error "Error getting feature paths: $($_.Exception.Message)"
    exit 1
}