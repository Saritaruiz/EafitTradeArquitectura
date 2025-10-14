# Eafit Trade 

## 📋 Descripción del Proyecto
Actualmente, los estudiantes y personal de EAFIT carecen de una fuente confiable y organizada de información sobre los vendedores en el campus. Esto dificulta encontrar opciones de compra, comparar precios y acceder a productos específicos. Nuestra aplicación resuelve esto proporcionando un catálogo digital con información detallada de los vendedores, mejorando la conexión entre compradores y vendedores.

## 🛠️ Tecnologías Utilizadas

- **Backend:** Django 5.1.6
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap
- **Base de datos:** SQLite (desarrollo), PostgreSQL (recomendado para producción)
- **Autenticación:** Sistema de autenticación de Django
- **Manejo de imágenes:** Pillow
- **Integración IA:** Google Gemini API para búsqueda inteligente
- **Despliegue:** Gunicorn, Whitenoise

## 🚀 Instrucciones de Instalación y Ejecución

### Prerrequisitos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Git

### 1. Crear y preparar el directorio del proyecto

```bash
# Crear un directorio para el proyecto (puedes usar el nombre que prefieras)
mkdir EafitTrade1
cd EafitTrade1

# Clonar el repositorio
git clone https://github.com/Saritaruiz/EafitTradeArquitectura.git

# Entrar al directorio del proyecto clonado
cd EafitTrade
```

### 2. Configurar el entorno virtual

```bash
# Crear el entorno virtual
python -m venv env

# Activar el entorno virtual en Windows
env\Scripts\activate

# Activar el entorno virtual en macOS/Linux
source env/bin/activate
```

### 3. Instalar dependencias
Con el entorno virtual activado (deberías ver `(env)` al inicio de la línea de comandos):

```bash
# Actualizar pip a la última versión
python -m pip install --upgrade pip

# Instalar las dependencias del proyecto desde requirements.txt
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
Crear un archivo `.env` en el directorio raíz del proyecto con las siguientes variables:

```
GEMINI_API_KEY=tu_clave_de_api_google_gemini
```

### 5. Ejecutar migraciones de la base de datos

```bash
python manage.py migrate
```

### 6. Crear un superusuario (opcional)

```bash
python manage.py createsuperuser
```

### 7. Ejecutar el servidor de desarrollo

```bash
python manage.py runserver
```

La aplicación estará disponible en: http://127.0.0.1:8000/

## 📂 Estructura del Proyecto

```
EafitTrade/
├── eafit_trade/          # Configuración principal del proyecto
│   ├── settings.py       # Configuración de Django
│   ├── urls.py           # URLs principales
│   └── ...
├── products/             # Aplicación para gestión de productos
│   ├── models.py         # Modelos de datos
│   ├── views.py          # Lógica de vistas
│   ├── templates/        # Plantillas HTML
│   └── ...
├── seller_profiles/      # Aplicación para gestión de perfiles de vendedores
│   ├── models.py         # Modelos de datos
│   ├── views.py          # Lógica de vistas
│   ├── templates/        # Plantillas HTML
│   └── ...
├── media/                # Archivos subidos por usuarios
├── staticfiles/          # Archivos estáticos recopilados
├── requirements.txt      # Dependencias del proyecto
└── manage.py             # Script de gestión de Django
```

## 🔧 Solución de problemas comunes

### Error: "No such file or directory: 'requirements.txt'"
Si recibes este error, verifica que:
1. Estés en el directorio correcto (debe ser el directorio `EafitTrade` que contiene el archivo `requirements.txt`)
2. El archivo `requirements.txt` exista en tu directorio actual
3. Usa el comando `dir` (Windows) o `ls` (macOS/Linux) para verificar los archivos en tu directorio actual

### Error: "No module named 'django'"
Si recibes este error:
1. Verifica que el entorno virtual esté activado (deberías ver `(env)` al inicio de tu línea de comandos)
2. Asegúrate de haber instalado las dependencias correctamente con `pip install -r requirements.txt`

### Error: "manage.py not found"
Si recibes este error:
1. Asegúrate de estar en el directorio correcto (debe ser el directorio `EafitTrade` que contiene el archivo `manage.py`)
2. Usa `dir` o `ls` para verificar que `manage.py` existe en tu directorio actual

## 👥 Contribuir al Proyecto

1. Crea un fork del repositorio
2. Crea una rama para tu funcionalidad (`git checkout -b feature/nueva-funcionalidad`)
3. Realiza tus cambios y haz commits (`git commit -am 'Añade nueva funcionalidad'`)
4. Sube tus cambios (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## 📜 Licencia

Este proyecto está licenciado bajo la licencia MIT - ver el archivo LICENSE para más detalles.

## 📞 Contacto

Si tienes preguntas sobre el proyecto, puedes contactar a:
- Email: info@eafittrade.com
- GitHub: [camiloarbr](https://github.com/camiloarbr/EafitTrade)

## Usando ngrok con EafitTrade

Para exponer tu servidor local de desarrollo a internet y permitir que otros usuarios accedan a tu instancia de EafitTrade, puedes utilizar ngrok. Esto es útil para pruebas, demostraciones o desarrollo colaborativo.

### Instalación de ngrok

1. Descarga ngrok desde [https://ngrok.com/download](https://ngrok.com/download) o instálalo usando pyngrok:
```bash
pip install pyngrok
```

2. Si descargaste el ejecutable directamente:
   - Descomprime el archivo
   - Coloca el ejecutable en una ubicación accesible

### Configuración del token de autenticación de ngrok

1. Registra una cuenta gratuita en [https://ngrok.com/signup](https://ngrok.com/signup)

2. Una vez registrado, ve a la [página de configuración de autenticación](https://dashboard.ngrok.com/get-started/your-authtoken) para obtener tu token de autenticación

3. Configura el token en ngrok usando el comando:
```bash
.\ngrok.exe config add-authtoken tu_token_de_ngrok
```

4. En Windows, si usas PowerShell, puede que el operador `&&` no funcione. Usa comandos separados en lugar de concatenarlos.

### Método 1: Uso de ngrok desde la línea de comandos

1. Inicia tu servidor Django en el puerto 8000:
```bash
python manage.py runserver
```

2. En otra terminal, ejecuta ngrok para crear un túnel al puerto 8000:
```bash
.\ngrok.exe http 8000  # En Windows, usa la ruta completa si es necesario
```

3. Ngrok te proporcionará una URL pública (por ejemplo, `https://a1b2c3d4.ngrok.io`) que puedes compartir.

### Método 2: Uso de ngrok integrado con Django

EafitTrade incluye una integración con pyngrok que permite iniciar ngrok directamente desde la aplicación:

1. Asegúrate de que pyngrok esté instalado y configurado con tu token de autenticación:
```bash
pip install pyngrok
python -c "from pyngrok import ngrok; ngrok.set_auth_token('tu_token_de_ngrok')"
```

2. Inicia el servidor Django:
```bash
python manage.py runserver
```

3. Visita la URL `/start-ngrok/` desde tu navegador (debes estar autenticado como administrador).

4. Se mostrará un mensaje con la URL pública de ngrok que puedes compartir.

### Consideraciones importantes

- La configuración ya incluye los dominios necesarios en `ALLOWED_HOSTS` para permitir conexiones desde ngrok.
- Las URLs de ngrok cambian cada vez que reinicias ngrok, a menos que tengas una cuenta de pago.
- Para servicios de producción, considera usar un hosting real en lugar de ngrok.
- Recuerda que exponer tu servidor local a Internet puede representar riesgos de seguridad.

