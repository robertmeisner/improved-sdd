#!/usr/bin/env pwsh
# Check that all required tools and prerequisites are available for task execution
# Usage: .\check-task-prerequisites.ps1 [-Json]

param(
    [switch]$Json,
    [switch]$Help
)

if ($Help) {
    Write-Host "Usage: .\check-task-prerequisites.ps1 [-Json]"
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
    
    # Check if plan.md exists
    if (-not (Test-Path $paths.IMPL_PLAN)) {
        Write-Error "No implementation plan found at $($paths.IMPL_PLAN)"
        Write-Host "Run .\setup-plan.ps1 first to create the plan."
        exit 1
    }
    
    if ($Json) {
        # Build array of available docs that actually exist
        $docs = @()
        if (Test-Path $paths.RESEARCH) { $docs += "research.md" }
        if (Test-Path $paths.DATA_MODEL) { $docs += "data-model.md" }
        if (Test-Path $paths.CONTRACTS_DIR) {
            $contractFiles = Get-ChildItem $paths.CONTRACTS_DIR -File -ErrorAction SilentlyContinue
            if ($contractFiles.Count -gt 0) { $docs += "contracts/" }
        }
        if (Test-Path $paths.QUICKSTART) { $docs += "quickstart.md" }
        if (Test-Path $paths.REQUIREMENTS) { $docs += "requirements.md" }
        if (Test-Path $paths.DESIGN) { $docs += "design.md" }
        if (Test-Path $paths.FEASIBILITY) { $docs += "feasibility.md" }
        
        $result = @{
            FEATURE_DIR = $paths.FEATURE_DIR
            AVAILABLE_DOCS = $docs
        }
        Write-JsonOutput $result
    }
    else {
        Write-Host "Checking prerequisites for: $($paths.CURRENT_BRANCH)" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "FEATURE_DIR: $($paths.FEATURE_DIR)"
        Write-Host ""
        Write-Host "AVAILABLE_DOCS:" -ForegroundColor Yellow
        
        # Check available design documents
        Test-FileExists $paths.RESEARCH "research.md"
        Test-FileExists $paths.DATA_MODEL "data-model.md"
        Test-DirectoryExists $paths.CONTRACTS_DIR "contracts/"
        Test-FileExists $paths.QUICKSTART "quickstart.md"
        Test-FileExists $paths.REQUIREMENTS "requirements.md"
        Test-FileExists $paths.DESIGN "design.md"
        Test-FileExists $paths.FEASIBILITY "feasibility.md"
        
        Write-Host ""
        Write-Host "Prerequisites check complete." -ForegroundColor Green
    }
}
catch {
    Write-Error "Error checking prerequisites: $($_.Exception.Message)"
    exit 1
}