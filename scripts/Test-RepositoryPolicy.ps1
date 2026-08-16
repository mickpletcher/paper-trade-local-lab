[CmdletBinding()]
param(
    [string]$Repository = $env:GITHUB_REPOSITORY
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($Repository)) {
    throw "Repository is required."
}
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI is required."
}

$requiredChecks = @(
    "lint", "test (3.11)", "test (3.13)", "test (3.14)", "build", "container-validate",
    "mypy (3.11)", "mypy (3.12)", "mypy (3.13)", "mypy (3.14)", "correctness-gates",
    "major-upgrade-canary", "markdown", "links", "validate", "dependency-review", "python-audit",
    "CodeQL", "windows-automation"
)
$actualChecks = @(gh api "repos/$Repository/branches/main/protection/required_status_checks" --jq ".contexts[]")
if ($LASTEXITCODE -ne 0) {
    throw "Unable to read required checks."
}
$missingChecks = @($requiredChecks | Where-Object { $actualChecks -notcontains $_ })
if ($missingChecks.Count -gt 0) {
    throw "Required check drift: $($missingChecks -join ', ')"
}

$workflowFiles = Get-ChildItem -LiteralPath ".github/workflows" -Filter "*.yml" -File
foreach ($workflowFile in $workflowFiles) {
    $content = Get-Content -Raw -LiteralPath $workflowFile.FullName
    $unpinned = [regex]::Matches($content, "(?m)^\s*uses:\s*[^./\s][^@\s]*@(?![0-9a-f]{40}(?:\s|$))[^\s#]+")
    if ($unpinned.Count -gt 0) {
        throw "Unpinned action in $($workflowFile.Name): $($unpinned[0].Value.Trim())"
    }
}

$actionsPolicy = gh api "repos/$Repository/actions/permissions" | ConvertFrom-Json
$permissions = gh api "repos/$Repository/actions/permissions/selected-actions" | ConvertFrom-Json
if (
    $LASTEXITCODE -ne 0 -or
    -not $actionsPolicy.enabled -or
    $actionsPolicy.allowed_actions -ne "selected" -or
    -not $actionsPolicy.sha_pinning_required -or
    -not $permissions.github_owned_allowed -or
    $permissions.verified_allowed
) {
    throw "GitHub Actions allowlist policy drift detected."
}
gh api "repos/$Repository/vulnerability-alerts" *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Dependabot vulnerability alerts are not enabled."
}
gh api "repos/$Repository/automated-security-fixes" *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Dependabot security updates are not enabled."
}
$security = gh api "repos/$Repository" --jq ".security_and_analysis" | ConvertFrom-Json
if (
    $LASTEXITCODE -ne 0 -or
    $security.secret_scanning.status -ne "enabled" -or
    $security.secret_scanning_push_protection.status -ne "enabled" -or
    $security.dependabot_security_updates.status -ne "enabled"
) {
    throw "Repository security feature drift detected."
}

Write-Output "Repository policy validation passed."
