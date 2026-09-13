#Requires -Version 7.0

# Constants shared by boot and teardown scripts
. "$PSScriptRoot/config.ps1"

# Constants only needed by the boot script
$location = "centralus"

$ErrorActionPreference = "Stop"

function Invoke-Step {
    param([string]$Description, [scriptblock]$Command)
    Write-Host "[boot] $Description"
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "[boot] ERROR: non-zero exit code: $LASTEXITCODE"
    }
}

Write-Host "[boot] Provisioning the Terraform backend."
Write-Host "[boot] This script may fail due to delays in permissions propagation."
Write-Host "[boot] If you get a permissions error, wait and try again."

# Determine account details from the currently logged in user
$account = az account show | ConvertFrom-Json
$subscriptionId = $account.id
$tenantId = $account.tenantId
Write-Host "[boot] This deployment will be hosted using:"
Write-Host "[boot]   Account: $($account.name)"
Write-Host "[boot]   Subscription: $subscriptionId"
Write-Host "[boot]   Tenant: $tenantId"

Invoke-Step "Creating resource group for the object storage account..." {
    az group create --name $terraformResourceGroupName --location $location
}

Invoke-Step "Creating storage account for the state container..." {
    az storage account create `
        --name $terraformStorageAccountName `
        --resource-group $terraformResourceGroupName `
        --sku Standard_LRS `
        --encryption-services blob
}

Invoke-Step "Enabling blob versioning on the storage account (for versioning the state file)..." {
    az storage account blob-service-properties update `
        --account-name $terraformStorageAccountName `
        --enable-versioning true
}

Invoke-Step "Creating the storage container to hold the Terraform state file..." {
    az storage container create `
        --name tfstate `
        --account-name $terraformStorageAccountName
}

Invoke-Step "Creating resource group for application resources..." {
    az group create --name $appResourceGroupName --location $location
}

Invoke-Step "Creating group for Terraform admins..." {
    az ad group create --display-name $adminGroup --mail-nickname $adminGroup
}

Invoke-Step "Assigning permissions to Terraform admins group for the state resource group..." {
    az role assignment create `
        --assignee-object-id $(az ad group show --group $adminGroup --query id -o tsv) `
        --assignee-principal-type Group `
        --role "Contributor" `
        --scope "/subscriptions/$subscriptionId/resourceGroups/$terraformResourceGroupName"
}

Invoke-Step "Assigning permissions to Terraform admins group for storage account..." {
    az role assignment create `
        --assignee-object-id $(az ad group show --group $adminGroup --query id -o tsv) `
        --assignee-principal-type Group `
        --role "Storage Blob Data Contributor" `
        --scope "/subscriptions/$subscriptionId/resourceGroups/$terraformResourceGroupName/providers/Microsoft.Storage/storageAccounts/$terraformStorageAccountName"
}

Invoke-Step "Assigning permissions to Terraform admins group for the application resource group..." {
    az role assignment create `
        --assignee-object-id $(az ad group show --group $adminGroup --query id -o tsv) `
        --assignee-principal-type Group `
        --role "Contributor" `
        --scope "/subscriptions/$subscriptionId/resourceGroups/$appResourceGroupName"
}

Invoke-Step "Adding current user to Terraform admins group..." {
    $currentUserId = $(az ad signed-in-user show --query id -o tsv)
    if ($(az ad group member check --group $adminGroup --member-id $currentUserId --query value -o tsv) -ceq "false") {
        az ad group member add --group $adminGroup --member-id $currentUserId
    }
}

Invoke-Step "Writing the backend configuration..." {
@"
# Do not manually edit this file; it is generated automatically by the boot script.
# Make changes in ``boot.ps1`` and run to regenerate.
resource_group_name  = "$terraformResourceGroupName"
storage_account_name = "$terraformStorageAccountName"
container_name       = "$terraformContainerName"
key                  = "$terraformKey"
subscription_id      = "$subscriptionId"
tenant_id            = "$tenantId"
"@ | Out-File -FilePath (Join-Path $PSScriptRoot "backend.hcl") -Encoding utf8

@"
# Do not manually edit this file; it is generated automatically by the boot script.
# Make changes in ``boot.ps1`` and run to regenerate.
subscription_id = "$subscriptionId"
tenant_id       = "$tenantId"
"@ | Out-File -FilePath (Join-Path $PSScriptRoot "generated.auto.tfvars") -Encoding utf8
}

Write-Host "[boot] Boot process finished successfully."
Write-Host '[boot] Run `terraform init` to initialize Terraform,'
Write-Host '[boot] then `terraform apply` to provision.'
