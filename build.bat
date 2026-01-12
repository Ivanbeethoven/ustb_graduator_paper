@echo off
REM build_main.bat - Compile LaTeX main file with XeLaTeX + BibTeX
REM Usage: build_main.bat [main.tex]

set "MAIN=%~1"
if "%MAIN%"=="" set "MAIN=main.tex"

if not exist "%MAIN%" (
    echo Error: file "%MAIN%" not found.
    exit /b 1
)

echo ================================
echo Building "%MAIN%" with XeLaTeX + BibTeX
echo ================================

for %%F in ("%MAIN%") do set "BASENAME=%%~nF"

echo xelatex pass 1...
xelatex -synctex=1 -interaction=nonstopmode -file-line-error "%MAIN%"
if errorlevel 1 (
    echo xelatex pass 1 failed. See "%BASENAME%.log".
    exit /b 1
)

echo bibtex...
bibtex "%BASENAME%"
if errorlevel 1 (
    echo bibtex failed. See "%BASENAME%.blg".
    exit /b 1
)

echo xelatex pass 2...
xelatex -synctex=1 -interaction=nonstopmode -file-line-error "%MAIN%"
if errorlevel 1 (
    echo xelatex pass 2 failed. See "%BASENAME%.log".
    exit /b 1
)

echo xelatex pass 3...
xelatex -synctex=1 -interaction=nonstopmode -file-line-error "%MAIN%"
if errorlevel 1 (
    echo xelatex pass 3 failed. See "%BASENAME%.log".
    exit /b 1
)

echo ================================
if exist "%BASENAME%.pdf" (
    echo Build complete: output "%BASENAME%.pdf"
    echo To clean intermediate files, use latexmk -c if available, or delete .aux/.log files manually.
    exit /b 0
) else (
    echo Build finished but PDF not created. Check "%BASENAME%.log".
    exit /b 1
)