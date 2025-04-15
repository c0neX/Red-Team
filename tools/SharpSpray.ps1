<#
.SYNOPSIS
  PowerUp-Lite - Privilege Escalation Checker for Windows Lab Environments

.DESCRIPTION
  Scans for common privilege escalation paths: weak service permissions, 
  unquoted service paths, modifiable PATHs, and AlwaysInstallElevated settings.

.NOTICE
  *************************
  *                                                                     *
  *  This tool is intended for legal use only.                          *
  *  Use it exclusively in authorized penetration tests, CTFs, or       *
  *  controlled lab environments.                                       *
  *                                                                     *
  *  Unauthorized or malicious use is strictly prohibited and may      *
  *  result in criminal or civil penalties.                            *
  *                                                                     *
  *  Use responsibly and with written permission.                      *
  *                                                                     *
  *************************
#>

Write-Host "`n[+] Running PowerUp-Lite..." -ForegroundColor Cyan

function Get-UnquotedServicePaths {
    Write-Host "`n[+] Checking for unquoted service paths..."
    Get-WmiObject win32_service | Where-Object {
        ($_.pathname -match " ") -and 
        ($_.pathname -notmatch "`"")
    } | ForEach-Object {
        Write-Output "[!] Unquoted Path: $($.Name) - $($.PathName)"
    }
}

function Get-ModifiableServiceBins {
    Write-Host "`n[+] Checking for services with modifiable binaries..."
    $services = Get-WmiObject win32_service
    foreach ($svc in $services) {
        $path = $svc.PathName -split ' ')[0].Trim('"')
        if (Test-Path $path) {
            $acl = Get-Acl $path
            if ($acl.AccessToString -match "Everyone Allow.*Write") {
                Write-Output "[!] Writable Service Binary: $($svc.Name) - $path"
            }
        }
    }
}

function Get-WeakPathPermissions {
    Write-Host "`n[+] Checking for modifiable PATH directories..."
    $env:Path.Split(';') | ForEach-Object {
        if (Test-Path $_) {
            $acl = Get-Acl $_
            if ($acl.AccessToString -match "Everyone Allow.*(Write|FullControl)") {
                Write-Output "[!] Writable PATH Folder: $_"
            }
        }
    }
}

function Check-AlwaysInstallElevated {
    Write-Host "`n[+] Checking AlwaysInstallElevated registry keys..."
    $hkcu = Get-ItemProperty -Path "HKCU:\Software\Policies\Microsoft\Windows\Installer" -ErrorAction SilentlyContinue
    $hklm = Get-ItemProperty -Path "HKLM:\Software\Policies\Microsoft\Windows\Installer" -ErrorAction SilentlyContinue
    if (($hkcu.AlwaysInstallElevated -eq 1) -and ($hklm.AlwaysInstallElevated -eq 1)) {
        Write-Output "[!] AlwaysInstallElevated is ENABLED!"
    } else {
        Write-Output "[+] AlwaysInstallElevated not configured or safe."
    }
}

# Main Execution
Get-UnquotedServicePaths
Get-ModifiableServiceBins
Get-WeakPathPermissions
Check-AlwaysInstallElevated

Write-Host "`n[+] Done. Review findings carefully." -ForegroundColor Green
