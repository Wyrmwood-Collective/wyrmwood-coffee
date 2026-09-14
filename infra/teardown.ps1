#Requires -Version 7.0

param(
    [switch]$Force
)

# Constants shared by boot and teardown scripts
. "$PSScriptRoot/config.ps1"

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $false

function Invoke-Step {
    param([string]$Description, [scriptblock]$Command)
    Write-Host "[teardown] $Description"
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "[teardown] ERROR: non-zero exit code: $LASTEXITCODE"
    }
}

Write-Host "[teardown] This will permanently delete:"
Write-Host "[teardown]   - Resource group '$terraformResourceGroupName' (its"
Write-Host "[teardown]     storage account, the tfstate container, and every"
Write-Host "[teardown]     role assignment scoped to it)"
Write-Host "[teardown]   - Resource group '$appResourceGroupName' and every"
Write-Host "[teardown]     resource inside it"
Write-Host "[teardown]   - Azure AD group '$adminGroup' (and its membership)"
Write-Host "[teardown]"
Write-Host "[teardown] WARNING: this destroys the Terraform state backend. If any"
Write-Host "[teardown] resources are still deployed, run ``terraform destroy``"
Write-Host "[teardown] FIRST. Once the state file is gone, Terraform can no longer"
Write-Host "[teardown] manage or clean up those resources."
Write-Host ""

az ad group show --group $adminGroup 1>$null 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "[teardown] Current members of '$adminGroup' who will lose this access:"
    az ad group member list --group $adminGroup --query "[].userPrincipalName" -o tsv | ForEach-Object { Write-Host "[teardown]   - $_" }
    Write-Host ""
}
$LASTEXITCODE = 0

if (-not $Force) {
    $confirmation = Read-Host "Type the resource group name ('$terraformResourceGroupName') to confirm teardown"
    if ($confirmation -cne $terraformResourceGroupName) {
        Write-Host "[teardown] Confirmation did not match. Aborting."
        exit 1
    }
}

Invoke-Step "Deleting application resource group (and scoped role assignments)..." {
    if ((az group exists --name $appResourceGroupName) -ceq "true") {
        az group delete --name $appResourceGroupName --yes
    } else {
        Write-Host "[teardown] Resource group '$appResourceGroupName' not found; skipping."
        $global:LASTEXITCODE = 0
    }
}

Invoke-Step "Deleting Terraform state resource group (storage account, container, and scoped role assignments go with it)..." {
    if ((az group exists --name $terraformResourceGroupName) -ceq "true") {
        az group delete --name $terraformResourceGroupName --yes
    } else {
        Write-Host "[teardown] Resource group '$terraformResourceGroupName' not found; skipping."
        $global:LASTEXITCODE = 0
    }
}

Invoke-Step "Deleting Terraform admins group..." {
    az ad group show --group $adminGroup 1>$null 2>$null
    if ($LASTEXITCODE -eq 0) {
        az ad group delete --group $adminGroup
    } else {
        Write-Host "[teardown] Group '$adminGroup' not found; skipping."
        $global:LASTEXITCODE = 0
    }
}

Write-Host "[teardown] Teardown finished successfully."
