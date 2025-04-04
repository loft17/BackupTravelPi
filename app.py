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


APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(APP_DIR, "config.json")
USER = getpass.getuser()
MEDIA_BASE = f"/media/{USER}"
LOG_DIR = os.path.join(APP_DIR, "logs")

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

HISTORY_PATH = os.path.join(APP_DIR, SETTINGS["history_file"])

ORIGEN = ""
DESTINO = ""
unidades = []
progress_win = None
progress_label = None
progress_var = None
fullscreen_active = SETTINGS.get("fullscreen", False)

root = tk.Tk()
root.geometry("480x320")
root.title("Backup SD")
root.configure(bg="#1e1e1e")
if fullscreen_active:
    root.attributes("-fullscreen", True)

# Función para guardar configuración
def save_settings():
    with open(CONFIG_FILE, "w") as f:
        json.dump(SETTINGS, f, indent=4)

# Función para cambiar entre pantalla completa
def toggle_fullscreen():
    global fullscreen_active
    fullscreen_active = not fullscreen_active
    SETTINGS["fullscreen"] = fullscreen_active
    save_settings()
    root.attributes("-fullscreen", fullscreen_active)

# Función para abrir la ventana de configuración
def abrir_configuracion():
    config_win = tk.Toplevel()
    config_win.title("Configuración")
    config_win.geometry("360x320")
    config_win.configure(bg="#1e1e1e")

    var_checksum = tk.BooleanVar(value=SETTINGS["verify_checksums"])
    var_reintentos = tk.IntVar(value=SETTINGS["max_retries"])
    var_intervalo = tk.IntVar(value=SETTINGS["auto_refresh_interval"])
    var_historial = tk.StringVar(value=SETTINGS["history_file"])
    var_fullscreen = tk.BooleanVar(value=SETTINGS.get("fullscreen", False))

    tk.Checkbutton(config_win, text="Verificar Checksums", variable=var_checksum,
                   bg="#1e1e1e", fg="white", selectcolor="#1e1e1e").pack(pady=4)
    tk.Label(config_win, text="Reintentos:", bg="#1e1e1e", fg="white").pack()
    tk.Entry(config_win, textvariable=var_reintentos).pack(pady=2)
    tk.Label(config_win, text="Refresco (ms):", bg="#1e1e1e", fg="white").pack()
    tk.Entry(config_win, textvariable=var_intervalo).pack(pady=2)
    tk.Label(config_win, text="Historial:", bg="#1e1e1e", fg="white").pack()
    tk.Entry(config_win, textvariable=var_historial, width=30).pack(pady=2)
    tk.Checkbutton(config_win, text="Pantalla Completa", variable=var_fullscreen,
                   bg="#1e1e1e", fg="white", selectcolor="#1e1e1e").pack(pady=4)

    def guardar_config():
        SETTINGS["verify_checksums"] = var_checksum.get()
        SETTINGS["max_retries"] = var_reintentos.get()
        SETTINGS["auto_refresh_interval"] = var_intervalo.get()
        SETTINGS["history_file"] = var_historial.get()
        SETTINGS["fullscreen"] = var_fullscreen.get()
        save_settings()
        messagebox.showinfo("Configuración", "Cambios guardados. Reinicia para aplicar.")
        config_win.destroy()

    # Guardar automáticamente los cambios sin necesidad de un botón "Guardar"
    SETTINGS["verify_checksums"] = var_checksum.get()
    SETTINGS["max_retries"] = var_reintentos.get()
    SETTINGS["auto_refresh_interval"] = var_intervalo.get()
    SETTINGS["history_file"] = var_historial.get()
    SETTINGS["fullscreen"] = var_fullscreen.get()
    save_settings()

# Función para listar las unidades conectadas
def listar_unidades():
    try:
        return [os.path.join(MEDIA_BASE, d) for d in os.listdir(MEDIA_BASE) if os.path.ismount(os.path.join(MEDIA_BASE, d))]
    except:
        return []

# Función para refrescar las unidades
def refrescar_unidades():
    global unidades
    unidades = listar_unidades()
    update_info()
    root.after(SETTINGS["auto_refresh_interval"], refrescar_unidades)

# Función para manejar la selección de origen y destino
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

# Función para manejar la selección de una unidad
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

