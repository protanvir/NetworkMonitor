Project Specification: Dockerized Network Monitor with Office 365 Alerts
1. Executive Summary
Goal: Build a lightweight, containerized Python web application to monitor local network devices via ICMP ping. Core Workflow: The app serves a dashboard showing device status. A background process checks connectivity every 30 seconds. If a device goes offline, the system sends an email alert via Office 365.

2. Technology Stack
Backend Framework: Python 3.9+ using Flask.

Database: SQLite (File-based, persistent).

Frontend: HTML5 with Bootstrap 5 (CDN).

Network Protocol: ICMP (Ping) using the pythonping library.

Email Protocol: SMTP with STARTTLS (Office 365 specific).

Deployment: Docker and Docker Compose.

3. Architecture & Data Model
Database Schema (SQLite)
Table Name: devices | Column Name | Type | Description | | :--- | :--- | :--- | | id | INTEGER | Primary Key, Auto-increment | | name | TEXT | Human-readable name (e.g., "Main Router") | | ip | TEXT | IP Address (e.g., "192.168.1.1") | | status | TEXT | Current state: "Online", "Offline", or "Pending" | | last_checked | TEXT | Timestamp of the last ping attempt |

Project Directory Structure
The agent must generate the following file structure exactly:

/netmonitor
├── app.py                 # Main Flask application, DB logic, and Background Thread
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker image configuration
├── docker-compose.yml     # Container orchestration and Env Vars
└── templates/
    └── dashboard.html     # Frontend UI with Bootstrap

4. Functional Requirements
A. Backend Logic (app.py)
Threaded Monitor:

Start a daemon thread on app launch (threading.Thread).

Loop forever with a sleep(30) interval.

Iterate through all devices in the DB.

Ping Logic: Use pythonping(ip, count=1, timeout=2).

State Change Detection: Compare the new status with the current status in the DB.

Alert Trigger: IF current_status == "Online" AND new_status == "Offline", call send_email_alert().

Update the DB with the new status and timestamp.

Email Alerting (Office 365):

Function: send_email_alert(device_name, device_ip)

SMTP Config: Use smtp.office365.com on port 587.

Security: strict usage of server.starttls().

Env Vars: Read credentials from os.environ (do not hardcode).

Web Routes:

GET /: Fetch all devices and render dashboard.html.

POST /add: Receive name and ip, insert into DB, redirect to /.

GET /delete/<id>: Delete device by ID, redirect to /.

B. Frontend UI (templates/dashboard.html)
Layout: Use Bootstrap 5 container.

Auto-Refresh: Include <meta http-equiv="refresh" content="30"> to auto-reload status.

Components:

Table: Columns for Name, IP, Status (use Badges: Green for Online, Red for Offline), Last Checked, and a "Delete" button.

Modal: A Bootstrap Modal to add a new device (prevents page navigation).

C. Docker Configuration
1. Dockerfile

Base Image: python:3.9-slim

System Dependencies: Must run apt-get install -y iputils-ping (Critical for pythonping).

Workdir: /app

Command: python app.py

2. docker-compose.yml

Service Name: netmonitor

Restart Policy: unless-stopped

Ports: 5000:5000

Volumes:

./data:/app/data (Map a data folder to persist devices.db).

Environment Variables:

DB_PATH=/app/data/devices.db

SMTP_SERVER=smtp.office365.com

SMTP_PORT=587

SMTP_USER=your_email@example.com

SMTP_PASS=your_app_password

ALERT_EMAIL=admin@example.com

5. Special Instructions for the Agent
Ensure the SQLite database connection handles multi-threading (create a new connection per thread/request).

Include error handling in the SMTP function so the main app does not crash if email fails.

Do not mock the ping function; use the real library.

