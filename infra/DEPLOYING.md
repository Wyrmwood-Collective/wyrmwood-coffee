# Deployment Guide

This application's deployment infrastructure is managed using [Terraform](https://developer.hashicorp.com/terraform).

## Terraform

### What Is Terraform?

Terraform is a tool for provisioning cloud resources using declarative configuration.
In other words, instead of manually provisioning cloud resources using a cloud provider's web interface,
you write configuration files (see `infra/*.tf`) that specify the desired configuration,
run `terraform apply`, and let Terraform make all the necessary changes for you.

Managing cloud resources in this way allows developers to track changes with version control software,
just as if it were any other part of your application code.
This process is often referred to as "infrastructure as code".

### The State File

Terraform must maintain a *state file* that describes the current set of provisioned resources and their current configurations.
This state file needs to be shared among any team member who needs to update the deployment.
However, the state file contains sensitive information (like database passwords), so it can't be checked into version control.
One approach, the approach this application takes, is to store the state file in a manually provisioned object storage resource.
Terraform updates this state file whenever the configuration is updated (by editing the configuration files) and applied (by running `terraform apply`).
In order to prevent multiple users from updating the infrastructure at the same time,
Terraform obtains a lock on the state file before making changes.

## Setup

### Installing Dependencies

Install the Azure command-line tool, the GitHub command-line tool, and Terraform:

```PowerShell
winget install -e --id Microsoft.AzureCLI
winget install -e --id Hashicorp.Terraform
```

Terraform will use the Azure CLI to authenticate, so it is required.
Make sure to log in before proceeding.
When logging in to Azure, replace `TENANT_ID` with the ID specified in `infra/backend.hcl`.

**Note:** For the initial bootstrap, when there is no `infra/backend.hcl` file,
specify whichever tenant you want to host the infrastructure.

```PowerShell
az login --tenant TENANT_ID
```

### Bootstrapping

Remember that Terraform relies on a state file which has to be shared between anyone making changes to the deployment configuration.
This project stores the shared state file in Azure.
Terraform can't setup the cloud resources for the state file itself, because Terraform depends on the state file.
So we need to do a one-time bootstrapping step, which must be performed by the owner of the Azure account.

The `infra/boot.ps1` script creates the resource group and storage account that holds the Terraform state file,
and creates the Terraform admin group that will have permission to provision resources.

The boot script is idempotent and will add the current user (the Azure account owner) to the Terraform admin group.
It also generates two files (`generated.auto.tfvars` and `backend.hcl`) which are used by the configuration.
These files pin the subscription and tenant that were active in the Azure CLI when the script ran,
so any subsequent `terraform` calls will fail if a user authenticates against the wrong subscription.

You may need to run `az logout` and `az login` after running the boot script in order for Terraform to authorize with Azure (group membership claims are cached in the token).

### Adding Additional Users to the Admin Group

To allow others to make changes to the deployment configuration you must:

1. Add them to the Terraform admin group
2. Grant them the Microsoft Graph "Directory Readers" permission

Begin by adding the user in the Azure portal (Azure Portal → Microsoft Entra ID → Add → User → Invite External User).
Once the user accepts, this creates a guest object for that user in your Azure directory.

To see current guest users and their object IDs:

```PowerShell
az ad user list --filter "userType eq 'Guest'" --query "[].{displayName:displayName, upn:userPrincipalName, id:id}" -o json
```

To add the user `$objectId` to the Terraform admin group (not idempotent):

```PowerShell
az ad group member add --group "terraform-infra-admins" --member-id $objectId
```

To grant the "Directory Readers" role (not idempotent):

```PowerShell
# `New-TemporaryFile` is necessary due to a quirk of how `az rest` handles string arguments
$body = @{
    principalId      = $objectId
    roleDefinitionId = "88d8e3e3-8f55-4a1e-953a-9b9898b8876b" # "Directory Readers" UUID
    directoryScopeId = "/"
} | ConvertTo-Json -Compress
$bodyFile = New-TemporaryFile
Set-Content -Path $bodyFile -Value $body -NoNewline -Encoding utf8
az rest --method POST --uri "https://graph.microsoft.com/v1.0/roleManagement/directory/roleAssignments" --headers "Content-Type=application/json" --body "@$bodyFile"
Remove-Item $bodyFile
```

To list the current members of the admin group:

```PowerShell
az ad group member list --group "terraform-infra-admins" --query "[].{displayName:displayName, upn:userPrincipalName, id:id}" -o json
```

## Applying Configuration Changes

**Note:** Run `terraform` from the `infra` directory.
You may also run from the project root if you add `-chdir=infra` to your invocation.

First initialize Terraform (all users must do this on a new machine):

```PowerShell
terraform init --backend-config=backend.hcl
```

Make the necessary configuration changes in the `.tf` files. Preview the changes with:

```PowerShell
terraform plan
```

When satisfied, apply the changes with:

```PowerShell
terraform apply
```

## Deprovisioning

To deprovision all resources, run `terraform destroy`,
then run `infra/teardown.ps1` to remove the state storage account and its resource group,
the application resource group, and the admin group.