# Función para obtener la información de uso de disco
def get_info(path):
    try:
        usage = shutil.disk_usage(path)
        return f"Libre: {usage.free // (1024**2)} MB | Usado: {usage.used // (1024**2)} MB"
    except:
        return ""

# Función para actualizar la información del origen y destino
def update_info():
    origen_label.config(text=get_info(ORIGEN))
    destino_label.config(text=get_info(DESTINO))

# Función para comprobar las unidades
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

# Función para mostrar el historial
def mostrar_historial():
    if not os.path.exists(HISTORY_PATH):
        messagebox.showinfo("Historial", "No hay historial disponible todavía.")
        return

    hist_win = tk.Toplevel()
    hist_win.title("Historial")
    hist_win.geometry("640x300")  # Aumenté el tamaño para más columnas
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

# Función para comprobar el espacio antes de comenzar el backup
def comprobar_espacio():
    try:
        space_left = shutil.disk_usage(DESTINO).free // (1024**2)  # en MB
        if space_left < 100:  # Si el espacio disponible es menor a 100 MB
            if not messagebox.askyesno("Espacio insuficiente", f"Quedan solo {space_left}MB disponibles en el destino. ¿Deseas continuar?"):
                return False
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Error al comprobar el espacio disponible en el destino: {e}")
        return False

# Función para actualizar el progreso
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

# Función para mostrar la ventana de progreso
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

# Función para ejecutar el backup
def ejecutar_backup_thread():
    mostrar_ventana_progreso()
    fecha_log = time.strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(LOG_DIR, f"log_{fecha_log}.txt")
    resumen = backup_files(ORIGEN, DESTINO, log_file, "last_checksums.txt", update_progress)
    progress_win.destroy()
    mostrar_resumen(resumen, log_file)

# Función para ejecutar el backup
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

# Funciones de log y apagado
def ver_log():
    os.system(f"xdg-open '{LOG_DIR}' &")

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

# Menú de la aplicación
menubar = tk.Menu(root)

# Sección "Menu" - Acciones principales relacionadas con las unidades
menu = tk.Menu(menubar, tearoff=0)
menu.add_command(label="Refrescar unidades", command=refrescar_unidades)
menu.add_command(label="Verificar dispositivos", command=comprobar_unidades)
menubar.add_cascade(label="Menu", menu=menu)

# Sección "Logs" - Acciones para manejar los logs
logs = tk.Menu(menubar, tearoff=0)
logs.add_command(label="Historial", command=mostrar_historial)
logs.add_command(label="Ver log", command=ver_log)
menubar.add_cascade(label="Logs", menu=logs)

# Sección "Sistema" - Opciones de sistema como pantalla completa y apagado
sistema = tk.Menu(menubar, tearoff=0)
sistema.add_command(label="Pantalla completa", command=toggle_fullscreen)
sistema.add_command(label="Apagar", command=apagar)
menubar.add_cascade(label="Sistema", menu=sistema)

root.config(menu=menubar)

# Botones de origen y destino
btn_origen = tk.Button(root, text="Seleccionar origen", width=30, height=2, bg="#444", fg="white", font=("Arial", 12), command=lambda: abrir_selector("Selecciona origen", set_origen))
btn_origen.place(x=70, y=20)

origen_label = tk.Label(root, text="", fg="white", bg="#1e1e1e", font=("Arial", 10))
origen_label.place(x=70, y=70)

btn_destino = tk.Button(root, text="Seleccionar destino", width=30, height=2, bg="#444", fg="white", font=("Arial", 12), command=lambda: abrir_selector("Selecciona destino", set_destino))
btn_destino.place(x=70, y=100)

destino_label = tk.Label(root, text="", fg="white", bg="#1e1e1e", font=("Arial", 10))
destino_label.place(x=70, y=150)

ip_label = tk.Label(root, text=f"IP HOTSPOT: {obtener_ip_wlan0()}", fg="white", bg="#1e1e1e", font=("Arial", 10))
ip_label.place(x=20, y=270)


# Botón de ejecutar backup
tk.Button(root, text="Hacer Backup", command=ejecutar_backup, width=30, height=2, bg="#28a745", fg="white", font=("Arial", 12)).place(x=70, y=200)

# Refrescar unidades cada cierto intervalo
refrescar_unidades()
root.mainloop()
