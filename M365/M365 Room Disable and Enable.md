
# Microsoft 365 Room Mailbox Management Guide

## Method 1: Using Microsoft 365 Admin Center (GUI)

### **Disable Room Mailbox:**
1. **Log in** to the [Microsoft 365 Admin Center](https://admin.microsoft.com).
2. In the left navigation pane, go to:
   - **Resources > Rooms & Equipment**.
3. **Find the room** (e.g., *CEO Room*) and select it by clicking the checkbox.
4. Click **Edit resource mailbox details** from the toolbar.
5. In the **Settings** page:
   - **Uncheck** “Allow scheduling” to stop bookings.
   - Set **Booking Delegates** to require manual approval or block automatic reservations.
6. Alternatively, click **“Delete resource mailbox”** to remove the room completely.

### **Enable Room Mailbox:**
1. Log in to the [Microsoft 365 Admin Center](https://admin.microsoft.com).
2. Go to:
   - **Resources > Rooms & Equipment**.
3. Find the **disabled or hidden room** under *Inactive users* or in the *Exchange Admin Center*.
4. Select the room, click **Edit resource mailbox details**, and:
   - **Enable** “Allow scheduling” for the room.
   - Configure **Booking policies** if needed.
5. **Save** your changes.

---

## Method 2: Using PowerShell (Recommended for Bulk or Automation)

### **Step 1: Connect to Exchange Online PowerShell:**
```powershell
Connect-ExchangeOnline
```

### **Disable the Room Mailbox:**
- **Fully Disable Mailbox:**
```powershell
Disable-Mailbox -Identity "ceo.room@domain.co.id"
```
- **Disable Auto-Booking (Keep Mailbox Active):**
```powershell
Set-CalendarProcessing -Identity "ceo.room@domain.co.id" -AutomateProcessing None
```

### **Enable the Room Mailbox:**
- **Re-enable Mailbox (If Previously Disabled):**
```powershell
Enable-Mailbox -Identity "ceo.room@domain.co.id"
```
- **Restore Auto-Booking Settings:**
```powershell
Set-CalendarProcessing -Identity "ceo.room@domain.co.id" -AutomateProcessing AutoAccept
```

### **Check Room Mailbox Status:**
```powershell
Get-Mailbox -Identity "ceo.room@domain.co.id" | Format-Table DisplayName,Alias,HiddenFromAddressListsEnabled
```

---

## Method 3: Hide or Show Room in Address Lists Without Deletion

### **Hide Room from Global Address List (GAL):**
```powershell
Set-Mailbox -Identity "ceo.room@domain.co.id" -HiddenFromAddressListsEnabled $true
```

### **Show Room in Global Address List (Unhide):**
```powershell
Set-Mailbox -Identity "ceo.room@domain.co.id" -HiddenFromAddressListsEnabled $false
```

---

## 📝 **Summary:**
- Use **Admin Center** for quick, manual management.
- Use **PowerShell** for advanced, automated, and bulk operations.
- **PowerShell** offers better control over settings like *auto-booking*, *GAL visibility*, and *bulk room management*. 
- Always **verify changes** using `Get-Mailbox` commands.
