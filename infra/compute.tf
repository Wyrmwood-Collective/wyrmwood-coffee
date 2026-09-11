resource "azurerm_resource_group" "main" {
  name     = "wyrmwood-coffee-rg"
  location = "centralus"
}

resource "azurerm_service_plan" "main" {
  name = "wyrmwood_app_plan"
  resource_group_name = azurerm_resource_group.main.name
  location = azurerm_resource_group.main.location
  os_type = "Linux"
  sku_name = "B1"
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
  }
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

resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_range" {
  name             = "allow-xchange-range"
  server_id        = azurerm_postgresql_flexible_server.wyrmwood_db.id
  start_ip_address = "216.80.50.122"
  end_ip_address   = "216.80.50.122"
}

output "postgres_fqdn" {
  value = azurerm_postgresql_flexible_server.wyrmwood_db.fqdn
}

output "postgres_admin_password" {
  value = random_password.postgres-admin-password.result
  sensitive = true
}
