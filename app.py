import os
import tkinter as tk
from tkinter import ttk, messagebox
import shutil
import getpass
import threading
import time
import csv
import json
from backup_logic import backup_files, SETTINGS
import socket
import subprocess

APP_DIR = os.path.dirname(os.path.abspath(__file__))
# Ya no se utilizará CONFIG_FILE porque no se modificarán los settings desde la app.
USER = getpass.getuser()
MEDIA_BASE = f"/media/{USER}"
LOG_DIR = os.path.join(APP_DIR, "logs")
HOTSPOT_SCRIPT = "/opt/hotspot.sh"

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

HISTORY_PATH = os.path.join(APP_DIR, SETTINGS["history_file"])

ORIGEN = ""
DESTINO = ""
unidades = []
progress_win = None
progress_label = None
progress_var = None
# La variable fullscreen_active se obtiene de SETTINGS y se respeta, sin posibilidad de cambiarla
fullscreen_active = SETTINGS.get("fullscreen", False)

root = tk.Tk()
root.geometry("480x320")
root.title("QuickBackup")
root.configure(bg="#1e1e1e")
if fullscreen_active:
    root.attributes("-fullscreen", True)

# -----------------------------------------------------------------------------
# Funciones de la aplicación (sin opciones para modificar los settings)
# -----------------------------------------------------------------------------

def listar_unidades():
    try:
        return [os.path.join(MEDIA_BASE, d) for d in os.listdir(MEDIA_BASE) if os.path.ismount(os.path.join(MEDIA_BASE, d))]
    except:
        return []

def refrescar_unidades():
    global unidades
    unidades = listar_unidades()
    update_info()
    root.after(SETTINGS["auto_refresh_interval"], refrescar_unidades)

def abrir_selector(titulo, callback):
    ventana = tk.Toplevel(root)
    ventana.title(titulo)
    ventana.geometry("300x300")
    ventana.configure(bg="#1e1e1e")
    for u in unidades:
        nombre = os.path.basename(u)
        b = tk.Button(ventana, text=nombre, width=25, height=3, bg="#444", fg="white", font=("Arial", 14),
                      command=lambda path=u: handle_selection(path, callback, ventana))
        b.pack(pady=5)

def handle_selection(path, callback, ventana):
    global ORIGEN, DESTINO
    if (callback == set_origen and path == DESTINO) or (callback == set_destino and path == ORIGEN):
        messagebox.showwarning("Advertencia", "El origen y destino no pueden ser iguales.")
        return
    callback(path)
    ventana.destroy()

def set_origen(path):
    global ORIGEN
    ORIGEN = path
    btn_origen.config(text=f"ORIGEN: {os.path.basename(path)}")
    update_info()

def set_destino(path):
    global DESTINO
    DESTINO = path
    btn_destino.config(text=f"DESTINO: {os.path.basename(path)}")
    update_info()

def get_info(path):
    try:
        usage = shutil.disk_usage(path)
        return f"Libre: {usage.free // (1024**2)} MB | Usado: {usage.used // (1024**2)} MB"
    except:
        return ""

def update_info():
    origen_label.config(text=get_info(ORIGEN))
    destino_label.config(text=get_info(DESTINO))

def comprobar_unidades():
    msg = ""
    for path in [ORIGEN, DESTINO]:
        if not path:
            continue
        try:
            usage = shutil.disk_usage(path)
            msg += f"{os.path.basename(path)}\nLibre: {usage.free // (1024**2)} MB\n\n"
        except Exception as e:
            msg += f"{os.path.basename(path)}\nError: {e}\n\n"
    messagebox.showinfo("Estado de unidades", msg or "Selecciona origen y destino primero.")

