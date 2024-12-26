import time
from datetime import datetime
import os
from prometheus_client import start_http_server, Gauge, CollectorRegistry
from unas import UNASPro
from dotenv import load_dotenv

registry = CollectorRegistry()

device_name = Gauge('device_name', 'Device Name', registry=registry, labelnames=['name'])
cpu_usage = Gauge('cpu_usage', 'CPU Usage (%)', registry=registry)
cpu_temperture = Gauge('cpu_temperature', 'CPU Temperture (°C)', registry=registry)
memory_free = Gauge('memory_free', 'Memory Free', registry=registry)
memory_used = Gauge('memory_used', 'Memory Used', registry=registry)
memory_total = Gauge('memory_total', 'Memory Total', registry=registry)
memory_usage = Gauge('memory_usage', 'Memory Usage (%)', registry=registry)
firmware = Gauge('firmware', 'Firmware Status', registry=registry, labelnames=['version'])
drive_temperature = Gauge('drive_temperature', 'Drive Temperature (°C)', registry=registry, labelnames=['slot'])
drive_healthy = Gauge('drive_healthy', 'Drive Healthy', registry=registry, labelnames=['slot'])
drive_size = Gauge('drive_size', 'Drive Size', registry=registry, labelnames=['slot'])
total_storage = Gauge('total_storage', 'Total Storage', registry=registry)
used_storage = Gauge('used_storage', 'Used Storage', registry=registry)
free_storage = Gauge('free_storage', 'Free Storage', registry=registry)
share = Gauge('share', 'Share Size', registry=registry, labelnames=['name'])
start_time = Gauge('start_time', 'Start Time', registry=registry)
network_interface = Gauge('network_interface', 'Network Interface', registry=registry, labelnames=['interface'])

def update_metrics():
    try:
        system_info = device.get_system_info()
    except Exception as e:
        print(f'Error: {e}')
        return
    
    cpu_usage_pct = system_info['cpu']['currentload'] * 100
    cpu_temp_c = system_info['cpu']['temperature']
    memory = system_info['memory']
    memory_free_mb = memory['free'] / 1024
    memory_total_mb = memory['total'] / 1024
    memory_used_mb = memory_total_mb - memory_free_mb
    memory_usage_percent = memory_used_mb / memory_total_mb * 100
    firmware_version = system_info['firmwareVersion']
    latest_firmware = device.get_latest_firmware()
    is_latest_firmware = firmware_version == latest_firmware
    device_name_val = system_info['name']
    storage = device.get_storage_info()
    drives = storage['diskInfo']['slots']
    total_storage_kb = storage['totalQuota']
    used_storage_kb = storage['usage']['system']
    startup_time = datetime.fromisoformat(system_info['startupTime']).timestamp()

    personal_shares = device.get_personal_drives()
    shared_shares = device.get_shared_drives()

    network_interfaces = device.get_network_interfaces()

    for s in personal_shares:
        name = f'{s['user']['firstName']} {s['user']['lastName']} (Personal)'
        share.labels(name=name).set(s['usage'])

    for s in shared_shares:
        name = f'{s['name']}'
        share.labels(name=name).set(s['usage'])

    for interface in network_interfaces:
        network_interface.labels(interface=interface['interface']).set(interface['connected'])
    
    cpu_usage.set(cpu_usage_pct)
    cpu_temperture.set(cpu_temp_c)
    memory_free.set(memory_free_mb)
    memory_total.set(memory_total_mb)
    memory_used.set(memory_used_mb)
    memory_usage.set(memory_usage_percent)
    firmware.labels(version=firmware_version).set(is_latest_firmware)
    device_name.labels(name=device_name_val).set(-1)
    total_storage.set(total_storage_kb)
    used_storage.set(used_storage_kb)
    free_storage.set(total_storage_kb - used_storage_kb)
    start_time.set(startup_time)

    for drive in drives:
        if drive['state'] == 'nodisk':
            continue
        slot = drive['slot']
        drive_temperature.labels(slot=slot).set(drive['temperature'])
        drive_healthy.labels(slot=slot).set(drive['healthy'] == 'good')
        drive_size.labels(slot=slot).set(drive['size'])

if __name__ == '__main__':
    load_dotenv()

    PORT = int(os.getenv("PORT", "8000"))
    hostname = os.getenv("DEVICE_HOSTNAME")
    username = os.getenv("DEVICE_USERNAME")
    password = os.getenv("DEVICE_PASSWORD")

    if not hostname or not username or not password:
        missing = []
        if not hostname:
            missing.append("DEVICE_HOSTNAME")
        if not username:
            missing.append("DEVICE_USERNAME")
        if not password:
            missing.append("DEVICE_PASSWORD")
        print(f"Missing environment variables: {', '.join(missing)}")
        exit(1)
    
    start_http_server(PORT, registry=registry)
    print(f"Server started on port {PORT}")

    try:
        device = UNASPro(hostname, username, password)
    except Exception as e:
        print(f'Error: {e}')
        exit(1)

    while True:
        logged_in = device.is_logged_in()
        if not logged_in:
            device.login()
        update_metrics()
        time.sleep(5)