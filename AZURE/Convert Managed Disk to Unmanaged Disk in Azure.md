
# Convert Managed Disk to Unmanaged Disk in Azure (Detailed Tutorial)

This guide provides a step-by-step tutorial with detailed explanations for converting managed disks to unmanaged disks in Azure using PowerShell.

---

## 📌 **Step 1: Prepare Managed Disk for Export**

1. Open **Azure Portal**.
2. Go to **Disks** under your **VM**.
3. Select your **Managed Disk**.
4. Click **Export**.
5. Generate a **SAS URL** (Shared Access Signature).

---

## 📄 **Step 2: Export Managed Disk Using PowerShell**

### **PowerShell Commands:**

```powershell
$AccessSAS = "<your-generated-SAS-URL>"
$destContext = New-AzureStorageContext –StorageAccountName "<storage-account-name>" -StorageAccountKey "<storage-account-key>"
$blobcopy = Start-AzureStorageBlobCopy -AbsoluteUri $AccessSAS -DestContainer "vhds" -DestContext $destContext -DestBlob "<your-vhd-name>.vhd"
while(($blobCopy | Get-AzureStorageBlobCopyState).Status -eq "Pending"){}
```

---

## 🛠️ **Step 3: Verify Exported Disk**

1. Open **Azure Portal**.
2. Go to your **Storage Account**.
3. Select the **vhds** container.
4. Verify that the **.vhd** file exists.

---

## 🌐 **Step 4: Attach Unmanaged Disk to VM**

1. Open **Azure Portal**.
2. Go to **Virtual Machines**.
3. Select your VM or create a new VM.
4. Choose **Use existing disk**.
5. Browse to the **vhds** container and select your exported **.vhd**.
6. Click **Attach** and start the VM.

---

This tutorial guides you through exporting and converting managed disks to unmanaged disks in Azure using PowerShell with clear explanations at each step, including verifying the exported disk and attaching it to a VM.
