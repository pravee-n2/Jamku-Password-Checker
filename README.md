# GST Portal Password Verifier

A desktop automation tool built for CA firms to bulk-verify GST portal login credentials — across multiple clients — without manual checking one by one.

Built with Python, PyQt5, and Selenium.

---

## What It Does

CA firms manage GST credentials for multiple clients. This tool:
- Takes a list of client GST usernames and passwords from a CSV/Excel file
- Automatically logs into the GST portal for each client
- Detects whether the password is **working**, **wrong**, or **expired**
- Shows live status in a table as it runs
- Exports the results to Excel

---

## Features

| Feature | Description |
|---|---|
| 📂 Drag & Drop File Upload | Drop a CSV or Excel file directly onto the app |
| 🔄 Live Progress Table | See status updating in real-time for each client |
| 🟢 Running / 🟡 Paused / 🔵 Completed Indicator | Always know what the app is doing |
| ⏸ Pause & Resume | Pause mid-run and resume without losing progress |
| 📤 Export to Excel | Export only the checked results at any point |
| 🔁 Auto Chrome Recovery | If Chrome crashes, the app restarts it automatically |
| 🧠 CAPTCHA Wait Support | App waits while you solve CAPTCHA manually |

---

## Password Status Results

Each client row will show one of these statuses after checking:

| Status | Meaning |
|---|---|
| `Password is working` | Login successful |
| `WRONG password` | Invalid credentials |
| `Password expired` | Login redirected to change password page |

---

## Input File Format

If you are using Jamku app, then you can export your client list by following this step:
Jamku Home --> GST module --> (Scroll below) Config button --> (click on) Export Account List --> Drag and drop the CSV into this app

Your CSV or Excel file **must have these exact column names:**

| Column Name | Description |
|---|---|
| `gstin` | Client's GSTIN number |
| `name` | Client name |
| `portalUserName` | GST portal username |
| `portalPassword` | GST portal password |

**Sample format:**

```
gstin,name,portalUserName,portalPassword
33XXXXX1234Z1ZX,ABC Traders,abc_user,Pass@123
33XXXXX5678Z1ZY,XYZ Pvt Ltd,xyz_user,Pass@456
```

---

## How to Use

**Step 1 — Open the app**
Run `GST_Login_Verifier.exe` (or run the `.py` script if using Python directly)

**Step 2 — Load your file**
Either drag and drop your CSV/Excel file onto the drop zone, or click the drop zone to browse and select the file.

**Step 3 — CAPTCHA**
The GST portal will show a CAPTCHA. Solve it manually in the Chrome window that opens. The app will wait and continue automatically after login.

**Step 4 — Watch live results**
The table updates in real-time. The progress bar and status indicator show how many have been checked.

**Step 5 — Pause if needed**
Click **⏸ Pause** anytime (e.g., if you need to step away). Click **▶ Resume** to continue.

**Step 6 — Export results**
Click **📤 Export Checked** at any point to save the results checked so far to an Excel file.

---

## ⚙️ Requirements (For Running from Python)

```
Python 3.8+
PyQt5
selenium
pandas
openpyxl
webdriver-manager
```

Install all dependencies:
```bash
pip install PyQt5 selenium pandas openpyxl webdriver-manager
```

Also requires **Google Chrome** to be installed on the machine.

---

## Build EXE (For Distribution)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "GST_Login_Verifier" "Final version of Jamku Login.py"
```

Output EXE will be in the `dist/` folder.

---

## Important Notes

- This tool is intended for **CA firms managing their own clients' credentials** with proper authorisation.
- Do **not** run multiple instances simultaneously.
- Keep the Chrome window visible — do not minimise it during CAPTCHA solving.
- The GST portal may occasionally be slow — the app handles this with automatic waits and retries.

---

## Built With

- [Python](https://www.python.org/)
- [PyQt5](https://pypi.org/project/PyQt5/) — Desktop GUI
- [Selenium](https://www.selenium.dev/) — Browser automation
- [Pandas](https://pandas.pydata.org/) — Data handling

---

## Developer

Built for internal use at a Chartered Accountant firm.  
For issues or feature requests, raise a GitHub Issue.
