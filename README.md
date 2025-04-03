# BackupTravelPi
Este proyecto permite realizar copias de seguridad de archivos desde una unidad de almacenamiento  (por ejemplo, una tarjeta SD) a otro destino (por ejemplo, un disco duro o una unidad USB). La  aplicación cuenta con una interfaz gráfica fácil de usar y varias funciones útiles, como la  verificación de integridad mediante checksums, la verificación del espacio en disco antes de hacer  la copia, y un historial detallado de las copias realizadas.



# Requisitos
- Python 3.x
- Tkinter (para la interfaz gráfica)
- Paquetes adicionales como shutil, hashlib, os, time, csv, json


## Paquetes necesarios
Este proyecto utiliza algunos paquetes externos que deben ser instalados previamente. Para instalarlos, ejecuta el siguiente comando:
```bash
pip install -r requirements.txt
```

El archivo requirements.txt debe contener:
```ini
watchdog==2.1.7
```


## Requisitos de Sistema
- Sistema Operativo: Linux (Aunque puede funcionar en otros sistemas operativos con ajustes menores).
- Tkinter: La mayoría de las distribuciones de Python ya incluyen Tkinter, pero si no lo tienes instalado, puedes instalarlo con:
```bash
apt-get install python3-tk
```



# Estructura del Proyecto
```folder
/backup-sd
    ├── app.py                # Script principal para la aplicación de backup
    ├── backup_logic.py       # Lógica de backup (manejo de archivos, verificación de checksums)
    ├── config.json           # Archivo de configuración con los ajustes del proyecto
    ├── lang.json             # Archivo de traducción para múltiples idiomas (opcional)
    ├── logs/                 # Carpeta donde se guardan los logs del backup
    ├── last_checksums.txt    # Archivo de último checksum calculado
    ├── backup_history.csv    # Archivo CSV donde se guarda el historial de backups
    └── requirements.txt      # Lista de paquetes necesarios para ejecutar el proyecto
```

# Instalación
1. Clona este repositorio:
```bash
git clone https://github.com/loft17/QuickBackup.git
```

2. Accede al directorio del proyecto:
```bash
cd QuickBackup
```

3. Instala los paquetes necesarios:
```bash
pip install -r requirements.txt
```

4. Asegúrate de que tienes Tkinter instalado. Si no lo tienes, instálalo usando:
```bash
apt-get install python3-tk
```


# Uso
Configuración Inicial:

- **1. Configuración Inicial:**
    - Abre el archivo `config.json` para ajustar los parámetros predeterminados, como el número de reintentos, la frecuencia de actualización, y el nombre del archivo de historial.
    - Si no tienes el archivo de historial, se generará automáticamente al realizar el primer backup.

- **2. Ejecutar la Aplicación:**
    - Ejecuta la aplicación principal con:
    ```bash
    python app.py
    ```

- **3. Interfaz Gráfica:**
    - Botón de "Seleccionar origen": Elige la unidad de almacenamiento de origen (por ejemplo, la tarjeta SD).
    - Botón de "Seleccionar destino": Elige el destino donde se guardarán los archivos (por ejemplo, un disco duro o unidad USB).
    - Botón de "Hacer Backup": Realiza el backup de los archivos seleccionados desde el origen al destino.

- **4. Historial de Backups:**
    - Todos los backups realizados se guardan en un archivo `backup_history.csv`, que puedes consultar desde el menú **Logs > Historial**.
        
- **5. Verificación de Checksums:**
    - La aplicación verifica los checksums de los archivos copiados para asegurarse de que los archivos no estén corruptos.
        
- **6. Monitoreo de Unidades Conectadas:**
    - La aplicación detecta automáticamente las unidades conectadas o desconectadas en el sistema y actualiza la lista de unidades disponibles sin necesidad de refrescar manualmente.



# Funcionalidades Avanzadas
- Espacio en Disco: Antes de realizar el backup, la aplicación verifica si hay suficiente espacio en el destino. Si no es suficiente, te pedirá confirmación para continuar.
- Configuración Automática: Los cambios realizados en la configuración de la aplicación se guardan automáticamente sin necesidad de presionar un botón adicional.
- Detección Automática de Unidades: Usando watchdog, el sistema detecta automáticamente la conexión o desconexión de dispositivos de almacenamiento y actualiza la interfaz de usuario.


# Archivos de Configuración
### `config.json`
Este archivo contiene la configuración predeterminada de la aplicación, como el intervalo de refresco, los reintentos para verificar los archivos y el nombre del archivo de historial.

### `backup_history.csv`
Este archivo mantiene un historial de todos los backups realizados, incluyendo la fecha, el número de archivos copiados, errores encontrados, destino y duración del backup.

onfiguración para auto-montaje USB enXFCE
Vamos desde el menú: Aplicaciones -> Configuración -> Dispositivos y soportes extraíbles.
Marcamos las opciones como se muestran en la imagen:
- Montar los dispositivos extraíbles al conectarlos.
- Montar los soportes extraíbles al insertarlos.

![image](https://github.com/user-attachments/assets/9c34041c-e881-4ac8-817b-eaf9dd0ffe06)

