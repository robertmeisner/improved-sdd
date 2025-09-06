#!/usr/bin/env pwsh
# Setup implementation plan structure for current branch
# Returns paths needed for implementation plan generation
# Usage: .\setup-plan.ps1 [-Json]

param(
    [switch]$Json,
    [switch]$Help
)

if ($Help) {
    Write-Host "Usage: .\setup-plan.ps1 [-Json]"
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
    
    # Create specs directory if it doesn't exist
    if (-not (Test-Path $paths.FEATURE_DIR)) {
        New-Item -ItemType Directory -Path $paths.FEATURE_DIR -Force | Out-Null
    }
    
    # Copy plan template if it exists
    $template = Join-Path $paths.REPO_ROOT "templates" "plan-template.md"
    if (Test-Path $template) {
        Copy-Item $template $paths.IMPL_PLAN -Force
    }
    else {
        # Create basic plan template
        $basicPlan = @"
# Implementation Plan: [FEATURE]

## Overview
[Feature description and goals]

## Technical Approach
[High-level technical approach]

## Implementation Steps
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Dependencies
[Any dependencies or prerequisites]

## Testing Strategy
[How the feature will be tested]

## Rollback Plan
[How to rollback if needed]
"@
        Set-Content -Path $paths.IMPL_PLAN -Value $basicPlan
    }
    
    if ($Json) {
        $result = @{
            FEATURE_SPEC = $paths.FEATURE_SPEC
            IMPL_PLAN = $paths.IMPL_PLAN
            SPECS_DIR = $paths.FEATURE_DIR
            BRANCH = $paths.CURRENT_BRANCH
        }
        Write-JsonOutput $result
    }
    else {
        Write-Host "Setup complete for branch: $($paths.CURRENT_BRANCH)" -ForegroundColor Green
        Write-Host ""
        Write-Host "Paths:" -ForegroundColor Yellow
        Write-Host "FEATURE_SPEC: $($paths.FEATURE_SPEC)"
        Write-Host "IMPL_PLAN: $($paths.IMPL_PLAN)"
        Write-Host "SPECS_DIR: $($paths.FEATURE_DIR)"
        Write-Host "BRANCH: $($paths.CURRENT_BRANCH)"
    }
}
catch {
    Write-Error "Error setting up plan: $($_.Exception.Message)"
    exit 1
}