
# Enable Microsoft Entra ID Login on Windows Server 2022 VM in Azure (Detailed Tutorial)

This guide provides a step-by-step tutorial with explanations for enabling **Microsoft Entra ID** login on **Windows Server 2022 VM in Azure**.

---

## 📌 **Prerequisites**

1. ✅ **Azure VM (Windows Server 2022)** – An existing VM running Windows Server 2022.
2. ✅ **Microsoft Entra ID Users** – Users must exist in Microsoft Entra ID (Azure AD).
3. ✅ **Azure AD Login Extension** – Installed on the VM (automatically installed by Azure for compatible OS).

---

## 🚀 **Step 1: Enable System-Assigned Managed Identity on the VM**

1. Open **Azure Portal** → Go to your **Windows Server 2022 VM**.
2. Under **Settings**, select **Identity**.
3. Turn **System assigned** status **On** → Click **Save**.

---

## 🔑 **Step 2: Assign RBAC Roles for Microsoft Entra ID Login**

1. Go to the VM → **Settings** → **Access control (IAM)**.
2. Click **+ Add** → **Add role assignment**.
3. Choose **Virtual Machine Administrator Login** or **Virtual Machine User Login**.
4. Add members and confirm.

---

## 🔧 **Step 3: Install Azure AD Login Extension (if missing)**

1. Go to **Extensions + applications** on the VM.
2. Add **Azure AD Login for Windows**.

---

## ⚙️ **Step 4: Enable Entra ID Login on VM**

1. Run PowerShell as Admin:

```powershell
dsregcmd /status
```

Ensure **AzureAdJoined** and **EnterpriseJoined** are **YES**.
2. Add Azure AD users to **Remote Desktop Users** group.

---

## 🖥️ **Step 5: Log In Using Microsoft Entra ID**

- Use RDP with username:
  `AzureAD\YourUsername@domain.com`

---

## 🔍 **Troubleshooting Tips**

- **Check NSGs** for RDP port.
- **Verify Azure AD Join** with `dsregcmd /status`.
- **Wait for role propagation** if login fails initially.
