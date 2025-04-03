import os
import time
import hashlib
import shutil
import csv
from datetime import datetime

SETTINGS = {
    "verify_checksums": True,
    "max_retries": 3,
    "auto_refresh_interval": 5000,
    "history_file": "backup_history.csv",
    "fullscreen": False,
    "lang": "es"
}

APP_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(APP_DIR, "logs")
CHECKSUM_PATH = os.path.join(APP_DIR, "last_checksums.txt")

if not os.path.exists(LOG_PATH):
    os.makedirs(LOG_PATH)

# === FUNCIONES ===
def calculate_checksum(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def get_files_to_copy(src_dir):
    file_list = []
    for root, _, files in os.walk(src_dir):
        for file in files:
            file_list.append(os.path.join(root, file))
    return file_list

def write_history(fecha, total, copiados, errores, destino, total_size, duracion):
    with open(os.path.join(APP_DIR, SETTINGS["history_file"]), "a") as f:
        writer = csv.writer(f)
        writer.writerow([fecha, total, copiados, errores, destino, total_size / (1024 ** 2), round(duracion, 2)])


def backup_files(src, dst, log_path, checksum_path, update_progress=None):
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fecha_folder = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst_folder = os.path.join(dst, f"backup_{fecha_folder}")
    os.makedirs(dst_folder, exist_ok=True)
 
    full_log = os.path.join(LOG_PATH, f"log_{fecha_folder}.txt")
    os.makedirs(os.path.dirname(full_log), exist_ok=True)

    log = open(full_log, "a")
    checksums = open(checksum_path, "a")

    files = get_files_to_copy(src)
    total = len(files)
    copiados = 0
    errores = []
    total_size = 0  # Variable para almacenar el tamaño total

    log.write(f"--- BACKUP {fecha} ---\n")
    log.write(f"Origen: {src}\nDestino: {dst_folder}\n")
    log.write(f"Verificar checksum: {SETTINGS['verify_checksums']}\n")
    log.write(f"Total archivos encontrados: {total}\n\n")

    for index, src_file in enumerate(files):
        rel_path = os.path.relpath(src_file, src)
        dst_file = os.path.join(dst_folder, rel_path)
        os.makedirs(os.path.dirname(dst_file), exist_ok=True)

        # Calcular el tamaño total de los archivos
        total_size += os.path.getsize(src_file)

        success = False
        for intento in range(1, SETTINGS["max_retries"] + 1):
            try:
                shutil.copy2(src_file, dst_file)

                if SETTINGS["verify_checksums"]:
                    src_hash = calculate_checksum(src_file)
                    dst_hash = calculate_checksum(dst_file)

                    if src_hash != dst_hash:
                        raise ValueError("Checksum mismatch")

                    log.write(f"[OK] {rel_path} - checksum verificado\n")
                else:
                    log.write(f"[OK] {rel_path} - copiado sin verificación\n")

                checksum = calculate_checksum(dst_file)
                checksums.write(f"{checksum}  {rel_path}\n")
                success = True
                break

            except Exception as e:
                if intento == SETTINGS["max_retries"]:
                    log.write(f"[ERROR] {rel_path} - {str(e)}\n")
                    errores.append(rel_path)
                else:
                    log.write(f"[REINTENTO {intento}] {rel_path} - {str(e)}\n")
                time.sleep(1)

        if success:
            copiados += 1

        if update_progress:
            update_progress(index + 1, total, f"{index + 1}/{total} {os.path.basename(src_file)}")

    duracion = time.time() - datetime.strptime(fecha, "%Y-%m-%d %H:%M:%S").timestamp()
    resumen = f"Archivos copiados: {copiados}/{total} | Tamaño total: {total_size / (1024 ** 2):.2f} MB | Tiempo: {int(duracion)}s\n"
    log.write(resumen)
    log.write(f"Errores: {len(errores)}\n")
    log.write("--- FIN BACKUP ---\n")
    log.close()
    checksums.close()

    # Guardar el historial con el número de errores y el tamaño total de la copia
    write_history(fecha, total, copiados, len(errores), dst_folder, total_size, duracion)

    return resumen + ("\nErrores en algunos archivos." if errores else "")
