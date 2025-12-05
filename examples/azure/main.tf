terraform {
  required_version = ">= 1.0"
  
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
  
  backend "azurerm" {
    # Backend configuration provided via workflow
  }
}

provider "azurerm" {
  features {}
}

# Create a resource group
resource "azurerm_resource_group" "example" {
  name     = var.resource_group_name
  location = var.location
  
  tags = var.common_tags
}

# Use CloudOps Azure AVM module for virtual network
module "network" {
  source = "../../modules/azure-avm/virtual-network"
  
  resource_group_name = azurerm_resource_group.example.name
  location            = azurerm_resource_group.example.location
  vnet_name          = var.vnet_name
  address_space      = var.vnet_address_space
  
  subnets = {
    default = {
      address_prefix = "10.0.1.0/24"
    }
    app = {
      address_prefix    = "10.0.2.0/24"
      service_endpoints = ["Microsoft.Storage", "Microsoft.KeyVault"]
    }
  }
  
  tags = var.common_tags
}

# Use CloudOps Azure AVM module for storage account
module "storage" {
  source = "../../modules/azure-avm/storage-account"
  
  resource_group_name    = azurerm_resource_group.example.name
  location               = azurerm_resource_group.example.location
  storage_account_name   = var.storage_account_name
  account_tier           = "Standard"
  replication_type       = "LRS"
  
  enable_https_traffic_only = true
  min_tls_version           = "TLS1_2"
  allow_public_access       = false
  enable_versioning         = true
  
  containers = {
    data = {
      access_type = "private"
    }
    backups = {
      access_type = "private"
    }
  }
  
  tags = var.common_tags
}
