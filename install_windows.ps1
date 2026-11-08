$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13

# System language detection
$sysLang = [System.Globalization.CultureInfo]::CurrentUICulture.TwoLetterISOLanguageName
$isRu = ($sysLang -in @("ru", "be", "uk"))

# Directories
$localApp = if ($env:LOCALAPPDATA) { $env:LOCALAPPDATA } elseif ($env:USERPROFILE) { Join-Path $env:USERPROFILE "AppData\Local" } else { Join-Path $HOME "AppData\Local" }
$InstallDir = Join-Path $localApp "Programs\NeverSearch"
$BinDir = Join-Path $localApp "Programs\Scripts"
$Script = Join-Path $InstallDir "r34_gallery.py"
$CmdPath = Join-Path $BinDir "r34.cmd"
$CmdPathNever = Join-Path $BinDir "never.cmd"

New-Item -ItemType Directory -Force -Path $InstallDir, $BinDir | Out-Null

# Find or auto-install Python
function Get-PythonExecutable {
    # 1. Existing PATH
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source -and (Test-Path $cmd.Source) -and $cmd.Source -notmatch "WindowsApps\\python\.exe") {
        return $cmd.Source
    }
    # 2. py launcher
    $cmd = Get-Command py -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source) {
        $p = & $cmd.Source -3 -c "import sys; print(sys.executable)" 2>$null
        if ($p -and (Test-Path $p.Trim())) { return $p.Trim() }
    }
    # 3. Refresh PATH from registry
    $regUser = [Environment]::GetEnvironmentVariable("Path", "User")
    $regMachine = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $env:PATH = "$regUser;$regMachine;$env:PATH"

    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source -and (Test-Path $cmd.Source) -and $cmd.Source -notmatch "WindowsApps\\python\.exe") {
        return $cmd.Source
    }

    # 4. Search known install locations
    $userProfile = if ($env:USERPROFILE) { $env:USERPROFILE } else { $HOME }
    $dirs = @(
        (Join-Path $localApp "Programs\Python"),
        (Join-Path $userProfile "AppData\Local\Programs\Python"),
        $env:ProgramFiles,
        ${env:ProgramFiles(x86)},
        "C:\Python313", "C:\Python312", "C:\Python311", "C:\Python310"
    )
    foreach ($d in $dirs) {
        if ($d -and (Test-Path $d)) {
            $found = Get-ChildItem -Path $d -Filter "python.exe" -Recurse -Depth 2 -ErrorAction SilentlyContinue |
                     Where-Object { $_.FullName -notmatch "WindowsApps" } |
                     Select-Object -ExpandProperty FullName
            if ($found) {
                $chosen = $found | Sort-Object -Descending | Select-Object -First 1
                if ($chosen -and (Test-Path $chosen)) { return $chosen }
            }
        }
    }
    return $null
}

$Python = Get-PythonExecutable
if (-not $Python) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host (if ($isRu) { "[*] Python не найден. Установка Python 3.11 через winget..." } else { "[*] Python not found. Installing Python 3.11 via winget..." }) -ForegroundColor Yellow
        winget install --id Python.Python.3.11 --exact --silent --accept-package-agreements --accept-source-agreements
        # Refresh PATH
        $regUser = [Environment]::GetEnvironmentVariable("Path", "User")
        $regMachine = [Environment]::GetEnvironmentVariable("Path", "Machine")
        $env:PATH = "$regUser;$regMachine;$env:PATH"
        $Python = Get-PythonExecutable
    }
    if (-not $Python) {
        Write-Host (if ($isRu) { "[*] Загрузка официального установщика Python 3.11..." } else { "[*] Downloading official Python 3.11 installer..." }) -ForegroundColor Yellow
        $pyInst = Join-Path $env:TEMP "python-3.11.9-amd64.exe"
        try {
            (New-Object System.Net.WebClient).DownloadFile("https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe", $pyInst)
            Write-Host (if ($isRu) { "[*] Бесшумная установка Python 3.11..." } else { "[*] Installing Python 3.11 silently..." }) -ForegroundColor Yellow
            Start-Process -FilePath $pyInst -ArgumentList "/quiet", "InstallAllUsers=0", "PrependPath=1", "Include_test=0" -Wait
            Remove-Item -Force $pyInst -ErrorAction SilentlyContinue
        } catch {}
        $regUser = [Environment]::GetEnvironmentVariable("Path", "User")
        $regMachine = [Environment]::GetEnvironmentVariable("Path", "Machine")
        $env:PATH = "$regUser;$regMachine;$env:PATH"
        $Python = Get-PythonExecutable
    }
}

if (-not $Python) {
    Write-Host (if ($isRu) { "[-] Python 3 не найден! Пожалуйста, установите Python 3 (отметьте 'Add Python to PATH') и перезапустите." } else { "[-] Python 3 not found! Please install Python 3 (check 'Add Python to PATH') and re-run installer." }) -ForegroundColor Red
    return
}

