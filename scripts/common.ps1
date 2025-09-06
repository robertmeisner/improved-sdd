# Common PowerShell functions for improved-sdd scripts
# Source this file in other scripts using: . "$PSScriptRoot\common.ps1"

function Get-RepoRoot {
    try {
        $repoRoot = git rev-parse --show-toplevel 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $repoRoot
        }
    }
    catch {}
    
    # Fallback: look for .git directory
    $current = Get-Location
    while ($current -ne $current.Root) {
        if (Test-Path (Join-Path $current ".git")) {
            return $current.Path
        }
        $current = $current.Parent
    }
    
    throw "Not in a git repository"
}

function Get-CurrentBranch {
    try {
        $branch = git rev-parse --abbrev-ref HEAD 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $branch
        }
    }
    catch {}
    
    throw "Cannot determine current branch"
}

function Get-FeatureDir {
    param(
        [string]$RepoRoot,
        [string]$CurrentBranch
    )
    
    return Join-Path $RepoRoot "specs" $CurrentBranch
}

function Get-FeaturePaths {
    $repoRoot = Get-RepoRoot
    $currentBranch = Get-CurrentBranch
    $featureDir = Get-FeatureDir $repoRoot $currentBranch
    
    return @{
        REPO_ROOT = $repoRoot
        CURRENT_BRANCH = $currentBranch
        FEATURE_DIR = $featureDir
        FEATURE_SPEC = Join-Path $featureDir "spec.md"
        IMPL_PLAN = Join-Path $featureDir "plan.md"
        TASKS = Join-Path $featureDir "tasks.md"
        RESEARCH = Join-Path $featureDir "research.md"
        DATA_MODEL = Join-Path $featureDir "data-model.md"
        QUICKSTART = Join-Path $featureDir "quickstart.md"
        CONTRACTS_DIR = Join-Path $featureDir "contracts"
        FEASIBILITY = Join-Path $featureDir "feasibility.md"
        REQUIREMENTS = Join-Path $featureDir "requirements.md"
        DESIGN = Join-Path $featureDir "design.md"
        RETROSPECTIVE = Join-Path $featureDir "retrospective.md"
    }
}

function Test-FeatureBranch {
    param([string]$BranchName)
    
    if ($BranchName -eq "main" -or $BranchName -eq "master") {
        Write-Error "Cannot work on feature specs from main/master branch"
        return $false
    }
    
    if (-not ($BranchName -match '^\d{3}-')) {
        Write-Error "Feature branch must start with 3-digit number (e.g., 001-feature-name)"
        return $false
    }
    
    return $true
}

function Test-FileExists {
    param(
        [string]$FilePath,
        [string]$Description
    )
    
    if (Test-Path $FilePath) {
        Write-Host "  ✓ $Description" -ForegroundColor Green
        return $true
    }
    else {
        Write-Host "  ✗ $Description" -ForegroundColor Red
        return $false
    }
}

function Test-DirectoryExists {
    param(
        [string]$DirPath,
        [string]$Description
    )
    
    if (Test-Path $DirPath -PathType Container) {
        $count = (Get-ChildItem $DirPath -File).Count
        if ($count -gt 0) {
            Write-Host "  ✓ $Description ($count files)" -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "  ✗ $Description (empty)" -ForegroundColor Yellow
            return $false
        }
    }
    else {
        Write-Host "  ✗ $Description" -ForegroundColor Red
        return $false
    }
}

function Write-JsonOutput {
    param([hashtable]$Data)
    
    $jsonData = @{}
    foreach ($key in $Data.Keys) {
        $jsonData[$key] = $Data[$key]
    }
    
    ConvertTo-Json $jsonData -Compress
}

function Show-Banner {
    param([string]$Title)
    
    Write-Host ""
    Write-Host "╔══════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║           IMPROVED-SDD               ║" -ForegroundColor Cyan
    Write-Host "║    Spec-Driven Development           ║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    if ($Title) {
        Write-Host $Title -ForegroundColor Yellow
        Write-Host ""
    }
}

# Export functions for use in other scripts
Export-ModuleMember -Function *