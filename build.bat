@echo off
REM Build LaTeX with XeLaTeX, optimized for speed
REM Usage: build.bat [file.tex]
REM Optional: set FAST_BUILD=1 for faster builds with reduced output

setlocal enabledelayedexpansion
set "MAIN=%~1"
if "%MAIN%"=="" set "MAIN=main.tex"

if not exist "%MAIN%" (
    echo Error: file "%MAIN%" not found.
    exit /b 1
)

for %%F in ("%MAIN%") do set "BASENAME=%%~nF"

echo.
echo ================================
echo Building %MAIN%
echo ================================
echo.

REM Check if latexmk is available
where latexmk >nul 2>&1
if not errorlevel 1 (
    echo Using latexmk for automatic pass management...
    if "%FAST_BUILD%"=="1" (
        latexmk -xelatex -quiet "%MAIN%"
    ) else (
        latexmk -xelatex -interaction=nonstopmode "%MAIN%"
    )
    if errorlevel 1 (
        echo.
        echo Error: latexmk build failed. Check %BASENAME%.log
        exit /b 1
    )
    echo.
    echo ================================
    echo Build complete: %BASENAME%.pdf
    echo ================================
    exit /b 0
)

REM Fallback: use XeLaTeX with draft mode for speed
echo latexmk not found. Using XeLaTeX with draft-mode optimization...
echo.

set "INTERACTION=nonstopmode"
if "%FAST_BUILD%"=="1" set "INTERACTION=batchmode"

REM First pass: generate aux files
echo Step 1: XeLaTeX draft pass...
xelatex -draftmode -synctex=1 -interaction=%INTERACTION% -file-line-error "%MAIN%" >nul 2>&1
if errorlevel 1 (
    echo Error: XeLaTeX draft pass failed
    exit /b 1
)

REM Check for biber vs bibtex
if exist "%BASENAME%.bcf" (
    echo Step 2: Running biber...
    biber "%BASENAME%"
    if errorlevel 1 (
        echo Error: biber failed. Check %BASENAME%.blg
        exit /b 1
    )
) else (
    echo Step 2: Running bibtex...
    bibtex "%BASENAME%"
    if errorlevel 1 (
        echo Error: bibtex failed. Check %BASENAME%.blg
        exit /b 1
    )
)

REM Second pass: incorporate bibliography
echo Step 3: XeLaTeX second draft pass...
xelatex -draftmode -synctex=1 -interaction=%INTERACTION% -file-line-error "%MAIN%" >nul 2>&1

REM Final pass: generate PDF
echo Step 4: XeLaTeX final pass with PDF output...
xelatex -synctex=1 -interaction=%INTERACTION% -file-line-error "%MAIN%" >nul 2>&1
if errorlevel 1 (
    echo Warning: XeLaTeX final pass had errors. Check %BASENAME%.log
)

echo.
if exist "%BASENAME%.pdf" (
    echo ================================
    echo Build complete: %BASENAME%.pdf
    echo ================================
    exit /b 0
) else (
    echo Error: PDF not created. Check %BASENAME%.log
    exit /b 1
)