#Requires -RunAsAdministrator
<#
.SYNOPSIS
    为 codex_token_summary.py 自动配置 Windows Python 环境

.DESCRIPTION
    1. 检测系统中是否已安装 Python（>=3.9 推荐）
    2. 未安装时从 python.org 下载官方安装包并静默安装
    3. 自动将 Python 加入用户 PATH
    4. 安装 backports.zoneinfo（仅 Python < 3.9 时需要）
    5. 验证环境可用性

.USAGE
    # 直接运行
    .\setup_python_env.ps1

    # 如果策略限制，先执行
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    .\setup_python_env.ps1

.NOTES
    - 需要管理员权限（用于修改系统 PATH 和安装 Python）
    - 默认安装 Python 3.12 64-bit，可通过 $PythonVersion 变量修改
#>

[CmdletBinding()]
param(
    [string]$PythonVersion = "3.12.10",
    [string]$PythonInstallerUrl = "",
    [string]$InstallPath = "$env:LOCALAPPDATA\Programs\Python\Python312",
    [switch]$SkipInstallIfExists = $true
)

# ---------- 工具函数 ----------
function Write-Info { param([string]$msg) Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Success { param([string]$msg) Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Warn { param([string]$msg) Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-ErrorLine { param([string]$msg) Write-Host "[ERROR] $msg" -ForegroundColor Red }

function Test-PythonAvailable {
    try {
        $verStr = & python --version 2>&1
        if ($verStr -match "Python\s+(\d+)\.(\d+)\.(\d+)") {
            return [PSCustomObject]@{
                Available = $true
                Major = [int]$Matches[1]
                Minor = [int]$Matches[2]
                Patch = [int]$Matches[3]
                VersionString = $Matches[0]
            }
        }
    } catch { }
    return [PSCustomObject]@{ Available = $false }
}

function Add-ToUserPath {
    param([string]$NewPath)
    $current = [Environment]::GetEnvironmentVariable("Path", "User")
    $parts = $current -split ';' | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
    if ($parts -contains $NewPath) {
        Write-Info "PATH 已包含: $NewPath"
        return
    }
    $newPathValue = ($parts + $NewPath) -join ';'
    [Environment]::SetEnvironmentVariable("Path", $newPathValue, "User")
    Write-Success "已添加到用户 PATH: $NewPath"
}

function Install-PythonFromOfficial {
    param([string]$Version, [string]$TargetPath)

    $major = ($Version -split '\.')[0]
    $minor = ($Version -split '\.')[1]
    $shortVer = "$major.$minor"

    # 构建下载 URL（64-bit Windows installer）
    if (-not $PythonInstallerUrl) {
        $installerName = "python-$Version-amd64.exe"
        $PythonInstallerUrl = "https://www.python.org/ftp/python/$Version/$installerName"
    } else {
        $installerName = [System.IO.Path]::GetFileName($PythonInstallerUrl)
    }

    $tempDir = [System.IO.Path]::GetTempPath()
    $installerPath = Join-Path $tempDir $installerName

    Write-Info "正在下载 Python $Version..."
    Write-Info "来源: $PythonInstallerUrl"

    try {
        # 使用 BITS 或 Invoke-WebRequest 下载
        if (Get-Command Start-BitsTransfer -ErrorAction SilentlyContinue) {
            Start-BitsTransfer -Source $PythonInstallerUrl -Destination $installerPath -ErrorAction Stop
        } else {
            Invoke-WebRequest -Uri $PythonInstallerUrl -OutFile $installerPath -UseBasicParsing -ErrorAction Stop
        }
    } catch {
        Write-ErrorLine "下载失败: $($_.Exception.Message)"
        Write-Info "请手动下载并安装 Python ${shortVer}: https://www.python.org/downloads/windows/"
        exit 1
    }

    Write-Success "下载完成: $installerPath"

    # 静默安装参数
    # InstallAllUsers=0 表示仅当前用户；PrependPath=1 自动加 PATH；Include_pip=1 包含 pip
    $arguments = @(
        "/quiet"
        "InstallAllUsers=0"
        "PrependPath=1"
        "Include_test=0"
        "Include_doc=0"
        "Include_launcher=1"
        "InstallLauncherAllUsers=0"
        "TargetDir=`"$TargetPath`""
    ) -join ' '

    Write-Info "正在安装 Python（静默模式）..."
    Write-Info "安装目录: $TargetPath"

    $proc = Start-Process -FilePath $installerPath -ArgumentList $arguments -Wait -PassThru
    if ($proc.ExitCode -ne 0) {
        Write-ErrorLine "Python 安装失败，退出码: $($proc.ExitCode)"
        exit 1
    }

    Write-Success "Python $Version 安装完成"

    # 清理安装包
    Remove-Item $installerPath -ErrorAction SilentlyContinue
}

# ---------- 主流程 ----------
Write-Info "开始初始化 Python 环境（用于 codex_token_summary.py）"

# 1. 检测现有 Python
$py = Test-PythonAvailable
if ($py.Available) {
    Write-Info "检测到已安装 Python: $($py.VersionString)"
    if ($py.Major -ge 3 -and $py.Minor -ge 9) {
        Write-Success "Python 版本满足要求 (>=3.9)"
        $skipInstall = $true
    } else {
        Write-Warn "Python 版本较低 ($($py.VersionString))，建议升级到 3.9+ 以获得最佳兼容性"
        if ($SkipInstallIfExists) {
            $skipInstall = $true
        } else {
            $skipInstall = $false
        }
    }
} else {
    Write-Info "未检测到 Python，将执行自动安装"
    $skipInstall = $false
}

# 2. 安装 Python（如需要）
if (-not $skipInstall) {
    Install-PythonFromOfficial -Version $PythonVersion -TargetPath $InstallPath

    # 手动确保 PATH 包含新安装的 Python（有时候安装器不会立即生效）
    $pythonExe = Join-Path $InstallPath "python.exe"
    $scriptsPath = Join-Path $InstallPath "Scripts"

    if (Test-Path $pythonExe) {
        Add-ToUserPath -NewPath $InstallPath
        Add-ToUserPath -NewPath $scriptsPath
    } else {
        Write-Warn "未找到预期的 python.exe: $pythonExe"
    }

    # 刷新当前会话的环境变量
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "User") + ";" +
                [Environment]::GetEnvironmentVariable("Path", "Machine")

    # 重新检测
    $py = Test-PythonAvailable
    if (-not $py.Available) {
        Write-ErrorLine "安装后仍无法找到 python 命令，请尝试重新打开 PowerShell 窗口再试"
        exit 1
    }
    Write-Success "Python 安装验证通过: $($py.VersionString)"
} else {
    Write-Info "跳过 Python 安装"
}

# 3. 安装额外依赖（仅 Python < 3.9 需要 backports.zoneinfo）
if ($py.Major -eq 3 -and $py.Minor -lt 9) {
    Write-Info "Python < 3.9，安装 backports.zoneinfo..."
    try {
        & python -m pip install backports.zoneinfo --quiet
        Write-Success "backports.zoneinfo 安装完成"
    } catch {
        Write-Warn "pip 安装失败: $($_.Exception.Message)"
        Write-Info "可手动运行: python -m pip install backports.zoneinfo"
    }
} else {
    Write-Info "Python >= 3.9，zoneinfo 为标准库，无需额外安装"
}

# 4. 验证脚本可运行
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$scriptPath = Join-Path $scriptDir "codex_token_summary.py"

if (Test-Path $scriptPath) {
    Write-Info "验证 codex_token_summary.py 可执行性..."
    try {
        $output = & python $scriptPath --help 2>&1
        if ($output -match "usage.*codex_token_summary.py") {
            Write-Success "脚本验证通过！"
        } else {
            Write-Warn "脚本运行异常，输出: $output"
        }
    } catch {
        Write-Warn "运行脚本时出错: $($_.Exception.Message)"
    }
} else {
    Write-Warn "未找到 codex_token_summary.py（应在同目录），请确认路径: $scriptPath"
}

# 5. 提示用户
Write-Host ""
Write-Success "Python 环境初始化完成！"
Write-Host ""
Write-Host "后续可直接运行:" -ForegroundColor Cyan
Write-Host "  python codex_token_summary.py --days 7" -ForegroundColor White
Write-Host ""
Write-Host "如果命令未识别，请重新打开 PowerShell 窗口以加载新的 PATH 设置。" -ForegroundColor Gray