def mostrar_historial():
    if not os.path.exists(HISTORY_PATH):
        messagebox.showinfo("Historial", "No hay historial disponible todavía.")
        return

    hist_win = tk.Toplevel()
    hist_win.title("Historial")
    hist_win.geometry("640x300")
    hist_win.configure(bg="#1e1e1e")

    tree = ttk.Treeview(hist_win, columns=("Fecha", "Archivos", "Copiados", "Errores", "Destino", "Tamaño Total (MB)", "Duración"), show="headings")
    for col in tree["columns"]:
        tree.heading(col, text=col)
        tree.column(col, width=120)

    tree.pack(fill="both", expand=True)

    with open(HISTORY_PATH, newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            tree.insert("", "end", values=row)

def comprobar_espacio():
    try:
        space_left = shutil.disk_usage(DESTINO).free // (1024**2)
        if space_left < 100:
            if not messagebox.askyesno("Espacio insuficiente", f"Quedan solo {space_left}MB disponibles en el destino. ¿Deseas continuar?"):
                return False
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Error al comprobar el espacio disponible en el destino: {e}")
        return False

def update_progress(current, total, filename=""):
    percent = int((current / total) * 100)
    progress_var.set(percent)
    if progress_label:
        progress_label.config(text=f"{current}/{total} ({percent}%)\n{filename}")
    if time_est_label:
        elapsed = time.time() - start_time
        est_total = (elapsed / current) * total if current else 0
        remaining = est_total - elapsed
        mins, secs = divmod(int(remaining), 60)
        time_est_label.config(text=f"Tiempo restante estimado: {mins:02d}:{secs:02d}")

def mostrar_ventana_progreso():
    global progress_win, progress_label, progress_var, time_est_label, start_time
    progress_var = tk.IntVar()
    progress_win = tk.Toplevel(root)
    progress_win.title("Progreso de Backup")
    progress_win.geometry("400x120")
    progress_win.configure(bg="#1e1e1e")
    ttk.Progressbar(progress_win, variable=progress_var, maximum=100, length=380).pack(pady=5)
    progress_label = tk.Label(progress_win, text="", bg="#1e1e1e", fg="white", font=("Arial", 10))
    progress_label.pack()
    time_est_label = tk.Label(progress_win, text="", bg="#1e1e1e", fg="white", font=("Arial", 9))
    time_est_label.pack()
    start_time = time.time()

def ejecutar_backup_thread():
    mostrar_ventana_progreso()
    fecha_log = time.strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(LOG_DIR, f"log_{fecha_log}.txt")
    resumen = backup_files(ORIGEN, DESTINO, log_file, "last_checksums.txt", update_progress)
    progress_win.destroy()
    mostrar_resumen(resumen, log_file)

def ejecutar_backup():
    if not ORIGEN or not DESTINO:
        messagebox.showerror("Error", "Selecciona origen y destino.")
        return
    if ORIGEN == DESTINO:
        messagebox.showerror("Error", "El origen y destino no pueden ser el mismo.")
        return

    if not comprobar_espacio():
        return

    threading.Thread(target=ejecutar_backup_thread).start()

def ver_log():
    os.system(f"xdg-open '{LOG_DIR}' &")

def cerrar_aplicacion():
    root.destroy()

def apagar():
    os.system("sudo shutdown now")

def obtener_ip_wlan0():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "Sin conexión"

def hotspot_start():
    subprocess.run([HOTSPOT_SCRIPT, "start"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    actualizar_estado_hotspot()

def hotspot_stop():
    subprocess.run([HOTSPOT_SCRIPT, "stop"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    actualizar_estado_hotspot()

def hotspot_status():
    resultado = subprocess.run([HOTSPOT_SCRIPT, "status"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    messagebox.showinfo("Hotspot", resultado.stdout or "Estado desconocido.")

def obtener_estado_hotspot():
    try:
        resultado = subprocess.run([HOTSPOT_SCRIPT, "status"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if "Hotspot activo" in resultado.stdout:
            return True
        else:
            return False
    except:
        return False

def mostrar_resumen(resumen, log_file):
    msg = resumen + "\n\nVer log para más detalles."
    if messagebox.askyesno("Backup completado", msg + "\n¿Deseas ver el log?"):
        os.system(f"xdg-open '{log_file}' &")

# Menú táctil flotante sin opciones de configuración
def mostrar_menu_tactil():
    overlay = tk.Toplevel(root)
    overlay.attributes("-alpha", 0.5)
    overlay.overrideredirect(True)
    overlay.geometry(f"{root.winfo_width()}x{root.winfo_height()}+{root.winfo_x()}+{root.winfo_y()}")
    overlay.configure(bg="black")

    close_button = tk.Button(overlay, text="X", command=overlay.destroy, bg="#333", fg="white", font=("Arial", 12))
    close_button.place(relx=0.98, rely=0.02, anchor="ne")

    menu_frame = tk.Frame(overlay, bg="#1e1e1e")
    menu_frame.place(relx=0.5, rely=0.5, anchor="center")

    def cargar_menu_principal():
        for widget in menu_frame.winfo_children():
            widget.destroy()
        opciones_principal = [
            ("Hotspot", cargar_submenu_hotspot),
            ("Sistema", cargar_submenu_sistema),
        ]
        for texto, accion in opciones_principal:
            btn = tk.Button(menu_frame, text=texto, width=25, height=2, bg="#333", fg="white",
                            font=("Arial", 12), command=accion)
            btn.pack(pady=5)

    def cargar_submenu_hotspot():
        for widget in menu_frame.winfo_children():
            widget.destroy()
        opciones_hotspot = [
            ("Iniciar Hotspot", hotspot_start),
            ("Detener Hotspot", hotspot_stop),
            ("Estado Hotspot", hotspot_status),
            ("Volver", cargar_menu_principal)
        ]
        for texto, accion in opciones_hotspot:
            btn = tk.Button(menu_frame, text=texto, width=25, height=2, bg="#333", fg="white",
                            font=("Arial", 12), command=accion)
            btn.pack(pady=5)

    def cargar_submenu_sistema():
        for widget in menu_frame.winfo_children():
            widget.destroy()
        opciones_sistema = [
            ("Apagar", apagar),
            ("Cerrar", cerrar_aplicacion),
            ("Ver Log", ver_log),
            ("Volver", cargar_menu_principal)
        ]
        for texto, accion in opciones_sistema:
            if texto in ["Apagar", "Cerrar"]:
                btn = tk.Button(menu_frame, text=texto, width=25, height=2, bg="#333", fg="white",
                                font=("Arial", 12),
                                command=lambda a=accion: (a(), overlay.destroy()))
            else:
                btn = tk.Button(menu_frame, text=texto, width=25, height=2, bg="#333", fg="white",
                                font=("Arial", 12), command=accion)
            btn.pack(pady=5)

    cargar_menu_principal()

# -----------------------------------------------------------------------------
# Configuración de la interfaz
# -----------------------------------------------------------------------------

btn_origen = tk.Button(root, text="Seleccionar origen", width=30, height=2, bg="#444", fg="white",
                       font=("Arial", 12), command=lambda: abrir_selector("Selecciona origen", set_origen))
btn_origen.place(x=70, y=20)

origen_label = tk.Label(root, text="", fg="white", bg="#1e1e1e", font=("Arial", 10))
origen_label.place(x=70, y=70)

btn_destino = tk.Button(root, text="Seleccionar destino", width=30, height=2, bg="#444", fg="white",
                        font=("Arial", 12), command=lambda: abrir_selector("Selecciona destino", set_destino))
btn_destino.place(x=70, y=100)

destino_label = tk.Label(root, text="", fg="white", bg="#1e1e1e", font=("Arial", 10))
destino_label.place(x=70, y=150)

btn_opciones = tk.Button(root, text="☰ Opciones", bg="#444", fg="white", font=("Arial", 12),
                         width=12, height=2, command=mostrar_menu_tactil)
btn_opciones.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

hotspot_status_label = tk.Label(root, text="", fg="white", bg="#1e1e1e", font=("Arial", 10))
hotspot_status_label.place(x=70, y=250)

def actualizar_estado_hotspot():
    activo = obtener_estado_hotspot()
    if activo:
        ssid = "PiTravel"
        ip = "10.0.0.1"
        hotspot_status_label.config(text=f"Hotspot activo: {ssid} - {ip}", fg="lime")
    else:
        hotspot_status_label.config(text="Hotspot inactivo", fg="red")
    root.after(10000, actualizar_estado_hotspot)

actualizar_estado_hotspot()

tk.Button(root, text="Hacer Backup", command=ejecutar_backup, width=30, height=2,
          bg="#28a745", fg="white", font=("Arial", 12)).place(x=70, y=200)

refrescar_unidades()
root.mainloop()
