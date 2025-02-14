
# AKS Engine Deployment on Azure Stack Hub (Detailed Tutorial)

This guide provides a step-by-step tutorial with explanations for deploying AKS Engine on Azure Stack Hub using Azure CLI.

---

## 📌 **Install Azure CLI on AKS Engine**
```sh
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```
**Explanation:** This command downloads and installs the Azure CLI on a Linux machine.

---

## 📄 **Register Azure Stack Endpoint**

### For IDWest:
```sh
az cloud register -n AzureStackUserIDWest --endpoint-resource-manager "https://management.idwest.hybridcloud.id" --suffix-storage-endpoint "idwest.hybridcloud.id" --suffix-keyvault-dns ".vault.idwest.hybridcloud.id"
```
### For IDSouth:
```sh
az cloud register -n AzureStackUserIDSouth --endpoint-resource-manager "https://management.idsouth.hybridcloud.id" --suffix-storage-endpoint "idsouth.hybridcloud.id" --suffix-keyvault-dns ".vault.idsouth.hybridcloud.id"
```
**Explanation:** Registers custom Azure Stack endpoints for different regions.

---

## 🔐 **Login to Azure Stack via Azure CLI**
```sh
az cloud set -n AzureStackUserIDSouth
az cloud set -n AzureStackUserIDWest
az cloud update --profile 2019-03-01-hybrid
az login
```
**Alternative login:**
```sh
az login -u <service-principal-id> -p <password> --service-principal --tenant <tenant-id>
```
**Explanation:** Configures and logs into the specified Azure Stack environment.

---

## 📂 **Prepare Kubernetes Configuration**
- Copy `Kubernetes.json` to `/home/<username>`.
- Rename and customize the `Kubernetes.json` file as per your requirements.

```sh
aks-engine generate ./kubernetes.json
```
**Explanation:** Generates Kubernetes deployment files and creates the `_output` folder.

---

## 📦 **Create Resource Group**
```sh
az group create --name kube-rg1 --location idsouth
```
**Explanation:** Creates a new resource group in the specified location.

---

## 🖥️ **Deploy Kubernetes Cluster**
```sh
az group deployment create --template-file azuredeploy.json --parameters azuredeploy.parameters.json --resource-group "kube-rg1" --name "deploy1st"
```
**Explanation:** Deploys the Kubernetes cluster using the specified template and parameters.

---

This document provides detailed explanations and steps for deploying AKS Engine on Azure Stack Hub with Azure CLI.
