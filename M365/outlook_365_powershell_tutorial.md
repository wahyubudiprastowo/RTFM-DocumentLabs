
# Manage Outlook 365 Online with PowerShell (Detailed Tutorial)

This guide provides a detailed tutorial with explanations for managing Outlook 365 (Exchange Online) using PowerShell commands.

---

## 📌 **Install PowerShell 7 on Windows**
1. Install PowerShell 7 on your Windows system.
2. Run PowerShell 7 as an Administrator.

---

## 📄 **Install and Verify Exchange Online Module**
```sh
Install-Module -Name ExchangeOnlineManagement
```
**Explanation:** Installs the Exchange Online Management module.

```sh
Find-Module ExchangeOnlineManagement -AllVersions -AllowPrerelease
Get-InstalledModule ExchangeOnlineManagement | Format-List Name,Version,InstalledLocation
```
**Explanation:** Checks for all versions of the module and displays installed module details.

---

## 🔐 **Connect to Exchange Online**
```sh
Import-Module ExchangeOnlineManagement
Connect-ExchangeOnline -UserPrincipalName <your_email>
```
**Explanation:** Imports the module and connects to Exchange Online using your principal name.

---

## 📦 **Manage Mailboxes and Archives**
- Fetch mailbox statistics:
```sh
$exomailboxsize = (Get-EXOMailbox | Get-EXOMailboxStatistics)
```
- Sort mailbox sizes in descending order:
```sh
$exomailboxsize | select DisplayName, TotalItemSize | sort -Property TotalItemSize -Descending
```
**Explanation:** Retrieves and sorts mailbox statistics.

- Check archive mailbox size:
```sh
$archivemailboxsize = (Get-EXOMailbox -Archive | Get-EXOMailboxStatistics -Archive)
$archivemailboxsize | select DisplayName, TotalItemSize | sort -Property TotalItemSize -Descending
```

---

## 🛡️ **Retention Policies and Mailbox Archives**
- Create new retention tags:
```sh
New-RetentionPolicyTag -Name "365 Day Archive" -Type All -RetentionEnabled $true -AgeLimitForRetention 365 -RetentionAction MoveToArchive
```
**Explanation:** Creates a policy to archive after 365 days.

- Apply policies:
```sh
Set-RetentionPolicy "Default MRM Policy" -RetentionPolicyTagLinks "365 Day Archive"
Set-Mailbox -Identity "<user mailbox>" -RetentionPolicy "Default MRM Policy"
```
- Enable mailbox archive for users:
```sh
Enable-Mailbox -Identity <user mailbox> -Archive
```
**Explanation:** Enables archiving for selected or all users.

---

## 🛠️ **Manage Mailbox Quotas**
- Change mailbox quotas for multiple users:
```sh
Get-Mailbox | Set-Mailbox -ProhibitSendQuota 50GB -ProhibitSendReceiveQuota 55GB -IssueWarningQuota 45GB
```
- Check quota:
```sh
Get-Mailbox <User ID> | Select *quota
```
**Explanation:** Adjusts mailbox size limits.

---

## 📧 **Send As or On Behalf Permissions**
- Grant send on behalf to a group:
```sh
Set-DistributionGroup -Identity <group_email> -GrantSendOnBehalfTo @{add="<user_email>"}
```
- Add send as permission:
```sh
Add-RecipientPermission "<group_email>" -AccessRights SendAs -Trustee "<user_email>"
```

---

This document provides detailed explanations and steps for managing Outlook 365 using PowerShell.
