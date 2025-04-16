<#
.SYNOPSIS
  PowerUp-Lite - Privilege Escalation Checker for Windows Lab Environments

.DESCRIPTION
  Scans for common privilege escalation vectors: weak service permissions, 
  unquoted service paths, modifiable PATHs, AlwaysInstallElevated settings, 
  token privileges, DLL hijacking paths, and weak scheduled tasks.

.NOTICE
  *************************
  *                       *  
  *  For lab use only.    *
  *  Use with consent.    *
  *  Unauthorized use     *
  *  is prohibited.       *
  *                       *
  *************************
#>

param(
    [switch]$Verbose
)

function Write-VerboseLog {
    param([string]$Message)
    if ($Verbose) {
        Write-Host $Message
    }
}

$RunID = [guid]::NewGuid().ToString()
$Results = @()
$LogPath = "$env:TEMP\powerup-lite-$RunID.txt"

Write-Host "`n[+] PowerUp-Lite v1.1" -ForegroundColor Cyan
Write-Host "[+] Run ID: $RunID"
Write-Host "[+] Host: $env:COMPUTERNAME" -ForegroundColor Cyan

function Get-UnquotedServicePaths {
    Write-VerboseLog "`n[>] Checking for unquoted service paths..."
    Get-CimInstance -ClassName Win32_Service | Where-Object {
        ($_.PathName -match " ") -and ($_.PathName -notmatch "`"")
    } | ForEach-Object {
        $result = "[!] Unquoted Path: $($_.Name) - $($_.PathName)"
        $Results += $result
    }
}

function Get-ModifiableServiceBins {
    Write-VerboseLog "`n[>] Checking for services with modifiable binaries..."
    Get-CimInstance -ClassName Win32_Service | ForEach-Object {
        $bin = ($_).PathName -split ' ')[0].Trim('"')
        if (Test-Path $bin) {
            $acl = Get-Acl $bin
            if ($acl.AccessToString -match "Everyone Allow.*Write") {
                $Results += "[!] Writable Service Binary: $($_.Name) - $bin"
            }
        }
    }
}

function Get-WeakPathPermissions {
    Write-VerboseLog "`n[>] Checking modifiable folders in PATH..."
    $env:Path.Split(';') | ForEach-Object {
        if (Test-Path $_) {
            $acl = Get-Acl $_
            if ($acl.AccessToString -match "Everyone Allow.*(Write|FullControl)") {
                $Results += "[!] Writable PATH Folder: $_"
            }
        }
    }
}

function Check-AlwaysInstallElevated {
    Write-VerboseLog "`n[>] Checking AlwaysInstallElevated registry keys..."
    $hkcu = Get-ItemProperty -Path "HKCU:\Software\Policies\Microsoft\Windows\Installer" -ErrorAction SilentlyContinue
    $hklm = Get-ItemProperty -Path "HKLM:\Software\Policies\Microsoft\Windows\Installer" -ErrorAction SilentlyContinue
    if (($hkcu.AlwaysInstallElevated -eq 1) -and ($hklm.AlwaysInstallElevated -eq 1)) {
        $Results += "[!] AlwaysInstallElevated is ENABLED!"
    } else {
        $Results += "[+] AlwaysInstallElevated is safe or not configured."
    }
}

function Check-TokenPrivileges {
    Write-VerboseLog "`n[>] Checking token privileges..."
    $tokenPrivs = whoami /priv
    $tokenPrivs | ForEach-Object {
        if ($_ -match "Enabled") {
            $Results += "[!] Enabled Privilege: $_"
        }
    }
}

function Find-PotentialDLLHijackPaths {
    Write-VerboseLog "`n[>] Looking for potential DLL hijack locations..."
    $env:Path.Split(';') | ForEach-Object {
        if ((Test-Path $_) -and (Get-Acl $_).AccessToString -match "Everyone Allow.*(Write|FullControl)") {
            $Results += "[!] Possible DLL hijack path: $_"
        }
    }
}

function Get-WeakScheduledTasks {
    Write-VerboseLog "`n[>] Checking scheduled tasks..."
    try {
        Get-ScheduledTask | ForEach-Object {
            $actions = $_.Actions | Where-Object { $_.Execute -and $_.Execute -notmatch '^%SystemRoot%' }
            foreach ($act in $actions) {
                $Results += "[!] Task: $($_.TaskName) - Potentially modifiable action: $($act.Execute)"
            }
        }
    } catch {
        $Results += "[x] Could not retrieve scheduled tasks. Possibly due to permissions."
    }
}

# === Execute Checks ===
Get-UnquotedServicePaths
Get-ModifiableServiceBins
Get-WeakPathPermissions
Check-AlwaysInstallElevated
Check-TokenPrivileges
Find-PotentialDLLHijackPaths
Get-WeakScheduledTasks

# === Output Summary ===
Write-Host "`n[+] Summary of Findings:" -ForegroundColor Yellow
$Results | ForEach-Object {
    if ($_ -match "Writable|Unquoted|Enabled|Hijack|Privilege|Task") {
        Write-Host $_ -ForegroundColor Red
    } else {
        Write-Host $_
    }
}

# === Save to File ===
$Results | Out-File -FilePath $LogPath -Encoding ASCII -Force
attrib +h $LogPath

Write-Host "`n[+] Results saved to: $LogPath" -ForegroundColor Green
Write-Host "[+] Done. Review findings carefully." -ForegroundColor Green
