param(
    [Parameter(Position = 0)]
    [string]$InputPath = ".\chap4_core_diagrams.pptx",

    [Parameter(Position = 1)]
    [string]$OutputDir = "",

    [int]$Width = 1600,
    [int]$Height = 900
)

$ErrorActionPreference = "Stop"

function Resolve-AbsolutePath {
    param([string]$PathValue)
    return [System.IO.Path]::GetFullPath((Resolve-Path $PathValue).Path)
}

if (-not (Test-Path $InputPath)) {
    throw "Input file not found: $InputPath"
}

$inputAbs = Resolve-AbsolutePath $InputPath

if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($inputAbs)
    $parentDir = Split-Path $inputAbs -Parent
    $OutputDir = Join-Path $parentDir "${baseName}_images"
}

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

$outputAbs = [System.IO.Path]::GetFullPath($OutputDir)

$powerPoint = $null
$presentation = $null

try {
    $powerPoint = New-Object -ComObject PowerPoint.Application
    $powerPoint.Visible = [Microsoft.Office.Core.MsoTriState]::msoTrue

    $presentation = $powerPoint.Presentations.Open($inputAbs, $false, $false, $false)
    $presentation.Export($outputAbs, "PNG", $Width, $Height)

    Write-Output "Exported slides to: $outputAbs"
}
finally {
    if ($presentation -ne $null) {
        $presentation.Close()
    }
    if ($powerPoint -ne $null) {
        $powerPoint.Quit()
    }
}
