import os
import sqlite3
import threading
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, redirect, url_for
from pythonping import ping
from dotenv import load_dotenv

import requests

load_dotenv()

app = Flask(__name__)

# Configuration
DB_PATH = os.environ.get('DB_PATH', 'devices.db')
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.office365.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASS = os.environ.get('SMTP_PASS', '')
ALERT_EMAIL = os.environ.get('ALERT_EMAIL', '')

# WhatsApp Configuration
WA_API_KEY = os.environ.get('WA_API_KEY', '')
WA_INSTANCE_ID = os.environ.get('WA_INSTANCE_ID', '')
WA_RECIPIENT = os.environ.get('WA_RECIPIENT', '')

# Ensure data directory exists
os.makedirs(os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else '.', exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('PRAGMA foreign_keys = ON')
    
    # Create categories table (updated schema)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            icon TEXT
        )
    ''')

    # Create locations table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')

    # Create devices table (updated schema)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            ip TEXT NOT NULL,
            category_id INTEGER,
            location_id INTEGER,
            status TEXT DEFAULT 'Pending',
            last_checked TEXT DEFAULT 'Never',
            FOREIGN KEY (category_id) REFERENCES categories (id),
            FOREIGN KEY (location_id) REFERENCES locations (id)
        )
    ''')
    
    # Migration: Add columns if they don't exist (for existing DBs)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(devices)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if 'category_id' not in columns:
        conn.execute('ALTER TABLE devices ADD COLUMN category_id INTEGER REFERENCES categories(id)')
    if 'location_id' not in columns:
        conn.execute('ALTER TABLE devices ADD COLUMN location_id INTEGER REFERENCES locations(id)')

    cursor.execute("PRAGMA table_info(categories)")
    cat_columns = [info[1] for info in cursor.fetchall()]
    if 'icon' not in cat_columns:
        conn.execute('ALTER TABLE categories ADD COLUMN icon TEXT')

    conn.commit()
    conn.close()

def send_email_alert(device_name, device_ip):
    if not SMTP_USER or not SMTP_PASS or not ALERT_EMAIL:
        print("SMTP credentials not set, skipping email alert.")
        return

    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = ALERT_EMAIL
        msg['Subject'] = f"ALERT: Device {device_name} is Offline"

        body = f"Device Name: {device_name}\nIP Address: {device_ip}\nStatus: Offline\nTime: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, ALERT_EMAIL, msg.as_string())
        server.quit()
        print(f"Alert email sent for {device_name} ({device_ip})")
    except Exception as e:
        print(f"Failed to send email alert: {e}")

def send_whatsapp_alert(device_name, device_ip):
    if not WA_API_KEY or not WA_INSTANCE_ID or not WA_RECIPIENT:
        print("WhatsApp credentials not set, skipping WhatsApp alert.")
        return

    try:
        url = "https://api.wacloud.app/send-message"
        headers = {
            "API-Key": WA_API_KEY
        }
        payload = {
            "recipient": WA_RECIPIENT,
            "content": f"ALERT: Device {device_name} ({device_ip}) is Offline at {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "instance_id": WA_INSTANCE_ID
        }

        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200 and response.json().get('success'):
             print(f"WhatsApp alert sent for {device_name} ({device_ip})")
        else:
             print(f"Failed to send WhatsApp alert. Status: {response.status_code}, Response: {response.text}")

    except Exception as e:
        print(f"Failed to send WhatsApp alert: {e}")

