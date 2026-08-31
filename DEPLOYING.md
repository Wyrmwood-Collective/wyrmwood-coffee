# Deploying to Azure

Install Azure CLI and Terraform:

```PowerShell
winget install Hashicorp.Terraform
winget install Microsoft.AzureCLI
```

Login to Azure:

```PowerShell
az login
```

## Boostrap

We need to perform some one-time setup before managing deployments with Terraform.

```PowerShell
# create a new resource group
az group create --name wyrmwood_collective --location centralus

# create a new storage account
az storage account create `
  --name wyrmwoodstorage `
  --resource-group wyrmwood_collective `
  --sku Standard_LRS `
  --encryption-services blob

# create the storage container
az storage container create `
  --name tfstate `
  --account-name wyrmwoodstorage `

# enable blob versioning on storage account
az storage account blob-service-properties update `
  --account-name wyrmwoodstorage `
  --enable-versioning true

# create the service principal (for authentication)
# save this information somwhere safe!
az ad sp create-for-rbac `
  --name "wyrmwood-terraform-sp" `
  --role "Contributor" `
  --scopes "/subscriptions/$(az account show --query id -o tsv)"

# terraform init
terraform -chdir=infra init
```
