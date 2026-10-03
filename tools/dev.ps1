#!/usr/bin/env pwsh
<#
.SYNOPSIS
    一键启停本地开发服务（FastAPI 后端 + Vite 前端）。

.DESCRIPTION
    一条命令同时拉起前后端，日志按来源着色并实时输出；stop 时按记录的 PID
    优雅终止整棵进程树，并校验端口彻底释放。

        pwsh tools/dev.ps1            # 等价于 start
        pwsh tools/dev.ps1 start
        pwsh tools/dev.ps1 stop
        pwsh tools/dev.ps1 restart
        pwsh tools/dev.ps1 status

    前台运行时 Ctrl+C 会停止两个服务（等同 stop）。

.NOTES
    Windows 上 `uv run uvicorn` 是两层进程（uv → python/uvicorn），
    只杀 uv 会留下孤儿 python 占着 8000 端口。因此 stop 分三层：
      1. taskkill /T      优雅终止主进程及其子进程
      2. taskkill /T /F   仍不死则强杀整棵树
      3. 按命令行匹配      兜底清理孤儿（主进程已退出后 /T 找不到子孙）
    第 3 步与 frontend/tests/support/backend.ts 的 killOrphanUvicorn 同思路，
    但要求同时命中多个特征，避免误杀同机其它项目的进程。

    兼容 Windows PowerShell 5.1：Start-Process 的 -Environment 是 7.4+ 才有，
    这里改为在启动前临时写入 $env: 再还原。
#>
[CmdletBinding()]
param(
    [ValidateSet('start', 'stop', 'restart', 'status')]
    [string] $Action = 'start'
)

$ErrorActionPreference = 'Stop'

$RepoRoot    = Split-Path -Parent $PSScriptRoot
$FrontendDir = Join-Path $RepoRoot 'frontend'
$StateDir    = Join-Path $RepoRoot '.dev'
$LogDir      = Join-Path $StateDir 'logs'
$StateFile   = Join-Path $StateDir 'pids.json'

$BackendPort  = 8000
$FrontendPort = 5173

function Write-Task {
    param([string] $Text, [string] $Color = 'Gray')
    Write-Host "[dev] $Text" -ForegroundColor $Color
}

function Write-Source {
    param([string] $Source, [string] $Text, [string] $Color = 'Gray')
    Write-Host "[$Source] $Text" -ForegroundColor $Color
}

# ---------------------------------------------------------------- 状态文件

function Get-State {
    if (-not (Test-Path -LiteralPath $StateFile)) { return $null }
    try {
        return Get-Content -LiteralPath $StateFile -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        # 状态文件损坏时按「无状态」处理，交给端口探测兜底
        return $null
    }
}

function Save-State {
    param([hashtable] $State)
    if (-not (Test-Path -LiteralPath $StateDir)) {
        New-Item -ItemType Directory -Path $StateDir -Force | Out-Null
    }
    Remove-Item -LiteralPath $StateFile -Force -ErrorAction SilentlyContinue
    $State | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $StateFile -Encoding UTF8
}

function Clear-State {
    Remove-Item -LiteralPath $StateFile -Force -ErrorAction SilentlyContinue
}

function Test-ProcessAlive {
    param($ProcessId)
    if ($null -eq $ProcessId) { return $false }
    $parsed = 0
    if (-not [int]::TryParse([string] $ProcessId, [ref] $parsed)) { return $false }
    if ($parsed -le 0) { return $false }
    return $null -ne (Get-Process -Id $parsed -ErrorAction SilentlyContinue)
}

# ---------------------------------------------------------------- 端口探测

function Get-PortOwner {
    param([int] $Port)
    try {
        $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop |
            Select-Object -First 1
        return $conn.OwningProcess
    } catch {
        return $null
    }
}

function Test-PortInUse {
    param([int] $Port)
    return $null -ne (Get-PortOwner -Port $Port)
}

