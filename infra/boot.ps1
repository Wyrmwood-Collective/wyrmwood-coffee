$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$currentDir = (Resolve-Path ".").Path
if ($currentDir -ne $repoRoot) {
  Write-Host "[boot] This script must be run from the project root."
  Write-Host "[boot] Project Root = $repoRoot"
  return
}

function Invoke-Step {
  param([string]$Description, [scriptblock]$Command)
  Write-Host "[boot] $Description"
  & $Command
  if ($LASTEXITCODE -ne 0) {
    throw "[boot] ERROR: non-zero exit code: $LASTEXITCODE"
  }
}

Invoke-Step "Creating resource group for the object storage account..." {
  az group create --name wyrmwood_collective --location centralus
}

Invoke-Step "Creating storage account for the state container..." {
  az storage account create `
    --name wyrmwoodstorage `
    --resource-group wyrmwood_collective `
    --sku Standard_LRS `
    --encryption-services blob
}

Invoke-Step "Enabling blob versioning on the storage account (for versioning the state file)..." {
  az storage account blob-service-properties update `
    --account-name wyrmwoodstorage `
    --enable-versioning true
}

Invoke-Step "Creating the storage container to hold the Terraform state file..." {
  az storage container create `
    --name tfstate `
    --account-name wyrmwoodstorage
}

Invoke-Step "Initializing Terraform..." {
  terraform -chdir=infra init
}

Write-Host "[boot] Boot process finished successfully."
Write-Host '[boot] Run `terraform -chdir=infra apply` to provision.'

# create the service principal (for CI/CD authentication)
# save this information somwhere safe!
# az ad sp create-for-rbac `
#   --name "wyrmwood-terraform-sp" `
#   --role "Contributor" `
#   --scopes "/subscriptions/$(az account show --query id -o tsv)"
