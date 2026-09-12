#Requires -Version 7.0

$subscriptionId = "9d3db13e-5092-43f3-94e9-e1e916637239"
$configResourceGroup = "wyrmwood_collective"
$location = "centralus"
$storageAccount = "wyrmwoodstorage"
$adminGroup = "terraform-infra-admins"
$appDisplayName = "github-actions-deploy-myapp"

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
    az group create --name $configResourceGroup --location $location
}

Invoke-Step "Creating storage account for the state container..." {
    az storage account create `
        --name $storageAccount `
        --resource-group $configResourceGroup `
        --sku Standard_LRS `
        --encryption-services blob
}

Invoke-Step "Enabling blob versioning on the storage account (for versioning the state file)..." {
    az storage account blob-service-properties update `
        --account-name $storageAccount `
        --enable-versioning true
}

Invoke-Step "Creating the storage container to hold the Terraform state file..." {
    az storage container create `
        --name tfstate `
        --account-name $storageAccount
}

Invoke-Step "Creating group for Terraform admins..." {
    az ad group create --display-name $adminGroup --mail-nickname $adminGroup
}

Invoke-Step "Assigning permissions to Terraform admins group for resource group..." {
    az role assignment create `
        --assignee-object-id $(az ad group show --group $adminGroup --query id -o tsv) `
        --assignee-principal-type Group `
        --role "Contributor" `
        --scope "/subscriptions/$subscriptionId/resourceGroups/$configResourceGroup"
}

Invoke-Step "Assigning permissions to Terraform admins group for storage account..." {
    az role assignment create `
        --assignee-object-id $(az ad group show --group $adminGroup --query id -o tsv) `
        --assignee-principal-type Group `
        --role "Storage Blob Data Contributor" `
        --scope "/subscriptions/$subscriptionId/resourceGroups/$configResourceGroup/providers/Microsoft.Storage/storageAccounts/$storageAccount"
}

Invoke-Step "Adding current user to Terraform admins group..." {
    $currentUserId = $(az ad signed-in-user show --query id -o tsv)
    if ($(az ad group member check --group $adminGroup --member-id $currentUserId --query value -o tsv) -ceq "false") {
        az ad group member add --group $adminGroup --member-id $currentUserId
    }
}

Invoke-Step "Creating the app registration..." {
    $existingApp = az ad app list --display-name $appDisplayName --query "[0]" | ConvertFrom-Json
    if (-not $existingApp) {
        az ad app create --display-name $appDisplayName --query appId -o tsv
    }
}

Write-Host "[boot] Boot process finished successfully."
Write-Host '[boot] Run `terraform init` to initialize Terraform,'
Write-Host '[boot] then `terraform apply` to provision.'
Write-Host "[boot] You may need to wait for permissions to propagate."
Write-Host "[boot] If you get an error, wait and try again."
