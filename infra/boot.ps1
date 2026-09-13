#Requires -Version 7.0

# Terraform state file resource group and storage account/container
$terraformResourceGroupName = "wyrmwood_collective"
$terraformStorageAccountName = "wyrmwoodstorage"
$terraformContainerName = "tfstate"
$terraformKey = "prod.terraform.tfstate"

# Other constants shared between the boot script and the configuration files
$adminGroup = "terraform-infra-admins"
$githubAppDisplayName = "github-actions-wyrmwood-coffee"

# Constants only needed by the boot script
$subscriptionId = "9d3db13e-5092-43f3-94e9-e1e916637239"
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

Invoke-Step "Creating group for Terraform admins..." {
    az ad group create --display-name $adminGroup --mail-nickname $adminGroup
}

Invoke-Step "Assigning permissions to Terraform admins group for resource group..." {
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
"@ | Out-File -FilePath (Join-Path $PSScriptRoot "backend.hcl") -Encoding utf8

@"
# Do not manually edit this file; it is generated automatically by the boot script.
# Make changes in ``boot.ps1`` and run to regenerate.
terraform_infra_admins_group_name        = "$adminGroup"
terraform_github_actions_deploy_app_name = "$githubAppDisplayName"
"@ | Out-File -FilePath (Join-Path $PSScriptRoot "generated.auto.tfvars") -Encoding utf8 -NoNewline
}

Write-Host "[boot] Boot process finished successfully."
Write-Host '[boot] Run `terraform init` to initialize Terraform,'
Write-Host '[boot] then `terraform apply` to provision.'
Write-Host "[boot] You may need to wait for permissions to propagate."
Write-Host "[boot] If you get an error, wait and try again."