function Wait-PortFree {
    param([int] $Port, [int] $TimeoutSec = 10)
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        if (-not (Test-PortInUse -Port $Port)) { return $true }
        Start-Sleep -Milliseconds 200
    }
    return -not (Test-PortInUse -Port $Port)
}

function Wait-PortListening {
    param([int] $Port, [int] $TimeoutSec = 60)
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        if (Test-PortInUse -Port $Port) { return $true }
        Start-Sleep -Milliseconds 300
    }
    return $false
}

# ---------------------------------------------------------------- 进程终止

function Wait-ProcessGone {
    param([int] $ProcessId, [int] $TimeoutSec = 5)
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        if (-not (Test-ProcessAlive $ProcessId)) { return $true }
        Start-Sleep -Milliseconds 150
    }
    return -not (Test-ProcessAlive $ProcessId)
}

<#
    调用 taskkill.exe。
    脚本级 $ErrorActionPreference = 'Stop' 会把原生命令写到 stderr 的输出
    （如「could not be terminated」）升级成终止性错误，导致 stop 在第一次
    优雅终止失败时就整体中断、再也走不到强杀与兜底清理。这里临时降级。
#>
function Invoke-TaskKill {
    param([int] $ProcessId, [switch] $Force)
    $arguments = @('/PID', $ProcessId, '/T')
    if ($Force) { $arguments += '/F' }
    $saved = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & taskkill.exe @arguments 2>&1 | Out-Null
        return $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $saved
    }
}

function Stop-ProcessTree {
    param([int] $ProcessId, [string] $Name)

    if (-not (Test-ProcessAlive $ProcessId)) {
        Write-Task "$Name 主进程 $ProcessId 已不在运行"
        return
    }

    # 1. 优雅：终止主进程及其子进程
    #    uvicorn / vite 都是无窗口控制台进程，taskkill 不带 /F 只发 WM_CLOSE，
    #    基本收不到，因此这里只等 3s 就升级强杀，不让 stop 拖太久。
    Invoke-TaskKill -ProcessId $ProcessId | Out-Null
    if (Wait-ProcessGone -ProcessId $ProcessId -TimeoutSec 3) {
        Write-Task "$Name 已优雅停止（PID $ProcessId）" 'DarkGray'
        return
    }

    # 2. 强杀整棵树
    Write-Task "$Name 未响应优雅终止，强制结束进程树" 'Yellow'
    Invoke-TaskKill -ProcessId $ProcessId -Force | Out-Null
    Wait-ProcessGone -ProcessId $ProcessId -TimeoutSec 5 | Out-Null
    if (Test-ProcessAlive $ProcessId) {
        Write-Task "$Name 主进程 $ProcessId 强制终止后仍在运行，转由命令行兜底清理" 'Yellow'
    }
}

<#
    按命令行特征兜底清理孤儿进程。
    主进程被强杀后其子孙会被 reparent，此时从已死的 PID 出发 taskkill /T
    找不到它们，于是 python 继续占着 8000 端口。

    $MustMatch 中的每个片段都必须出现，且 $ProcessName 必须精确匹配，
    避免误杀同机其它项目的同名进程。

    枚举与终止都在当前进程内完成：把多行脚本交给 `powershell.exe -Command`
    会被原生命令行的引号规则拆坏而静默不执行。
#>
function Remove-Orphan {
    param(
        [string]   $ProcessName,
        [string[]] $MustMatch,
        [string]   $Label
    )
    $procs = @()
    try {
        $procs = @(Get-CimInstance Win32_Process -Filter "Name='$ProcessName'" -ErrorAction Stop)
    } catch {
        Write-Task "无法枚举 $ProcessName 进程：$($_.Exception.Message)" 'Yellow'
        return
    }
    foreach ($proc in $procs) {
        if ($proc.ProcessId -eq $PID) { continue }
        $line = [string] $proc.CommandLine
        if (-not $line) { continue }
        $matched = $true
        foreach ($fragment in $MustMatch) {
            if ($line -notlike "*$fragment*") { $matched = $false; break }
        }
        if (-not $matched) { continue }
        Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Task "$Label 清理残留进程 $($proc.ProcessId)（$ProcessName）" 'DarkGray'
    }
}

