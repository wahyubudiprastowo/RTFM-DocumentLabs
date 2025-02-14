
# Custom S2S Connection to Azure Stack (Detailed Tutorial)

This guide provides detailed steps with explanations for creating a Site-to-Site (S2S) connection to Azure Stack using PowerShell.

---

## 📌 **Add Azure Stack Environment**
```sh
Add-AzureRMEnvironment -Name "AzureStackUser" -ArmEndpoint "https://management.idwest.hybridcloud.id"
```
**Explanation:** Adds a custom Azure Stack environment with the specified ARM endpoint.

---

## 🔐 **Set Tenant Name and Authenticate**
```sh
$AuthEndpoint = (Get-AzureRmEnvironment -Name "AzureStackUser").ActiveDirectoryAuthority.TrimEnd('/')
$AADTenantName = "riamanugrahsemesta.onmicrosoft.com"
$TenantId = (invoke-restmethod "$($AuthEndpoint)/$($AADTenantName)/.well-known/openid-configuration").issuer.TrimEnd('/').Split('/')[-1]
```
**Explanation:** Sets the authentication endpoint, tenant name, and retrieves the tenant ID.

---

## 🔑 **Sign in to Azure Stack**
```sh
Add-AzureRmAccount -EnvironmentName "AzureStackUser" -TenantId $TenantId
Connect-AzureRmAccount
```
**Explanation:** Connects to the Azure Stack environment using the specified tenant ID.

---

## 🌐 **Create S2S Connection**
- Define IPSec Policy:
```sh
$ipsecpolicy6 = New-AzureRmIpsecPolicy -IkeEncryption AES256 -IkeIntegrity MD5 -DhGroup DHGroup2 -IpsecEncryption AES256 -IpsecIntegrity MD5 -SALifeTimeSeconds 28800 -SADataSizeKilobytes 102400000
```
**Explanation:** Creates a new IPSec policy with specified encryption, integrity, and lifetime settings.

- Get Network Gateway and Local Network Gateway:
```sh
$RG1 = "RIAM-RGRP-0001"
$vnet1gw = Get-AzureRmVirtualNetworkGateway -Name "RIAM-VNG-0001" -ResourceGroupName $RG1
$lng6 = Get-AzureRmLocalNetworkGateway -Name "RIAM-LNG-0001" -ResourceGroupName $RG1
```
**Explanation:** Retrieves the virtual and local network gateways.

- Create the Connection:
```sh
New-AzureRmVirtualNetworkGatewayConnection -Name "Test" -ResourceGroupName $RG1 -VirtualNetworkGateway1 $vnet1gw -LocalNetworkGateway2 $lng6 -Location "idwest" -ConnectionType IPsec -IpsecPolicies $ipsecpolicy6 -SharedKey 'T3lkomAzur3R1am'
```
**Explanation:** Establishes the S2S connection using the specified gateways, location, IPSec policy, and shared key.

---

**Note:** For more details on supported parameters, visit [Azure Stack VPN S2S Documentation](https://docs.microsoft.com/en-us/azure-stack/user/azure-stack-vpn-s2s).
