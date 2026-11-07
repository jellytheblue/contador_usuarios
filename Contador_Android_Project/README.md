# Contador de usuarios — Android

Versión táctil en Kivy del contador original de Python/Tkinter.

## Incluye

- Grupos: crear, seleccionar, renombrar y eliminar.
- Usuarios/personajes: crear, renombrar, activar/desactivar y eliminar.
- Recuento global de activos y total.
- Reinicio automático de todos los interruptores entre 0,5 y 720 horas.
- Guardado automático en el almacenamiento privado de la aplicación.
- Importación y exportación de respaldos JSON con el selector nativo de Android.
- Interfaz vertical adaptable a pantallas Android.

## Compilar el APK en Windows

Buildozer necesita Linux. En Windows 10/11, usa WSL2 con Ubuntu. La documentación oficial de Kivy y Buildozer describe este flujo.

1. Instala WSL2 y Ubuntu desde PowerShell (como administrador):

   ```powershell
   wsl --install -d Ubuntu
   ```

2. Abre Ubuntu y ejecuta:

   ```bash
   sudo apt update
   sudo apt install -y git zip unzip openjdk-17-jdk python3-pip python3-venv \
     autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev \
     libtinfo6 cmake libffi-dev libssl-dev automake autopoint gettext
   ```

3. Copia el ZIP desde Windows al sistema Linux de WSL y descomprímelo allí (no compiles desde `/mnt/c`):

   ```bash
   mkdir -p ~/proyectos/contador
   cp /mnt/c/Users/TU_USUARIO/Downloads/Contador_Android_Project.zip ~/proyectos/contador/
   cd ~/proyectos/contador
   unzip Contador_Android_Project.zip
   cd Contador_Android_Project
   ```

   Sustituye `TU_USUARIO` por tu carpeta de usuario de Windows.

4. Instala Buildozer dentro de un entorno virtual y compila:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip buildozer
   buildozer -v android debug
   ```

5. El APK aparecerá en `bin/`. Copia el archivo a Windows o al teléfono e instálalo.

La primera compilación descarga Android SDK/NDK y puede tardar bastante; las siguientes reutilizan esas herramientas.

## Datos y compatibilidad

La app guarda `contador_usuarios_datos.json` dentro del almacenamiento privado asignado por Android. El formato JSON conserva las claves y estructura de la versión Windows, pero Android mantiene su propia copia aislada. Para migrar los datos iniciales, copia el `contador_usuarios_datos.json` del PC al teléfono (por ejemplo, a Descargas) y, desde el botón **Copia JSON → Importar copia JSON**, selecciónalo. También puedes exportar una copia desde el teléfono. No se solicita permiso amplio de almacenamiento: se usa el selector de documentos de Android.

El temporizador comprueba el vencimiento al estar abierta y al volver a primer plano. Si Android suspende o cierra la app, el reinicio pendiente se procesa al reabrirla, manteniendo la cadencia prevista. No se instala un servicio persistente en segundo plano, por lo que no se garantiza que el contador visual continúe ejecutándose mientras Android mantiene la app cerrada.

## Ejecutar en escritorio para probar la interfaz

```bash
python -m pip install kivy==2.3.1
python main.py
```
