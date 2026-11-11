# Tools Hub ⚡

Panel central y gestor unificado para todas tus herramientas locales de trabajo. Diseñado con una interfaz web sobria, minimalista y ultrarrápida, permite ejecutar y abrir cualquier herramienta en una nueva pestaña del navegador con un solo clic.

---

## 🚀 Inicio Rápido

Si acabas de clonar este repositorio en una máquina nueva, descarga todas las herramientas independientes con:

```bash
./setup.sh
```

Para iniciar el panel central y abrirlo automáticamente en tu navegador predeterminado:

```bash
./start-hub.sh
```

El panel estará disponible en: **[http://localhost:7777](http://localhost:7777)**

---

## 🛠️ Herramientas Incluidas (Repositorios Independientes)

| Herramienta | Carpeta / Repo | Puerto | Descripción |
| :--- | :--- | :--- | :--- |
| **YouTube & Local Transcript** | [`transcript/`](https://github.com/RedoRojo/transcript) | `8001` | Transcripción de videos de YouTube y archivos locales con Whisper y exportación multiformato (TXT, PDF, SRT, MD). |
| **PDF Toolbox** | [`pdf-toolbox/`](https://github.com/RedoRojo/pdf-toolbox) | `8002` | OCR de libros escaneados, compresión, unión, división, rotación y conversión limpia de artículos web a PDF. |
| **Link to QR** | [`qr-code/`](https://github.com/RedoRojo/qr-code) | `8003` | Generador instantáneo de códigos QR con copia a portapapeles y descargas PNG/SVG. |
| **Kindle Toolbox** | [`kindle-toolbox/`](https://github.com/RedoRojo/kindle-toolbox) | `8004` | Conversor de artículos web y PDFs a libros EPUB3 reflowable optimizados para pantallas E-Ink y Kindle. |

Cada herramienta vive en su propio repositorio de Git y corre de manera aislada en su subdirectorio con su entorno específico (`.venv` o Miniconda) sin colisión de puertos.

---

## ⚡ ¿Cómo Funciona el Lanzador de 1 Clic?

1. En el panel principal (`http://localhost:7777`), haz clic en **"Iniciar y Abrir"** en la tarjeta de la herramienta deseada.
2. El navegador abrirá una nueva pestaña. Si el servidor aún está inactivo, el Hub lo iniciará automáticamente en segundo plano.
3. La pestaña detecta en tiempo real cuando el puerto del servidor está listo y redirige instantáneamente a la herramienta.
4. Si la herramienta ya estaba activa, se abrirá inmediatamente sin tiempos de espera.
5. Puedes detener o reiniciar cualquier herramienta activa directamente desde los botones de su tarjeta.

---

## ➕ Cómo Añadir una Nueva Herramienta

El Hub incluye **auto-detección automática**. Para integrar una nueva herramienta:

1. Crea o clona una carpeta en este directorio (ej. `mi-herramienta/`).
2. Agrega dentro su script de inicio `run.sh` o archivo `app.py` (y opcionalmente un `tool.json`).
3. *(Opcional)* Declara sus metadatos y puerto en `tools.json`:

```json
{
  "id": "mi-herramienta",
  "name": "Mi Nueva Herramienta",
  "description": "Breve descripción de lo que hace.",
  "category": "Utilidades",
  "icon": "code",
  "dir": "mi-herramienta",
  "command": "./run.sh",
  "port": 8005,
  "health_path": "/"
}
```

Al refrescar el panel (tecla `R` o botón Refrescar), aparecerá automáticamente lista para usarse.

---

## ⚙️ Estructura del Proyecto

```text
tools/
├── hub.py              # Servidor HTTP y gestor de procesos (Python standard library)
├── start-hub.sh        # Script ejecutable de inicio y apertura de navegador
├── setup.sh            # Script para clonar o actualizar los repositorios de herramientas
├── tools.json          # Registro declarativo de herramientas y puertos
├── static/
│   └── index.html      # Interfaz minimalista (CSS moderno + JS reactivo)
├── transcript/         # Repo independiente: YouTube & Local Transcript (puerto 8001)
├── pdf-toolbox/        # Repo independiente: PDF Toolbox (puerto 8002)
├── qr-code/            # Repo independiente: Link to QR (puerto 8003)
└── kindle-toolbox/     # Repo independiente: Kindle Toolbox (puerto 8004)
```
