
# Enable Microsoft Entra ID Login on Windows Server 2022 VM in Azure

This guide explains how to enable **Microsoft Entra ID** (formerly Azure Active Directory) login on a **Windows Server 2022** VM in Azure. By following these steps, users will be able to authenticate using their Entra ID credentials.

---

## 📌 **Prerequisites**
Before you begin, ensure that you have:
1. ✅ **Azure VM (Windows Server 2022)** – An existing VM running Windows Server 2022.
2. ✅ **Microsoft Entra ID Users** – The users must exist in Microsoft Entra ID (Azure AD).
3. ✅ **Azure AD Login Extension** – Installed on the VM (Azure usually installs it automatically).
4. ✅ **Network Security Groups (NSG) Configured** – Ensure **RDP (port 3389)** is allowed.

---

## 🚀 **Step 1: Enable System-Assigned Managed Identity on the VM**
This step allows the VM to communicate with **Microsoft Entra ID** for authentication.

1. Open **Azure Portal** and go to your **Windows Server 2022 VM**.
2. Under **Settings**, select **Identity**.
3. Under **System assigned**, switch the **Status** to **On** and click **Save**.
4. This allows the VM to register itself with **Microsoft Entra ID**.

---

## 🔑 **Step 2: Assign RBAC Roles for Microsoft Entra ID Login**
To allow specific users to log in to the VM, assign them one of the following **Azure RBAC roles**:
- **Virtual Machine Administrator Login** (for admin access)
- **Virtual Machine User Login** (for standard user access)

### ✅ **Steps to Assign a Role:**
1. In **Azure Portal**, go to your **Windows Server 2022 VM**.
2. Under **Settings**, select **Access control (IAM)**.
3. Click on **+ Add** → **Add role assignment**.
4. In the **Role** dropdown, select:
   - 🔹 **Virtual Machine Administrator Login** (for admin access)
   - 🔹 **Virtual Machine User Login** (for regular user access)
5. Under **Members**, click **+ Select members** and add the Entra ID users/groups.
6. Click **Review + assign** to confirm.

---

## 🔧 **Step 3: Install and Enable the Azure AD Login Extension**
Most **Windows Server VMs** automatically have the **Azure AD Login extension**, but if it’s missing, install it manually.

### ✅ **How to Install the Extension:**
1. Open **Azure Portal** and go to your **VM**.
2. Under **Settings**, select **Extensions + applications**.
3. Click **+ Add**, then select **Azure AD Login for Windows**.
4. Follow the on-screen steps to complete installation.

---

## ⚙️ **Step 4: Enable Entra ID Login on Windows Server 2022**
After configuring Azure, you need to enable **Microsoft Entra ID login** on the VM.

### ✅ **Check if the VM is Joined to Microsoft Entra ID**
1. Open **PowerShell** as **Administrator** on the VM.
2. Run the following command:

   ```powershell
   dsregcmd /status
   ```
