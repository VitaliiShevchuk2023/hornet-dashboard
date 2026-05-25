output "dashboard_url" {
  description = "Public URL of the Streamlit dashboard"
  value       = "https://${azurerm_container_app.dashboard.ingress[0].fqdn}"
}

output "acr_login_server" {
  description = "ACR login server"
  value       = azurerm_container_registry.main.login_server
}

output "acr_admin_username" {
  description = "ACR admin username"
  value       = azurerm_container_registry.main.admin_username
  sensitive   = true
}

output "resource_group_name" {
  description = "Resource group name"
  value       = azurerm_resource_group.main.name
}

output "container_app_name" {
  description = "Container App name"
  value       = azurerm_container_app.dashboard.name
}