function Invoke-Stop {
    $state = Get-State

    if ($null -eq $state) {
        Write-Task '没有运行记录，仍按端口与命令行做一次兜底清理' 'Yellow'
    } else {
        Stop-ProcessTree -ProcessId ([int] $state.backend.pid)  -Name '后端'
        Stop-ProcessTree -ProcessId ([int] $state.frontend.pid) -Name '前端'
    }

    # 兜底：主进程被强杀后子孙会被 reparent，taskkill /T 从已死的 PID 出发找不到它们
    Remove-Orphan -ProcessName 'python.exe' -MustMatch @('zzz_panel', 'uvicorn') -Label '后端'
    Remove-Orphan -ProcessName 'uv.exe'     -MustMatch @('zzz_panel', 'uvicorn') -Label '后端'
    Remove-Orphan -ProcessName 'node.exe'   -MustMatch @('vite', 'frontend')     -Label '前端'

    $backendFree  = Wait-PortFree -Port $BackendPort  -TimeoutSec 10
    $frontendFree = Wait-PortFree -Port $FrontendPort -TimeoutSec 10

    Clear-State

    if ($backendFree -and $frontendFree) {
        Write-Task "已停止，端口 $BackendPort / $FrontendPort 均已释放" 'Green'
        return 0
    }

    $busy = @()
    if (-not $backendFree)  { $busy += $BackendPort }
    if (-not $frontendFree) { $busy += $FrontendPort }
    Write-Task "端口仍被占用：$($busy -join ', ')。请手动确认占用进程后重试。" 'Red'
    return 1
}

# ---------------------------------------------------------------- 启动

function Resolve-Executable {
    param([string] $Name, [string[]] $WindowsCandidates)
    $isWindows = ($env:OS -eq 'Windows_NT')
    if ($isWindows) {
        foreach ($candidate in $WindowsCandidates) {
            $found = Get-Command $candidate -ErrorAction SilentlyContinue
            if ($found) { return $found.Source }
        }
    }
    $found = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $found) { throw "找不到可执行文件 $Name。请确认已安装并在 PATH 中。" }
    return $found.Source
}

function Start-Service {
    param(
        [string]    $Source,
        [string]    $File,
        [string[]]  $Arguments,
        [string]    $WorkingDir,
        [hashtable] $Env
    )

    # 变量名不能与参数同名：PowerShell 变量大小写不敏感，$logPath 会覆盖 $File
    $stdout = Join-Path $LogDir "$Source.out.log"
    $stderr = Join-Path $LogDir "$Source.err.log"
    foreach ($logPath in @($stdout, $stderr)) {
        Remove-Item -LiteralPath $logPath -Force -ErrorAction SilentlyContinue
        Set-Content -LiteralPath $logPath -Value '' -Encoding UTF8 -NoNewline
    }

    Write-Task "启动 $Source：$File $($Arguments -join ' ')"

    # Start-Process -Environment 需要 PowerShell 7.4+；5.1 上改为临时改 $env:，
    # 子进程会继承，随后立刻还原，不污染当前会话。
    $saved = @{}
    foreach ($key in $Env.Keys) {
        $saved[$key] = [Environment]::GetEnvironmentVariable($key, 'Process')
        [Environment]::SetEnvironmentVariable($key, $Env[$key], 'Process')
    }
    try {
        $process = Start-Process -FilePath $File `
            -ArgumentList $Arguments `
            -WorkingDirectory $WorkingDir `
            -RedirectStandardOutput $stdout `
            -RedirectStandardError $stderr `
            -WindowStyle Hidden `
            -PassThru
    } finally {
        foreach ($key in $saved.Keys) {
            [Environment]::SetEnvironmentVariable($key, $saved[$key], 'Process')
        }
    }

    return [pscustomobject]@{
        Source = $Source
        Pid    = $process.Id
        Stdout = $stdout
        Stderr = $stderr
    }
}

