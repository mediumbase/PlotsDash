import socket

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