locals {
  prefix   = "${var.project_name}-${var.environment}"
  acr_name = replace(local.prefix, "-", "")

  common_tags = {
    project     = var.project_name
    environment = var.environment
    managed_by  = "terraform"
    team        = "CorrelAid"
    partner     = "NABU"
  }
}

resource "azurerm_resource_group" "main" {
  name     = "rg-${local.prefix}"
  location = var.location
  tags     = local.common_tags
}

resource "azurerm_container_registry" "main" {
  name                = local.acr_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = true
  tags                = local.common_tags
}

resource "azurerm_log_analytics_workspace" "main" {
  name                = "log-${local.prefix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = local.common_tags
}

resource "azurerm_container_app_environment" "main" {
  name                       = "cae-${local.prefix}"
  resource_group_name        = azurerm_resource_group.main.name
  location                   = azurerm_resource_group.main.location
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  tags                       = local.common_tags
}

resource "azurerm_container_app" "dashboard" {
  name                         = "ca-${local.prefix}"
  resource_group_name          = azurerm_resource_group.main.name
  container_app_environment_id = azurerm_container_app_environment.main.id
  revision_mode                = "Single"

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
    name  = "eu-hornet-gdrive-id"
    value = var.eu_hornet_gdrive_id
  }

  secret {
    name  = "as-hornet-gdrive-id"
    value = var.as_hornet_gdrive_id
  }

  template {
    min_replicas = var.min_replicas
    max_replicas = var.max_replicas

    container {
      name   = "streamlit"
      image  = "${azurerm_container_registry.main.login_server}/${var.project_name}:${var.image_tag}"
      cpu    = var.cpu
      memory = var.memory

      env {
        name        = "EU_HORNET_GDRIVE_ID"
        secret_name = "eu-hornet-gdrive-id"
      }
      env {
        name        = "AS_HORNET_GDRIVE_ID"
        secret_name = "as-hornet-gdrive-id"
      }
      env {
        name  = "STREAMLIT_SERVER_PORT"
        value = "8501"
      }
      env {
        name  = "STREAMLIT_BROWSER_GATHER_USAGE_STATS"
        value = "false"
      }

      liveness_probe {
        transport               = "HTTP"
        path                    = "/_stcore/health"
        port                    = 8501
        initial_delay           = 30
        interval_seconds        = 30
        timeout                 = 10
        failure_count_threshold = 3
      }
    }

    http_scale_rule {
      name                = "http-scaler"
      concurrent_requests = "20"
    }
  }

  ingress {
    external_enabled = true
    target_port      = 8501
    transport        = "http"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  tags = local.common_tags
}
