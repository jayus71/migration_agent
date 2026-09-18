# Native Microsoft PowerPoint export of the editable I-09 motivation figure.
$ErrorActionPreference = 'Stop'
$figureDir = $PSScriptRoot
$buildDir = Join-Path $env:TEMP 'codex-repair-cases'
New-Item -ItemType Directory -Force -Path $buildDir | Out-Null
$source = Join-Path $buildDir 'repair_cases.pptx'
Copy-Item -LiteralPath (Join-Path $figureDir 'repair_cases.pptx') -Destination $source -Force
$app = New-Object -ComObject PowerPoint.Application
$deck = $app.Presentations.Open($source, $true, $false, $false)
try {
    if ($deck.Slides.Count -ne 1) { throw 'Expected one motivation figure' }
    $pdf = Join-Path $buildDir 'training_repair.pdf'
    $deck.SaveAs($pdf, 32)
    Copy-Item -LiteralPath $pdf -Destination (Join-Path $figureDir 'training_repair.pdf') -Force
    $deck.Slides.Item(1).Export((Join-Path $figureDir 'training_repair.png'), 'PNG', 1650, 589)
} finally {
    $deck.Close()
    $app.Quit()
}
