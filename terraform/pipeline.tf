# ── GBIF Pipeline Job ─────────────────────────────────

resource "azurerm_container_app_job" "gbif_sync" {
  name                         = "job-gbif-sync-${var.environment}"
  resource_group_name          = azurerm_resource_group.main.name
  location                     = azurerm_resource_group.main.location
  container_app_environment_id = azurerm_container_app_environment.main.id

  replica_timeout_in_seconds = 7200

  schedule_trigger_config {
    cron_expression          = "0 3 * * 1"
    parallelism              = 1
    replica_completion_count = 1
  }

  # ACR credentials — так само як в Container App
  registry {
    server               = azurerm_container_registry.main.login_server
    username             = azurerm_container_registry.main.admin_username
    password_secret_name = "acr-password"
  }

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.main.admin_password
  }

  secret {
    name  = "storage-account-key"
    value = azurerm_storage_account.data.primary_access_key
  }

  template {
    container {
      name    = "gbif-pipeline"
      image   = "${azurerm_container_registry.main.login_server}/hornet-dashboard:${var.image_tag}"
      cpu     = 1.0
      memory  = "2Gi"
      command = ["python", "download_gbif.py"]

      env {
        name  = "AZURE_STORAGE_ACCOUNT_NAME"
        value = azurerm_storage_account.data.name
      }
      env {
        name        = "AZURE_STORAGE_ACCOUNT_KEY"
        secret_name = "storage-account-key"
      }
      env {
        name  = "AZURE_STORAGE_CONTAINER"
        value = azurerm_storage_container.gbif_data.name
      }
      env {
        name  = "UPLOAD_TO_AZURE"
        value = "true"
      }
    }
  }

  tags = local.common_tags
}

output "pipeline_job_name" {
  description = "Container Apps Job name (для ручного запуску)"
  value       = azurerm_container_app_job.gbif_sync.name
}
