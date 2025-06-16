
# VM Deployment with AzCli in Azure Stack Hub From VHD (Detailed Tutorial)

This guide provides a detailed explanation of Azure CLI commands used to register a hybrid cloud, manage resources, and create virtual machines (VMs) with unmanaged disks.

---

## 📌 **Azure Cloud Registration**
```sh
az cloud register \
  -n AzureStackIDStackHub \
  --endpoint-resource-manager "https://management.IDStackHub.hybridcloud.id" \
  --suffix-storage-endpoint "IDStackHub.hybridcloud.id" \
  --suffix-keyvault-dns ".vault.IDStackHub.hybridcloud.id"
```
**Explanation:** Registers a custom Azure cloud (Azure Stack) with specified endpoints.

---

## 📄 **Cloud Management Commands**
```sh
az cloud list --output table
```
Lists all registered clouds.

```sh
az cloud set -n AzureStackUser
```
Sets the active cloud.

```sh
az cloud update --profile latest
```
Updates the cloud profile to the latest version.

---

## 🔐 **Azure Login and Account Check**
```sh
az login
az account show
```
Logs in and shows current account details.

---

## 📦 **Resource and Storage Management**
```sh
az group list --query "[?name=='IT-RESOURCESGRP']"
```
Queries a specific resource group.

```sh
az storage blob show --account-name itrgrp0001disks --container-name vhds --name SDWAN-OSDISK.vhd
```
Displays details of a specific VHD file.

```sh
az storage account list -g IT-RESOURCESGRP --output table
```
Lists storage accounts in the specified resource group.

---

## 🖥️ **VM Creation Commands**

### **SDWANVM-SVR**
```sh
az vm create \
   -n SDWANVM-SVR \
   -g itproductlaunch-production \
   --use-unmanaged-disk \
   --attach-os-disk https://itproductdisk.blob.IDStackHub.hybridcloud.id/vhds/SDWAN-OSDISK.vhd \
   --nics SDWANVM-F4S-01-nic \
   --os-type linux \
   --size Standard_F4s \
   --boot-diagnostics-storage itproductdiag
```

**Explanation:** Each section provides VM creation steps with unmanaged disks, network interfaces, OS type, and storage settings.

---

This document offers step-by-step guidance for deploying VMs in Azure Stack Hybrid Cloud using Azure CLI.

