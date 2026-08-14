[CmdletBinding(DefaultParameterSetName = "Committed")]
param(
    [Parameter(ParameterSetName = "Committed")]
    [string]$BaseRef,

    [Parameter(Mandatory, ParameterSetName = "WorkingTree")]
    [switch]$CheckWorkingTree
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$requiredFiles = @(
    "CHANGELOG.md"
    "ASSESSMENT.md"
    "FUTURE-UPGRADES.md"
    "COMPLETED-UPGRADES.md"
)

function Get-DateHeadingMatch {
    param([string]$Content)

    return [regex]::Matches($Content, "(?m)^## (?<date>\d{4}-\d{2}-\d{2})\s*$")
}

function Assert-DescendingDateOrder {
    param(
        [string]$Name,
        [object[]]$DateMatches
    )

    if ($DateMatches.Count -eq 0) {
        throw "$Name must contain at least one dated section."
    }

    $previous = [datetime]::MaxValue
    foreach ($match in $DateMatches) {
        $current = [datetime]::ParseExact($match.Groups["date"].Value, "yyyy-MM-dd", $null)
        if ($current -gt $previous) {
            throw "$Name date sections must be newest first."
        }
        $previous = $current
    }
}

Push-Location $repoRoot
try {
    $rootNames = @(Get-ChildItem -LiteralPath $repoRoot -File | ForEach-Object Name)
    foreach ($requiredFile in $requiredFiles) {
        if (-not ($rootNames -ccontains $requiredFile)) {
            throw "Missing required root file with exact casing: $requiredFile"
        }
    }

    $changelog = Get-Content -Raw -LiteralPath "CHANGELOG.md"
    $changelogDates = Get-DateHeadingMatch $changelog
    Assert-DescendingDateOrder "CHANGELOG.md" $changelogDates
    $firstSectionEnd = if ($changelogDates.Count -gt 1) { $changelogDates[1].Index } else { $changelog.Length }
    $firstSection = $changelog.Substring($changelogDates[0].Index, $firstSectionEnd - $changelogDates[0].Index)
    $entryCount = [regex]::Matches($firstSection, "(?m)^### ").Count
    $summaryCount = [regex]::Matches($firstSection, "(?m)^Summary: ").Count
    $whyCount = [regex]::Matches($firstSection, "(?m)^Why: ").Count
    if ($entryCount -eq 0 -or $entryCount -ne $summaryCount -or $entryCount -ne $whyCount) {
        throw "Every entry in the newest CHANGELOG.md section must include Summary and Why lines."
    }

    $assessment = Get-Content -Raw -LiteralPath "ASSESSMENT.md"
    foreach ($heading in @("## Purpose", "## Current State", "## Build And Dependencies", "## Automation", "## Known Limitations", "## Health")) {
        if (-not $assessment.Contains($heading, [System.StringComparison]::Ordinal)) {
            throw "ASSESSMENT.md is missing $heading."
        }
    }
    $assessmentWordCount = [regex]::Matches($assessment, "\b[\p{L}\p{N}][\p{L}\p{N}'-]*\b").Count
    if ($assessmentWordCount -gt 600) {
        throw "ASSESSMENT.md must remain readable in under a minute. Current word count: $assessmentWordCount"
    }

    $future = Get-Content -Raw -LiteralPath "FUTURE-UPGRADES.md"
    $tierHeadings = @("## Tier 1 (High)", "## Tier 2 (Medium)", "## Tier 3 (Low)")
    $previousIndex = -1
    for ($index = 0; $index -lt $tierHeadings.Count; $index++) {
        $heading = $tierHeadings[$index]
        $headingIndex = $future.IndexOf($heading, [System.StringComparison]::Ordinal)
        if ($headingIndex -le $previousIndex) {
            throw "FUTURE-UPGRADES.md must contain ordered heading: $heading"
        }
        $nextIndex = if ($index -lt $tierHeadings.Count - 1) {
            $future.IndexOf($tierHeadings[$index + 1], [System.StringComparison]::Ordinal)
        } else {
            $future.Length
        }
        $section = $future.Substring($headingIndex, $nextIndex - $headingIndex)
        if ($section -notmatch "(?m)^\* ") {
            throw "$heading must contain at least one upgrade."
        }
        $previousIndex = $headingIndex
    }

    $completed = Get-Content -Raw -LiteralPath "COMPLETED-UPGRADES.md"
    Assert-DescendingDateOrder "COMPLETED-UPGRADES.md" (Get-DateHeadingMatch $completed)

    $changedFiles = @()
    if ($CheckWorkingTree) {
        $changedFiles += @(git diff --name-only HEAD --)
        if ($LASTEXITCODE -ne 0) {
            throw "Unable to inspect tracked working tree changes."
        }
        $changedFiles += @(git diff --cached --name-only HEAD --)
        if ($LASTEXITCODE -ne 0) {
            throw "Unable to inspect staged working tree changes."
        }
        $changedFiles += @(git ls-files --others --exclude-standard)
        if ($LASTEXITCODE -ne 0) {
            throw "Unable to inspect untracked working tree changes."
        }
    } elseif (-not [string]::IsNullOrWhiteSpace($BaseRef)) {
        git rev-parse --verify "${BaseRef}^{commit}" *> $null
        if ($LASTEXITCODE -ne 0) {
            throw "Base reference is not available: $BaseRef"
        }
        $changedFiles += @(git diff --name-only "${BaseRef}...HEAD" --)
        if ($LASTEXITCODE -ne 0) {
            throw "Unable to inspect changes from $BaseRef to HEAD."
        }
    }

    $changedFiles = @($changedFiles | Where-Object { $_ } | Sort-Object -Unique)
    if ($changedFiles.Count -gt 0) {
        foreach ($requiredFile in $requiredFiles) {
            if (-not ($changedFiles -icontains $requiredFile)) {
                throw "Change set must update $requiredFile."
            }
        }
    }
}
finally {
    Pop-Location
}

Write-Output "Project governance validation passed."