<#
    顺序输出两个日志文件的新增内容，每行加来源前缀与配色。
    PowerShell 没有原生的「同时 tail 两个文件」，这里按字节位点轮询。
#>
function Read-NewLines {
    param([string] $Path, [long] $Offset, [string] $Source, [ConsoleColor] $Color)

    $stream = [System.IO.File]::Open($Path, 'Open', 'Read', 'ReadWrite')
    try {
        [void] $stream.Seek($Offset, 'Begin')
        $reader = New-Object System.IO.StreamReader(
            $stream, [System.Text.UTF8Encoding]::new($false), $true, 4096, $true)
        try {
            $text = $reader.ReadToEnd()
        } finally {
            $reader.Dispose()
        }
        $newOffset = $stream.Position
    } finally {
        $stream.Dispose()
    }

    foreach ($line in ($text -split "`r?`n")) {
        if ($line -ne '') { Write-Source $Source $line $Color }
    }
    return $newOffset
}

function Follow-Logs {
    param([object[]] $Handles)

    $colors = @{ backend = 'Cyan'; frontend = 'Green' }
    $position = @{}
    foreach ($handle in $Handles) {
        $position["$($handle.Source)|out"] = 0
        $position["$($handle.Source)|err"] = 0
    }

    try {
        while ($true) {
            $alive = $false
            foreach ($handle in $Handles) {
                if (Test-ProcessAlive $handle.Pid) { $alive = $true }
                foreach ($kind in @('out', 'err')) {
                    $path = if ($kind -eq 'out') { $handle.Stdout } else { $handle.Stderr }
                    $key = "$($handle.Source)|$kind"
                    if (-not (Test-Path -LiteralPath $path)) { continue }
                    if ((Get-Item -LiteralPath $path).Length -le $position[$key]) { continue }
                    $position[$key] = Read-NewLines -Path $path -Offset $position[$key] `
                        -Source $handle.Source -Color $colors[$handle.Source]
                }
            }
            if (-not $alive) {
                Write-Task '两个进程都已退出，停止跟随日志' 'Yellow'
                break
            }
            Start-Sleep -Milliseconds 200
        }
    } finally {
        Write-Host ''
        Invoke-Stop | Out-Null
    }
}

function Invoke-Start {
    $state = Get-State
    $backendAlive  = ($null -ne $state) -and (Test-ProcessAlive $state.backend.pid)
    $frontendAlive = ($null -ne $state) -and (Test-ProcessAlive $state.frontend.pid)

    if ($backendAlive -and $frontendAlive) {
        Write-Task "服务已在运行（后端 PID $($state.backend.pid)、前端 PID $($state.frontend.pid)）。" 'Yellow'
        Write-Task '查看状态：pwsh tools/dev.ps1 status    停止：pwsh tools/dev.ps1 stop' 'DarkGray'
        return 0
    }

    # 记录与实际不一致（半死不活）时先收拾干净
    if ($null -ne $state) { Invoke-Stop | Out-Null }

    foreach ($port in @($BackendPort, $FrontendPort)) {
        $owner = Get-PortOwner -Port $port
        if ($null -ne $owner) {
            Write-Task "端口 $port 已被 PID $owner 占用，但它不是本脚本启动的服务。" 'Red'
            Write-Task '请先释放该端口，或执行 `pwsh tools/dev.ps1 restart`。' 'Yellow'
            return 1
        }
    }

    if (-not (Test-Path -LiteralPath $LogDir)) {
        New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    }

    $uv  = Resolve-Executable -Name 'uv'  -WindowsCandidates @('uv.exe')
    $npm = Resolve-Executable -Name 'npm' -WindowsCandidates @('npm.cmd', 'npm')

    $backend = Start-Service -Source 'backend' `
        -File $uv `
        -Arguments @('run', 'uvicorn', 'zzz_panel.api.app:app', '--port', "$BackendPort") `
        -WorkingDir $RepoRoot `
        -Env @{ PYTHONIOENCODING = 'utf-8'; PYTHONUTF8 = '1' }

    $frontend = Start-Service -Source 'frontend' `
        -File $npm `
        -Arguments @('run', 'dev') `
        -WorkingDir $FrontendDir `
        -Env @{}

    Save-State -State @{
        backend  = @{ pid = $backend.Pid;  port = $BackendPort }
        frontend = @{ pid = $frontend.Pid; port = $FrontendPort }
    }

    if (-not (Wait-PortListening -Port $BackendPort -TimeoutSec 60)) {
        Write-Task "后端在 60s 内没有监听 $BackendPort，stderr 尾部如下：" 'Red'
        Get-Content -LiteralPath $backend.Stderr -Tail 20 -ErrorAction SilentlyContinue |
            ForEach-Object { Write-Source 'backend' $_ 'DarkGray' }
        Invoke-Stop | Out-Null
        return 1
    }
    if (-not (Wait-PortListening -Port $FrontendPort -TimeoutSec 60)) {
        Write-Task "前端在 60s 内没有监听 $FrontendPort，stdout 尾部如下：" 'Red'
        Get-Content -LiteralPath $frontend.Stdout -Tail 20 -ErrorAction SilentlyContinue |
            ForEach-Object { Write-Source 'frontend' $_ 'DarkGray' }
        Invoke-Stop | Out-Null
        return 1
    }

    Write-Host ''
    Write-Task '两个服务都已就绪：' 'Green'
    Write-Task "  计算器  http://localhost:$FrontendPort/calculator"
    Write-Task "  启动页  http://localhost:$FrontendPort/"
    Write-Task "  指南    http://localhost:$FrontendPort/guide"
    Write-Task "  后端    http://127.0.0.1:$BackendPort/api/health"
    Write-Task "  日志    $LogDir"
    Write-Task '按 Ctrl+C 停止，或另开终端执行 `pwsh tools/dev.ps1 stop`' 'DarkGray'
    Write-Host ''

    Follow-Logs -Handles @($backend, $frontend)
    return 0
}

function Show-Status {
    $state = Get-State
    if ($null -eq $state) {
        Write-Task '没有运行记录。' 'Yellow'
    } else {
        foreach ($name in @('backend', 'frontend')) {
            $entry = $state.$name
            $alive = Test-ProcessAlive $entry.pid
            $mark  = if ($alive) { '运行中' } else { '已退出' }
            $color = if ($alive) { 'Green' } else { 'Red' }
            Write-Task ("{0,-8} PID {1,-7} 端口 {2,-5} {3}" -f $name, $entry.pid, $entry.port, $mark) $color
        }
    }
    foreach ($port in @($BackendPort, $FrontendPort)) {
        $owner = Get-PortOwner -Port $port
        if ($null -eq $owner) {
            Write-Task "端口 $port 空闲" 'DarkGray'
            continue
        }
        # 记录的是 uv / npm 这类包装进程，真正 listen 的是它的子进程，PID 必然不同
        $note = ''
        if ($null -ne $state) {
            foreach ($name in @('backend', 'frontend')) {
                if ([int] $state.$name.port -eq $port -and [int] $state.$name.pid -ne [int] $owner) {
                    $note = "（监听者是 $($state.$name.pid) 的子进程）"
                    break
                }
            }
        }
        if ($note) {
            Write-Task "端口 $port 被 PID $owner 监听 $note" 'Gray'
        } else {
            Write-Task "端口 $port 被 PID $owner 监听" 'Gray'
        }
    }
}

# ---------------------------------------------------------------- 入口

switch ($Action) {
    'start'   { exit (Invoke-Start) }
    'stop'    { exit (Invoke-Stop) }
    'restart' { Invoke-Stop | Out-Null; exit (Invoke-Start) }
    'status'  { Show-Status; exit 0 }
}