# Constants shared by boot.ps1 and teardown.ps1.
# Changing these values after resources have been deployed
# may result in duplicated or orphaned resources.

# Terraform state file resource group and storage account/container
$terraformResourceGroupName = "wyrmwood_collective"
$terraformStorageAccountName = "wyrmwoodstorage"
$terraformContainerName = "tfstate"
$terraformKey = "prod.terraform.tfstate"

# Other constants shared across multiple files
$appResourceGroupName = "wyrmwood-coffee-rg"
$adminGroup = "terraform-infra-admins"
