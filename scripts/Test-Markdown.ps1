[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$cliPath = Join-Path $repoRoot "node_modules/markdownlint-cli2/markdownlint-cli2.mjs"
if (-not (Test-Path -LiteralPath $cliPath -PathType Leaf)) {
    throw "Markdownlint is not installed. Run 'npm ci --ignore-scripts' first."
}

$targets = @(
    "*.md"
    "docs/**/*.md"
    "specs/**/*.md"
    "prompts/**/*.md"
    ".github/**/*.md"
)

Push-Location $repoRoot
try {
    & node $cliPath @targets
    $exitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}

if ($exitCode -ne 0) {
    exit $exitCode
}
