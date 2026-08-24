# 🏋️‍♂️ APP GYM — AI Fitness & Nutrition Coach

Aplicación local en Streamlit para llevar el seguimiento de entrenamientos
(por bloques y ejercicios), nutrición flexible (IIFYM), métricas corporales
y recibir auditorías automáticas de un coach basado en la API de Gemini
(Google).

Todos los datos (rutinas, comidas, medidas) se guardan en una base de datos
SQLite **local**, en tu propio ordenador. Nadie más los ve.

## ✨ Funcionalidades

- Registro de entrenamientos por bloques, con múltiples series por ejercicio.
- Auditoría biomecánica automática de la sesión de hoy (IA).
- Registro nutricional: describe una comida en lenguaje natural y la IA
  calcula los macros por ti (o regístrala manualmente / con medidas caseras
  calibradas).
- Coach de flexibilidad nutricional según tus macros restantes del día.
- Dashboard con evolución de peso, cintura y desarrollo muscular.
- Auditoría longitudinal cada 14 días con reajuste de objetivos.

## 🚀 Cómo usarlo

### 1. Clona el repositorio

```bash
git clone https://github.com/tu-usuario/app-gym.git
cd app-gym
```

### 2. Crea un entorno virtual e instala dependencias

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Consigue tu propia API key de Gemini

Necesitas una API key gratuita de Google AI Studio:
👉 https://aistudio.google.com/apikey

### 4. Configura tu API key

Copia el archivo de ejemplo y edítalo con tu clave:

```bash
# Windows:
copy .env.example .env
# Mac/Linux:
cp .env.example .env
```

Abre `.env` y sustituye el valor por tu clave real:

```
GEMINI_API_KEY=tu_clave_real_aqui
```

> ⚠️ El archivo `.env` nunca se sube a GitHub (está en `.gitignore`). Tu clave
> es privada y solo vive en tu ordenador.

### 5. Arranca la aplicación

```bash
streamlit run app.py
```

Se abrirá en tu navegador en `http://localhost:8501`.

## 👤 Primeros pasos dentro de la app

Al arrancar por primera vez, la base de datos está vacía. Antes de usar el
resto de pestañas, rellena en este orden:

1. **👤 Perfil Inicial** — tus datos básicos (nombre, edad, peso, objetivo, nivel).
2. **🚀 Day One (Base)** — tu contexto de entrenamiento y hábitos actuales (opcional pero recomendado).
3. **🥗 Nutrición → Auditoría Longitudinal → Aplicar Reajuste Nutricional Directo** — ajusta tus objetivos de kcal/proteína/carbos/grasas reales (los valores de partida son solo orientativos).
4. **⚖️ Calibrar Medidas Caseras** (opcional) — si quieres registrar comida por "vasos" o "cazos" propios en vez de gramos, calíbralos aquí primero.

A partir de ahí, ya puedes registrar entrenamientos y comidas con normalidad.

## 🗂️ Tus datos

- La base de datos (`gimnasio.db`) se crea automáticamente en la carpeta del
  proyecto la primera vez que arrancas la app.
- No se sube a GitHub ni se comparte con nadie: vive solo en tu disco local.
- Si quieres empezar de cero, basta con borrar el archivo `gimnasio.db` y
  volver a arrancar la app (se regenerará vacío).

## 🛠️ Estructura del proyecto

```
app.py                  # Interfaz Streamlit (pestañas de la app)
form_components.py      # Formularios de entrada de datos
database.py             # Acceso a la base de datos SQLite local
ai_coach.py             # Integración con la API de Gemini
requirements.txt        # Dependencias de Python
.env.example            # Plantilla para tu API key (copiar como .env)
```

## 📄 Requisitos

- Python 3.10+
- Una API key de Gemini (gratuita) — https://aistudio.google.com/apikey
