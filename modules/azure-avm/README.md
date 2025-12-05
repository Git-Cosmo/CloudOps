# Azure Verified Modules (AVM) - CloudOps Edition

This directory contains curated Azure Verified Module-style Terraform modules for common infrastructure patterns.

## Available Modules

### Networking
- `virtual-network` - Azure Virtual Network with subnets
- `network-security-group` - Network Security Groups with rules

### Compute
- `virtual-machine` - Azure Virtual Machines
- `aks-cluster` - Azure Kubernetes Service clusters

### Storage
- `storage-account` - Azure Storage Accounts

### Database
- `sql-database` - Azure SQL Database

## Usage

Reference these modules from your Terraform configuration:

```hcl
module "network" {
  source = "./modules/azure-avm/virtual-network"
  
  resource_group_name = "my-rg"
  location            = "eastus"
  vnet_name          = "my-vnet"
  address_space      = ["10.0.0.0/16"]
  
  subnets = {
    default = {
      address_prefix = "10.0.1.0/24"
    }
  }
}
```

## Design Principles

These modules follow Azure Verified Module standards:
- Consistent naming conventions
- Comprehensive tagging support
- Security best practices by default
- Modular and composable design
