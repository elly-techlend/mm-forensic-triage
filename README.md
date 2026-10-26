# Mobile Money Forensic Triage Tool (UG)

A lightweight, open-source digital forensics tool designed to extract mobile money evidence (SMS & Call Logs) from unrooted Android devices. 

## 🎯 The Problem
In Uganda, mobile money fraud is rising. However, modern Android devices (Android 12+) block traditional ADB database extraction, making it difficult for law enforcement to retrieve evidence without expensive commercial tools.

## 🛠️ The Solution
This tool bypasses SELinux restrictions using **Android Content Providers** to safely extract SMS and Call Logs. It ensures forensic integrity by generating **SHA-256 hashes** for all evidence and provides a beautiful web-based dashboard for intelligence analysis.

## ✨ Features
- **Zero Root Access:** Extracts data via standard USB Debugging (ADB).
- **Chain of Custody:** Automatically hashes all raw evidence files (SHA-256).
- **Intelligence Dashboard:** Beautiful dark-mode Flask interface with filtering by Telecom, Amount, Type, and Date.
- **Court-Admissible PDF:** Generates professional PDF reports for law enforcement.

## 🚀 Installation & Usage
1. Install dependencies: `pip install flask reportlab`
2. Connect the Android device (ensure USB Debugging is enabled).
3. Run the extraction: `python3 triage.py --case CASE-ID`
4. Start the dashboard: `python3 reports/app.py`
5. Open `http://127.0.0.1:5000` in your browser.

## ⚠️ Disclaimer
This tool is for educational and legitimate forensic investigation purposes only. Ensure you have legal authorization before extracting data from any device.