def monitor_devices():
    print("Starting background monitor thread...")
    while True:
        try:
            conn = get_db_connection()
            devices = conn.execute('SELECT * FROM devices').fetchall()
            
            for device in devices:
                device_id = device['id']
                name = device['name']
                ip = device['ip']
                current_status = device['status']
                
                # Ping logic
                try:
                    # pythonping returns a ResponseList, we check success
                    # timeout is in seconds
                    response = ping(ip, count=1, timeout=2)
                    new_status = "Online" if response.success() else "Offline"
                except Exception as e:
                    print(f"Ping error for {ip}: {e}")
                    new_status = "Offline"
                
                # Check for status change trigger
                if current_status == "Online" and new_status == "Offline":
                    send_email_alert(name, ip)
                    send_whatsapp_alert(name, ip)
                
                # Update DB
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                conn.execute('UPDATE devices SET status = ?, last_checked = ? WHERE id = ?', 
                             (new_status, timestamp, device_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error in monitor loop: {e}")
        
        time.sleep(30)

@app.route('/')
def index():
    conn = get_db_connection()
    
    # Fetch all devices with their category and location info
    query = '''
        SELECT d.*, c.name as category, c.icon as category_icon, l.name as location 
        FROM devices d
        LEFT JOIN categories c ON d.category_id = c.id
        LEFT JOIN locations l ON d.location_id = l.id
        ORDER BY d.name
    '''
    devices = conn.execute(query).fetchall()
    
    # Fetch all categories to ensure we display even empty ones (optional, but good for structure)
    categories_db = conn.execute('SELECT * FROM categories ORDER BY name').fetchall()
    locations = conn.execute('SELECT * FROM locations').fetchall()
    conn.close()

    # Group devices by Category
    # Structure: [ {'name': 'Router', 'icon': 'bi-router', 'devices': [...]}, ... ]
    
    categories_dict = {}
    
    # Initialize groups from defined categories
    for cat in categories_db:
        categories_dict[cat['name']] = {
            'name': cat['name'],
            'icon': cat['icon'],
            'id': cat['id'],
            'devices': []
        }
    
    # Container for uncategorized devices
    uncategorized = {
        'name': 'Uncategorized',
        'icon': 'bi-question-circle',
        'id': None,
        'devices': []
    }
    
    for device in devices:
        cat_name = device['category']
        if cat_name and cat_name in categories_dict:
            categories_dict[cat_name]['devices'].append(device)
        else:
            uncategorized['devices'].append(device)
            
    # Convert to list for display
    # Filter out empty categories if desired, or keep them. Let's keep them if requested, 
    # but maybe only show if they have devices or user prefers to see all sections.
    # For now, let's show all defined categories + Uncategorized if it has items.
    
    grouped_devices = list(categories_dict.values())
    
    # Only add Uncategorized if there are devices in it
    if uncategorized['devices']:
        grouped_devices.append(uncategorized)

    return render_template('dashboard.html', 
                           grouped_devices=grouped_devices, 
                           categories=categories_db, 
                           locations=locations)

@app.route('/admin')
def admin():
    conn = get_db_connection()
    categories = conn.execute('SELECT * FROM categories').fetchall()
    locations = conn.execute('SELECT * FROM locations').fetchall()
    conn.close()
    return render_template('admin.html', categories=categories, locations=locations)

@app.route('/admin/category/add', methods=['POST'])
def add_category():
    name = request.form['name']
    icon = request.form.get('icon') # Get icon class
    if name:
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO categories (name, icon) VALUES (?, ?)', (name, icon))
            conn.commit()
        except sqlite3.IntegrityError:
            pass # Ignore duplicates or handle error
        conn.close()
    return redirect(url_for('admin'))

@app.route('/admin/category/delete/<int:id>')
def delete_category(id):
    conn = get_db_connection()
    # Optional: Handle devices linked to this category? Set to NULL?
    conn.execute('UPDATE devices SET category_id = NULL WHERE category_id = ?', (id,))
    conn.execute('DELETE FROM categories WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/admin/category/edit/<int:id>', methods=['POST'])
def edit_category(id):
    name = request.form['name']
    icon = request.form.get('icon')
    if name:
        conn = get_db_connection()
        try:
            conn.execute('UPDATE categories SET name = ?, icon = ? WHERE id = ?', (name, icon, id))
            conn.commit()
        except sqlite3.IntegrityError:
            pass # Ignore duplicates
        conn.close()
    return redirect(url_for('admin'))

@app.route('/admin/location/add', methods=['POST'])
def add_location():
    name = request.form['name']
    if name:
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO locations (name) VALUES (?)', (name,))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        conn.close()
    return redirect(url_for('admin'))

@app.route('/admin/location/delete/<int:id>')
def delete_location(id):
    conn = get_db_connection()
    conn.execute('UPDATE devices SET location_id = NULL WHERE location_id = ?', (id,))
    conn.execute('DELETE FROM locations WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/admin/location/edit/<int:id>', methods=['POST'])
def edit_location(id):
    name = request.form['name']
    if name:
        conn = get_db_connection()
        try:
            conn.execute('UPDATE locations SET name = ? WHERE id = ?', (name, id))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        conn.close()
    return redirect(url_for('admin'))

@app.route('/add', methods=['POST'])
def add_device():
    name = request.form['name']
    ip = request.form['ip']
    category_id = request.form.get('category_id') # Can be None/Empty
    location_id = request.form.get('location_id')

    # Convert empty strings to None
    if category_id == "": category_id = None
    if location_id == "": location_id = None
    
    if name and ip:
        conn = get_db_connection()
        conn.execute('INSERT INTO devices (name, ip, category_id, location_id) VALUES (?, ?, ?, ?)', 
                     (name, ip, category_id, location_id))
        conn.commit()
        conn.close()
        
    return redirect(url_for('admin'))

@app.route('/edit/<int:id>', methods=['POST'])
def edit_device(id):
    name = request.form['name']
    ip = request.form['ip']
    category_id = request.form.get('category_id')
    location_id = request.form.get('location_id')

    if category_id == "": category_id = None
    if location_id == "": location_id = None
    
    conn = get_db_connection()
    conn.execute('''
        UPDATE devices 
        SET name = ?, ip = ?, category_id = ?, location_id = ? 
        WHERE id = ?
    ''', (name, ip, category_id, location_id, id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_device(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM devices WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    # Start monitor thread
    monitor_thread = threading.Thread(target=monitor_devices, daemon=True)
    monitor_thread.start()
    
    app.run(host='0.0.0.0', port=5000)
