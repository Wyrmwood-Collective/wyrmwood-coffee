locals {
  environment = "staging"
}

variable "app_resource_group_name" {
  type = string
}

# The resource group for this application's resources.
data "azurerm_resource_group" "main" {
  name = var.app_resource_group_name
}

resource "random_password" "postgres_admin_password" {
  length = 24
}

resource "azurerm_postgresql_flexible_server" "main" {
  name                = "wyrmwood-coffee-db"
  resource_group_name = data.azurerm_resource_group.main.name
  location            = data.azurerm_resource_group.main.location

  version  = 18
  sku_name = "B_Standard_B1ms"

  storage_mb = 32768 # 32 GB (minimum allowed)

  administrator_login    = "wyrmwood_coffee_db_admin_user"
  administrator_password = random_password.postgres_admin_password.result

  backup_retention_days        = 7 # minimum
  geo_redundant_backup_enabled = false

  public_network_access_enabled = true

  # ignore zone drift since we leave it unspecified
  lifecycle {
    ignore_changes = [zone]
  }
}

locals {
  staging_database_url = format(
    "postgresql+psycopg://%s:%s@%s/%s",
    azurerm_postgresql_flexible_server.main.administrator_login,
    urlencode(random_password.postgres_admin_password.result),
    azurerm_postgresql_flexible_server.main.fqdn,
    azurerm_postgresql_flexible_server_database.main.name
  )
}

resource "azurerm_postgresql_flexible_server_firewall_rule" "azure" {
  name             = "allow-azure-internal-ips"
  server_id        = azurerm_postgresql_flexible_server.main.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

resource "azurerm_postgresql_flexible_server_firewall_rule" "xchange" {
  name             = "allow-xchange-ip"
  server_id        = azurerm_postgresql_flexible_server.main.id
  start_ip_address = "216.80.50.122"
  end_ip_address   = "216.80.50.122"
}

resource "azurerm_postgresql_flexible_server_database" "main" {
  name      = "wyrmwood_coffee"
  server_id = azurerm_postgresql_flexible_server.main.id
  collation = "en_US.utf8"
  charset   = "utf8"
}

resource "azurerm_service_plan" "main" {
  name                = "wyrmwood_app_plan"
  resource_group_name = data.azurerm_resource_group.main.name
  location            = data.azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = "B1"
}

resource "random_password" "jwt_secret_key" {
  length = 64
}

resource "azurerm_linux_web_app" "main" {
  name                = "wyrmwood-coffee-app"
  resource_group_name = data.azurerm_resource_group.main.name
  location            = data.azurerm_resource_group.main.location
  service_plan_id     = azurerm_service_plan.main.id

  site_config {
    application_stack {
      python_version = "3.12"
    }
    app_command_line                  = "bash startup.sh"
    health_check_path                 = "/health"
    health_check_eviction_time_in_min = 2
  }

  app_settings = {
    APP_ENVIRONMENT                = local.environment
    SCM_DO_BUILD_DURING_DEPLOYMENT = true
    STAGING_DATABASE_URL           = local.staging_database_url
    JWT_SECRET_KEY                 = random_password.jwt_secret_key.result
  }
}

output "staging_database_url_psql" {
  description = "Database URL for direct connections with psql"
  value       = replace(local.staging_database_url, "+psycopg", "")
  sensitive   = true
}

output "web_app_default_hostname" {
  value = azurerm_linux_web_app.main.default_hostname
}
