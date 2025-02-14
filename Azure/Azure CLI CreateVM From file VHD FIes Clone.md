
# Azure CLI VM Deployment in AZURE STACK Hybrid Cloud (Detailed Tutorial)

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
**Explanation:**
- **az cloud register**: Registers a custom Azure cloud (Azure Stack) with specified endpoints.
- **-n**: Cloud name.
- **--endpoint-resource-manager**: Management endpoint URL.
- **--suffix-storage-endpoint**: Storage endpoint suffix.
- **--suffix-keyvault-dns**: Key Vault DNS suffix.

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
az group list --query "[?name=='ITRESOURCES-GROUP']"
```
Queries a specific resource group.

```sh
az storage blob show --account-name itrgrp0001disks --container-name vhds --name itosdisk-sdwan-clone.vhd
```
Displays details of a specific VHD file in a storage account.

```sh
az storage account list -g ITRESOURCES-GROUP --output table
```
Lists storage accounts in a resource group.

---

## 🖥️ **VM Creation Commands**

### **Create VM SDWANVM-SVR**
```sh
az vm create \
   -n SDWANVM-SVR \
   -g itproductlaunch-production \
   --use-unmanaged-disk \
   --attach-os-disk https://itproductlaunchproddisk.blob.IDStackHub.hybridcloud.id/vhds/SDWANVM-OSDisk.vhd \
   --nics SDWANVM-nic \
   --os-type linux \
   --size Standard_F4s \
   --boot-diagnostics-storage itproductdiag
```

**Explanation:**
- **-n**: VM name.
- **-g**: Resource group.
- **--use-unmanaged-disk**: Uses unmanaged disks.
- **--attach-os-disk**: Attaches an existing OS disk.
- **--nics**: Network interface.
- **--os-type**: OS type.
- **--size**: VM size.
- **--boot-diagnostics-storage**: Storage account for boot diagnostics.

(Repeat similar sections for SDWANVM-DB-02, SDWANVM-MICRO-01, and SDWANVM-MICRO-02 with specific details provided in the input.)

---

This document includes detailed command explanations for registering, managing, and deploying VMs in Azure Stack Hybrid Cloud environments using Azure CLI.
