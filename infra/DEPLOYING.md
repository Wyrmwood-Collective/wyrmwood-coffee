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
This process is often refered to as "infrastructure as code".

### The State File

Terraform must maintain a *state file* that describes the current set of provisioned resources and their current configurations.
This state file needs to be shared among any team member who needs to update the deployment.
However, the state file contains sensitive information (like database passwords), so it can't be checked into version control.
One approach, the approach this application takes, is to store the state file in a manually provisioned object storage resource.
Terraform updates this state file whenever the configuration is updated (by editing the configuration files) and applied (by running `terraform apply`).
In order to prevent multiple users from updating the infrastructure at the same time,
Terraform obtains a lock on the state file before making changes.

## Setup

## Installing Dependencies

Install the Azure command-line tool, the GitHub command-line tool, and Terraform:

```PowerShell
winget install -e --id Microsoft.AzureCLI
winget install -e --id GitHub.cli
winget install -e --id Hashicorp.Terraform
```

Terraform will use the Azure CLI and the GitHub CLI to authentice, so they are required.
Make sure to log in with both tools before proceeding:

```PowerShell
az login
gh auth login
```

## Bootstrapping

Remember that Terraform relies on a state file which has to be shared between anyone making changes to the deployment configuration.
This project stores the shared state file in Azure.
Terraform can't setup the cloud resources for the state file itself, because Terraform depends on the state file.
So we need to do a one-time bootrapping step, which must be performed by the owner of the Azure account.

The `infra/boot.ps1` script creates the resource group and storage account that holds the Terraform state file,
and creates the Terraform admin group that will have permission to provision resources.

The boot script is idempotent and will add the current user (the Azure account owner) to the Terraform admin group.
It also generates two files (`generated.auto.tfvars` and `backend.hcl`) which are used by the configuration.

## Adding Additional Users to the Admin Group

To allow others to make changes to the deployment configuration they must be added to the admin group.

Begin by adding the user in the Azure portal (Azure Portal → Microsoft Entra ID → Add → User → Invite External User).
Once the user accepts, this creates a guest object for that user in your Azure directory.

To see current guest users and their object IDs:

```PowerShell
az ad user list --filter "userType eq 'Guest'" --query "[].{displayName:displayName, upn:userPrincipalName, id:id}" -o json
```

To see current permissions for a user `$objectId`:

```PowerShell
az role assignment list --assignee $objectId --all --include-groups -o json
```

To add the user `$objectId` to the Terraform admin group:

```PowerShell
az ad group member add --group "terraform-infra-admins" --member-id $objectId
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

When satisified, apply the changes with:

```PowerShell
terraform apply
```

## Rotating Passwords

If a password is ever compromised, rotate with:

```PowerShell
terraform apply -replace="random_password.postgres_admin_password"
```
