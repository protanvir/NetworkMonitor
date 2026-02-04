# Network Monitor

A comprehensive network monitoring solution built with Python (Flask) and Bootstrap 5. This application monitors the status (Online/Offline) of network devices via ICMP ping, organizes them by category and location, and sends email and WhatsApp alerts when devices go offline.

## Features

-   **Real-time Monitoring**: continuous background monitoring of device connectivity.
-   **Dashboard**:
    -   **Grouped View**: Devices organized by Category (e.g., Routers, Switches, Cameras).
    -   **Collapsible Sections**: Toggle visibility of device groups.
    -   **Visual Indicators**: Color-coded badges for Online/Offline status.
    -   **Dark/Light Mode**: Toggleable theme for visual comfort.
-   **Admin Management**:
    -   Manage **Categories** with custom Bootstrap Icons.
    -   Manage **Locations**.
    -   Edit Device details (Name, IP, Category, Location).
-   **Alerts**: 
    -   **Email**: Notifications via SMTP (configured for Office 365, adaptable to others).
    -   **WhatsApp**: Messages via WhatsApp Cloud API.
    -   **Configurable Recipients**: Manage Alert Email and WhatsApp Number directly from the Admin Dashboard.
-   **Dockerized**: Fully containerized for easy deployment.

## Prerequisites

-   **Python 3.9+** (for local execution)
-   **Docker & Docker Compose** (for containerized execution)

## Installation

### Option 1: Docker (Recommended)

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd NetworkMonitor/netmonitor
    ```

2.  Configure the environment:
    -   Rename `.env.example` to `.env` (or create one).
    -   Update the settings (see [Configuration](#configuration)).

3.  Build and Run:
    ```bash
    docker-compose up -d --build
    ```

4.  Access the dashboard at `http://localhost:9000`.

### Option 2: Local Python Setup

1.  install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2.  Configure environment variables in `.env`.

3.  Run the application:
    ```bash
    python app.py
    ```

## Configuration

Create a `.env` file in the root directory with the following variables:

```ini
# Database
DB_PATH=devices.db

# Email Alerts (Office 365 Example)
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USER=your-email@domain.com
SMTP_PASS=your-password
ALERT_EMAIL=recipient@domain.com  # Optional default, can be overridden in Admin

# WhatsApp Alerts
WA_API_KEY=your-api-key
WA_INSTANCE_ID=your-instance-id
WA_RECIPIENT=1234567890  # Optional default, can be overridden in Admin
```

## Usage

1.  **Add Devices**: Click "Add Device" on the dashboard. Enter Name, IP, and assign a Category/Location.
2.  **Manage Categories**: Go to "Admin" to create new categories (e.g., "Server", "Printer") and assign icons (e.g., `bi-printer`).
3.  **Configure Alerts**: In the Admin section, use the "Notification Settings" verify or update the Alert Email and WhatsApp Number.
4.  **Monitor**: The dashboard updates automatically. If a device goes offline, alerts are triggered (via Email and WhatsApp).

## License

[MIT](LICENSE)
