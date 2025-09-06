#!/usr/bin/env pwsh
# Create a new feature with branch, directory structure, and template
# Usage: .\create-new-feature.ps1 "feature description"
#        .\create-new-feature.ps1 -Json "feature description"

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$FeatureDescription,

    [switch]$Json,

    [switch]$Help
)

if ($Help) {
    Write-Host "Usage: .\create-new-feature.ps1 [-Json] <feature_description>"
    exit 0
}

# Source common functions
. "$PSScriptRoot\common.ps1"

if (-not $FeatureDescription) {
    Write-Error "Usage: .\create-new-feature.ps1 [-Json] <feature_description>"
    exit 1
}

try {
    # Get repository root
    $repoRoot = Get-RepoRoot
    $specsDir = Join-Path $repoRoot "specs"

    # Create specs directory if it doesn't exist
    if (-not (Test-Path $specsDir)) {
        New-Item -ItemType Directory -Path $specsDir -Force | Out-Null
    }

    # Find the highest numbered feature directory
    $highest = 0
    if (Test-Path $specsDir) {
        $existingFeatures = Get-ChildItem $specsDir -Directory | Where-Object { $_.Name -match '^\d{3}-' }
        foreach ($feature in $existingFeatures) {
            $number = [int]($feature.Name.Substring(0, 3))
            if ($number -gt $highest) {
                $highest = $number
            }
        }
    }

    # Generate next feature number
    $featureNum = "{0:D3}" -f ($highest + 1)

    # Create branch name from description
    $words = $FeatureDescription -replace '[^\w\s-]', '' -split '\s+' | Where-Object { $_ -ne '' } | Select-Object -First 3
    $branchSuffix = ($words -join '-').ToLower()
    $branchName = "$featureNum-$branchSuffix"

    # Create and switch to new branch
    git checkout -b $branchName 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create branch '$branchName'"
    }

    # Create feature directory
    $featureDir = Join-Path $specsDir $branchName
    New-Item -ItemType Directory -Path $featureDir -Force | Out-Null

    # Copy template if it exists
    $template = Join-Path $repoRoot "templates" "spec-template.md"
    $specFile = Join-Path $featureDir "spec.md"

    if (Test-Path $template) {
        Copy-Item $template $specFile
    }
    else {
        # Create basic spec file
        $basicSpec = @"
# Feature Specification: $FeatureDescription

## Overview
$FeatureDescription

## Requirements
[To be filled in]

## Acceptance Criteria
[To be filled in]

## Implementation Notes
[To be filled in]
"@
        Set-Content -Path $specFile -Value $basicSpec
    }

    if ($Json) {
        $result = @{
            BRANCH_NAME = $branchName
            SPEC_FILE = $specFile
            FEATURE_NUM = $featureNum
            FEATURE_DIR = $featureDir
        }
        Write-JsonOutput $result
    }
    else {
        Write-Host "Created feature branch: $branchName" -ForegroundColor Green
        Write-Host "Feature directory: $featureDir" -ForegroundColor Cyan
        Write-Host "Spec file: $specFile" -ForegroundColor Cyan
        Write-Host "Feature number: $featureNum" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Yellow
        Write-Host "1. Edit the spec file to define your feature requirements"
        Write-Host "2. Run .\setup-plan.ps1 to create implementation plan"
        Write-Host "3. Use your AI assistant to implement the feature"
    }
}
catch {
    Write-Error "Error creating feature: $($_.Exception.Message)"
    exit 1
}
