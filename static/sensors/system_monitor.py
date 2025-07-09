import psutil
import socket

def get_cpu_usage():
    """Get CPU usage as a percentage."""
    return psutil.cpu_percent(interval=1)

def get_ram_usage():
    """Get RAM usage as a percentage."""
    return psutil.virtual_memory().percent

def get_storage_usage():
    """Get storage usage as a percentage."""
    return psutil.disk_usage('/').percent

def get_network_status():
    """Get network connection status and IP address."""
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return {
            "connected": True,
            "ip_address": ip_address
        }
    except Exception:
        return {
            "connected": False,
            "ip_address": "N/A"
        }