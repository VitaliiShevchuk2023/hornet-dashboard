# ── Azure Blob Storage ────────────────────────────────
locals {
  # Унікальна назва storage account — макс 24 символи, лише a-z0-9
  storage_name = "sthornet${substr(var.environment, 0, 4)}vsh"
}

resource "azurerm_storage_account" "data" {
  name                            = local.storage_name
  resource_group_name             = azurerm_resource_group.main.name
  location                        = azurerm_resource_group.main.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = true
  tags                            = local.common_tags
}

resource "azurerm_storage_container" "gbif_data" {
  name                  = "gbif-data"
  storage_account_name  = azurerm_storage_account.data.name
  container_access_type = "blob"
}

output "storage_account_name" {
  description = "Storage account name"
  value       = azurerm_storage_account.data.name
}

output "gbif_data_base_url" {
  description = "Base URL для читання CSV файлів"
  value       = "https://${azurerm_storage_account.data.name}.blob.core.windows.net/${azurerm_storage_container.gbif_data.name}"
}

output "european_hornet_url" {
  description = "Пряме посилання на European hornet CSV"
  value       = "https://${azurerm_storage_account.data.name}.blob.core.windows.net/${azurerm_storage_container.gbif_data.name}/european_hornet_DE.csv"
}

output "asian_hornet_url" {
  description = "Пряме посилання на Asian hornet CSV"
  value       = "https://${azurerm_storage_account.data.name}.blob.core.windows.net/${azurerm_storage_container.gbif_data.name}/asian_hornet_DE.csv"
}
