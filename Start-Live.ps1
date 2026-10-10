param([int]$Room = 0, [switch]$Login)
Set-Location $PSScriptRoot
if (!(Test-Path '.venv/Scripts/python.exe')) { py -3 -m venv .venv }
Push-Location bridge
& ../.venv/Scripts/python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { Pop-Location; throw '依赖安装失败' }
Pop-Location
$BridgeArgs = @('bridge/server.py', '--room', "$Room")
if ($Login) { $BridgeArgs += '--login' }
& ./.venv/Scripts/python.exe @BridgeArgs
