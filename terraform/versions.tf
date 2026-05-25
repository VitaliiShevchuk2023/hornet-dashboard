terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.95"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 2.47"
    }
  }

  # Uncomment after creating storage account manually (one-time bootstrap):
  # backend "azurerm" {
  #   resource_group_name  = "rg-hornet-tfstate"
  #   storage_account_name = "sthornettfstate"
  #   container_name       = "tfstate"
  #   key                  = "hornet-dashboard.terraform.tfstate"
  # }
}

provider "azurerm" {
  features {}
}
