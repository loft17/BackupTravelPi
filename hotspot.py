# hotspot.py
import subprocess
import socket
import tkinter.messagebox as messagebox

HOTSPOT_SCRIPT = "/opt/hotspot.sh"

def hotspot_start():
    subprocess.run([HOTSPOT_SCRIPT, "start"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def hotspot_stop():
    subprocess.run([HOTSPOT_SCRIPT, "stop"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def hotspot_status():
    resultado = subprocess.run([HOTSPOT_SCRIPT, "status"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    messagebox.showinfo("Hotspot", resultado.stdout or "Estado desconocido.")

def obtener_estado_hotspot():
    try:
        resultado = subprocess.run([HOTSPOT_SCRIPT, "status"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return "Hotspot activo" in resultado.stdout
    except:
        return False

def obtener_ip_wlan0():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "Sin conexión"
