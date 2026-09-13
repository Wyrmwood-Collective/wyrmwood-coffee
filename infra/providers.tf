terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }

    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 3.0"
    }

    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }

  backend "azurerm" {
    use_azuread_auth = true
  }
}

variable "subscription_id" {
  type = string
}

variable "tenant_id" {
  type = string
}

provider "azurerm" {
  features {}
  use_cli         = true
  subscription_id = var.subscription_id
  tenant_id       = var.tenant_id
}

provider "azuread" {
  use_cli   = true
  tenant_id = var.tenant_id
}
