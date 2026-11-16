
# PulseIQ Task 16 - Monthly PDF Automation

$ErrorActionPreference = "Stop"

# Move to the project directory
Set-Location $PSScriptRoot

# Create logs folder if it does not exist
New-Item -ItemType Directory -Force -Path ".\logs" | Out-Null

$LogFile = ".\logs\monthly_report_automation.log"

Start-Transcript -Path $LogFile -Append

try {
    Write-Host "Starting PulseIQ monthly report automation..."

    # Start the existing PostgreSQL container
    docker compose start postgres

    if ($LASTEXITCODE -ne 0) {
        throw "Could not start PostgreSQL."
    }

    # Calculate the previous calendar month
    $PreviousMonth = (Get-Date -Day 1).AddMonths(-1).ToString("yyyy-MM")

    Write-Host "Generating report for: $PreviousMonth"

    # Use the project's virtual environment
    $Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

    if (-not (Test-Path $Python)) {
        throw "Project virtual environment Python was not found."
    }

    & $Python ".\build_report.py" --month $PreviousMonth

    if ($LASTEXITCODE -ne 0) {
        throw "PDF report generation failed."
    }

    Write-Host "Monthly PDF report generated successfully."
}
catch {
    Write-Host "Automation failed: $_" -ForegroundColor Red
    exit 1
}
finally {
    Stop-Transcript
}
