resource "azurerm_resource_group" "main" {
  name     = "wyrmwood-coffee-rg"
  location = "centralus"
}

resource "random_password" "postgres-admin-password" {
  length = 24
}

resource "azurerm_postgresql_flexible_server" "wyrmwood_db" {
  name                = "wyrmwood-coffee-db"
  resource_group_name = azurerm_resource_group.main.name
  location            = "centralus"

  version  = 18
  sku_name = "B_Standard_B1ms"

  storage_mb = 32768 # 32 GB (minimum allowed)

  administrator_login    = "wyrmwood_coffee_db_admin_user"
  administrator_password = random_password.postgres-admin-password.result

  backup_retention_days        = 7 # minimum
  geo_redundant_backup_enabled = false

  # leave zone unspecified let Azure pick, avoids needing paired-zone setup

  public_network_access_enabled = true

  lifecycle {
    ignore_changes = [zone]
  }
}

resource "azurerm_postgresql_flexible_server_firewall_rule" "azure" {
  name             = "allow-azure-internal-ips"
  server_id        = azurerm_postgresql_flexible_server.wyrmwood_db.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

resource "azurerm_postgresql_flexible_server_firewall_rule" "xchange" {
  name             = "allow-xchange-ip"
  server_id        = azurerm_postgresql_flexible_server.wyrmwood_db.id
  start_ip_address = "216.80.50.122"
  end_ip_address   = "216.80.50.122"
}

resource "azurerm_postgresql_flexible_server_database" "wyrmwood_app_db" {
  name      = "wyrmwood_coffee"
  server_id = azurerm_postgresql_flexible_server.wyrmwood_db.id
  collation = "en_US.utf8"
  charset   = "utf8"
}

resource "azurerm_service_plan" "main" {
  name = "wyrmwood_app_plan"
  resource_group_name = azurerm_resource_group.main.name
  location = azurerm_resource_group.main.location
  os_type = "Linux"
  sku_name = "B1"
}

resource "random_password" "jwt_secret_key" {
  length  = 64
}

resource "azurerm_linux_web_app" "fastapi" {
  name = "wyrmwood-coffee-api"
  resource_group_name = azurerm_resource_group.main.name
  location = azurerm_resource_group.main.location
  service_plan_id = azurerm_service_plan.main.id

  site_config {
    application_stack {
      python_version = "3.12"
    }
    app_command_line = "bash startup.sh"
  }

  app_settings = {
    APP_ENVIRONMENT = "staging"
    SCM_DO_BUILD_DURING_DEPLOYMENT = true
    STAGING_DATABASE_URL = format(
      "postgresql+psycopg://%s:%s@%s/%s",
      azurerm_postgresql_flexible_server.wyrmwood_db.administrator_login,
      urlencode(random_password.postgres-admin-password.result),
      azurerm_postgresql_flexible_server.wyrmwood_db.fqdn,
      azurerm_postgresql_flexible_server_database.wyrmwood_app_db.name
    )
    JWT_SECRET_KEY = random_password.jwt_secret_key.result
  }
}

data "azuread_group" "terraform_infra_admins" {
  display_name     = "terraform-infra-admins"
  security_enabled = true
}

resource "azuread_application" "github_actions" {
  display_name = "github-actions-deploy-myapp"
  owners       = data.azuread_group.terraform_infra_admins.members
}

resource "azuread_service_principal" "github_actions" {
  client_id = azuread_application.github_actions.client_id
}

resource "azuread_application_federated_identity_credential" "github_actions_staging_env" {
  application_id = azuread_application.github_actions.id
  display_name   = "github-actions-staging-environment"
  audiences      = ["api://AzureADTokenExchange"]
  issuer         = "https://token.actions.githubusercontent.com"
  subject        = "repo:Wyrmwood-Collective@319175686/wyrmwood-coffee@1323499178:environment:staging"
}

resource "azurerm_role_assignment" "github_staging" {
  scope                = azurerm_linux_web_app.fastapi.id
  role_definition_name = "Website Contributor"
  principal_id         = azuread_service_principal.github_actions.object_id
}

# Lets the seed-staging workflow read the flexible server and manage its
# firewall rules (it opens/closes a rule for the runner's IP each run).
resource "azurerm_role_assignment" "github_staging_postgres" {
  scope                = azurerm_postgresql_flexible_server.wyrmwood_db.id
  role_definition_name = "Contributor"
  principal_id         = azuread_service_principal.github_actions.object_id
}

data "azurerm_client_config" "current" {}

output "azure_client_id" {
  value = azuread_application.github_actions.client_id
}

output "azure_tenant_id" {
  value = data.azurerm_client_config.current.tenant_id
}

output "azure_subscription_id" {
  value = data.azurerm_client_config.current.subscription_id
}

output "postgres_fqdn" {
  value = azurerm_postgresql_flexible_server.wyrmwood_db.fqdn
}

output "postgres_admin_password" {
  value = random_password.postgres-admin-password.result
  sensitive = true
}

output "web_app_default_hostname" {
  value = azurerm_linux_web_app.fastapi.default_hostname
}
