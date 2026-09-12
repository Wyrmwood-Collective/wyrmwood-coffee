data "github_repository" "wyrmwood_coffee" {
  full_name = "Wyrmwood-Collective/wyrmwood-coffee"
}

resource "github_actions_environment_variable" "azure_webapp_name" {
  repository    = data.github_repository.wyrmwood_coffee.name
  environment   = "staging"
  variable_name = "AZURE_WEBAPP_NAME"
  value         = azurerm_linux_web_app.fastapi.name
}

resource "github_actions_environment_secret" "staging_database_url" {
  repository  = data.github_repository.wyrmwood_coffee.name
  environment = "staging"
  secret_name = "STAGING_DATABASE_URL"
  value       = azurerm_linux_web_app.fastapi.app_settings.STAGING_DATABASE_URL
}

resource "github_actions_environment_secret" "azure_client_id" {
  repository  = data.github_repository.wyrmwood_coffee.name
  environment = "staging"
  secret_name = "AZURE_CLIENT_ID"
  value       = azuread_application.github_actions.client_id
}

resource "github_actions_environment_secret" "azure_tenant_id" {
  repository  = data.github_repository.wyrmwood_coffee.name
  environment = "staging"
  secret_name = "AZURE_TENANT_ID"
  value       = data.azurerm_client_config.current.tenant_id
}

resource "github_actions_environment_secret" "azure_subscription_id" {
  repository  = data.github_repository.wyrmwood_coffee.name
  environment = "staging"
  secret_name = "AZURE_SUBSCRIPTION_ID"
  value       = data.azurerm_client_config.current.subscription_id
}
