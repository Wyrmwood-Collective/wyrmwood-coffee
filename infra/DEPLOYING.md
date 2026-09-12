# Deploying to Azure

## Understanding the Deployment Configuration

This application's deployment infrastructure is managed using [Terraform](https://developer.hashicorp.com/terraform).
Terraform is a tool for provisioning cloud resources using declarative configuration.
In other words, instead of manually provisioning cloud resources using a cloud provider's web interface, you write configuration files (`infra/*.tf`) that specify the desired configuration, and then you run `terraform apply` and it makes all the necessary changes for you.
Managing cloud resources in this way allows managing changes with version control software, just as if it were any other part of your application code (and so people often refer to this concept as "infrastructure as code").

Terraform must maintain a *state file* that describes the current set of provisioned resources and their current configurations.
This state file needs to be shared among any team member who needs to update the deployment.
However, the state file contains sensitive information (like database passwords), so it can't be checked into version control.
One approach, the approach this application takes, is to store the state file in a manually provisioned object storage resource.
Terraform updates this state file whenever the configuration is updated (by editing the configuration files) and applied (by running `terraform apply`).
The tool will obtain a lock on the file before making changes in order to prevent multiple users from updating the infrastructure at the same time.

## Installing Dependencies

Install the Azure command-line tool and Terraform:

```PowerShell
winget install -e --id Microsoft.AzureCLI
winget install -e --id Hashicorp.Terraform
```

Login to Azure:

```PowerShell
az login
```

## Bootstrapping

The owner of the Azure account will need to perform the one-time bootstrap.
The `infra/boot.ps1` script creates the resource group and storage account that holds the Terraform state file,
and creates the Terraform admin group that will have permission to provision resources.

The boot script is idempotent and will add the current user (the Azure account owner) to the Terraform admin group.

## Adding Additional Users to the Admin Group

First, add the user in the Azure portal (Azure Portal → Microsoft Entra ID → Add → User → Invite External User).
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
You may also run from the project root if you add `chdir=infra` to your invocation.

First initialize Terraform (all users must do this on a new machine):

```PowerShell
terraform init
```

To preview changes:

```PowerShell
terraform plan
```

To apply changes:

```PowerShell
terraform apply
```

## Other Commands

To see the database hostname and admin password:

```PowerShell
terraform output postgres_fqdn
terraform output -raw postgres_admin_password
```

## Configuring GitHub for Deployment

GitHub authenticates with Azure using OIDC.
It authenticates as a service principal which has permission to deploy to the app service.

### Environment Secrets

AZURE_CLIENT_ID
AZURE_TENANT_ID
AZURE_SUBSCRIPTION_ID
