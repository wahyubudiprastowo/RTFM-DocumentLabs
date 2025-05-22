
# 📘 ASSIGN LICENSE E3 / E5 WITH POWERSHELL AND USERLIST

Tutorial ini menjelaskan langkah-langkah Assign License E3/E5 Atau Lainnya berdasarkan SKU menggunakan PowerShell dan Microsoft Graph SDK. Cocok digunakan saat akan mengganti lisensi lama yang akan kedaluwarsa.

---

## 1️⃣ Install dan Login ke PowerShell Microsoft Graph

### 📥 Install Microsoft Graph Module
```powershell
Install-Module Microsoft.Graph -Scope CurrentUser -Force -AllowClobber
```

### 📦 Import Modul yang Dibutuhkan
```powershell
Import-Module Microsoft.Graph
Import-Module Microsoft.Graph.Users
Import-Module Microsoft.Graph.DirectoryObjects
Import-Module Microsoft.Graph.Users.Actions
```

> ⚠️ Hindari memuat semua modul Graph jika menggunakan PowerShell 5. Gunakan PowerShell 7 untuk stabilitas maksimal.

### 🔐 Login ke Microsoft Graph
```powershell
Connect-MgGraph -Scopes "User.Read.All", "Organization.Read.All", "User.ReadWrite.All", "Directory.ReadWrite.All"
```

Akan muncul pop-up untuk login. Gunakan akun **Global Administrator**.

---

## 2️⃣ Cek Lisensi (SKU) yang Tersedia

Jalankan perintah berikut:
```powershell
Get-MgSubscribedSku | Select-Object SkuPartNumber, SkuId, ConsumedUnits
```

Contoh hasil:
```
SkuPartNumber               SkuId                                  ConsumedUnits
-------------               -----                                  --------------
ENTERPRISEPACK              11111111-2222-3333-4444-555555555555   292
ENTERPRISEPACKWITHOUTTEAMS  aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee   0
```

- **ENTERPRISEPACK** → Lisensi lama (E3)
- **ENTERPRISEPACKWITHOUTTEAMS** → Lisensi baru (E3 tanpa Teams)

> 💡 Salin nilai `SkuId` untuk lisensi baru dan masukkan ke script di bawah.

---

## 3️⃣ Siapkan File CSV User

Buat file bernama `userlist.csv` dengan isi sebagai berikut:

```csv
UserPrincipalName
abdul.rosyid@xxxx.co.id
abroham@xxxx.co.id
adityono@xxxx.co.id
...
```

> Simpan file di lokasi yang mudah dijangkau, misalnya: `C:\Scripts\userlist.csv`

---

## 4️⃣ Buat Script PowerShell Assign Lisensi

Buat file `assign-license.ps1` dan isi dengan kode berikut:

```powershell
# Koneksi ke Microsoft Graph
Connect-MgGraph -Scopes "User.ReadWrite.All", "Directory.ReadWrite.All"

# ID SKU baru (ganti sesuai hasil dari Get-MgSubscribedSku)
$newSkuId = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" # <-- Ganti dengan SKU ID lisensi E3 No Teams

# Import data user dari CSV
$users = Import-Csv -Path "C:\Scripts\userlist.csv"

foreach ($user in $users) {
    try {
        Write-Host "Assigning license to: $($user.UserPrincipalName)"

        Set-MgUserLicense -UserId $user.UserPrincipalName `
            -AddLicenses @(@{SkuId = $newSkuId}) `
            -RemoveLicenses @()

        Write-Host "✅ Success: $($user.UserPrincipalName)" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Failed for $($user.UserPrincipalName): $_" -ForegroundColor Red
    }
}
```

---

## 5️⃣ Jalankan Script

Buka PowerShell 7, lalu jalankan:
```powershell
cd C:\Scripts
.\assign-license.ps1
```

---

## ✅ Tips Tambahan
- Pastikan jumlah lisensi baru cukup untuk semua user.
- Gunakan `Export-Csv` jika ingin merekam hasil ke log.
- Jalankan di waktu off-peak untuk meminimalkan gangguan.

---

## 📝 Lisensi
Script ini disediakan bebas pakai untuk keperluan internal organisasi. Gunakan dengan tanggung jawab sesuai hak akses admin masing-masing.