# Find or auto-install 7-Zip
function Get-7zExecutable {
    $cmd = Get-Command 7z -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source) { return $cmd.Source }
    $candidates = @(
        (Join-Path $env:ProgramFiles "7-Zip\7z.exe"),
        (Join-Path ${env:ProgramFiles(x86)} "7-Zip\7z.exe"),
        (Join-Path $localApp "Programs\7-Zip\7z.exe"),
        "C:\Program Files\7-Zip\7z.exe",
        "C:\Program Files (x86)\7-Zip\7z.exe"
    )
    foreach ($c in $candidates) {
        if ($c -and (Test-Path $c)) { return $c }
    }
    return $null
}

if (-not (Get-7zExecutable)) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host (if ($isRu) { "[*] Установка 7-Zip через winget..." } else { "[*] Installing 7-Zip via winget..." }) -ForegroundColor Yellow
        winget install --id 7zip.7zip --exact --silent --accept-package-agreements --accept-source-agreements
    }
    if (-not (Get-7zExecutable)) {
        Write-Host (if ($isRu) { "[*] Загрузка 7-Zip с официального сайта..." } else { "[*] Downloading 7-Zip from official site..." }) -ForegroundColor Yellow
        $sevenZipInst = Join-Path $env:TEMP "7z_setup.exe"
        try {
            (New-Object System.Net.WebClient).DownloadFile("https://www.7-zip.org/a/7z2408-x64.exe", $sevenZipInst)
            Start-Process -FilePath $sevenZipInst -ArgumentList "/S" -Wait
            Remove-Item -Force $sevenZipInst -ErrorAction SilentlyContinue
        } catch {}
    }
}

# Install dependencies
Write-Host (if ($isRu) { "[*] Проверка зависимостей Python (requests, prompt_toolkit)..." } else { "[*] Checking Python dependencies (requests, prompt_toolkit)..." }) -ForegroundColor Cyan
& "$Python" -m ensurepip --default-pip 2>$null | Out-Null
& "$Python" -m pip install --upgrade --quiet requests prompt_toolkit

# Download / update NeverSearch
Write-Host (if ($isRu) { "[*] Загрузка актуальной версии NeverSearch..." } else { "[*] Downloading latest NeverSearch..." }) -ForegroundColor Cyan
Invoke-WebRequest "https://raw.githubusercontent.com/vanadeyS/umaZhickR34/main/r34_gallery.py" -OutFile $Script -UseBasicParsing

# Create launchers
$LauncherContent = @"
@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
set PYTHONUTF8=1

set "SCRIPT=$Script"
if not exist "!SCRIPT!" (
    if defined LOCALAPPDATA (
        if exist "%LOCALAPPDATA%\Programs\NeverSearch\r34_gallery.py" set "SCRIPT=%LOCALAPPDATA%\Programs\NeverSearch\r34_gallery.py"
    )
)
if not exist "!SCRIPT!" (
    echo [-] r34_gallery.py not found!
    pause
    exit /b 1
)

if exist "$Python" (
    "$Python" "!SCRIPT!" %*
    exit /b !ERRORLEVEL!
)

where py >nul 2>&1
if !ERRORLEVEL! equ 0 (
    py -3 "!SCRIPT!" %*
    exit /b !ERRORLEVEL!
)

python "!SCRIPT!" %*
exit /b !ERRORLEVEL!
"@

[System.IO.File]::WriteAllText($CmdPath, $LauncherContent, [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText($CmdPathNever, $LauncherContent, [System.Text.UTF8Encoding]::new($false))

# Update User PATH
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if (-not $userPath) { $userPath = "" }
if (($userPath -split ";") -notcontains $BinDir) {
    [Environment]::SetEnvironmentVariable("Path", "$BinDir;$userPath", "User")
}
$env:PATH = "$BinDir;$env:PATH"

function global:r34 {
    param([Parameter(ValueFromRemainingArguments=$true)]$argsList)
    & "$Python" "$Script" @argsList
}
function global:never {
    param([Parameter(ValueFromRemainingArguments=$true)]$argsList)
    & "$Python" "$Script" @argsList
}

Write-Host (if ($isRu) { "`n[+] NeverSearch успешно установлен!" } else { "`n[+] NeverSearch successfully installed!" }) -ForegroundColor Green
Write-Host (if ($isRu) { "[*] Команды 'never' и 'r34' зарегистрированы в системе." } else { "[*] Commands 'never' and 'r34' registered in system." }) -ForegroundColor Gray
Write-Host (if ($isRu) { "[+] Запуск NeverSearch..." } else { "[+] Starting NeverSearch..." }) -ForegroundColor Cyan

& "$Python" "$Script"
