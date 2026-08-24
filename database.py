import sqlite3

DB_NAME = "gimnasio.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS perfil 
                      (nombre TEXT, edad INTEGER, peso REAL, objetivo TEXT, nivel TEXT)''')
    
    cursor.execute("PRAGMA table_info(perfil)")
    columns = [column[1] for column in cursor.fetchall()]
    if "peso" not in columns:
        cursor.execute("DROP TABLE perfil")
        cursor.execute('''CREATE TABLE perfil 
                          (nombre TEXT, edad INTEGER, peso REAL, objetivo TEXT, nivel TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS day_one 
                      (rutina TEXT, horas REAL, habitos TEXT, historia TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS modificaciones 
                      (fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP, tipo TEXT, peso REAL, descripcion TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS feedback 
                      (fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP, agente TEXT, valoracion TEXT, comentario TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS diario 
                      (fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP, grupo_muscular TEXT, ejercicios TEXT, comidas TEXT, sensaciones TEXT, analisis_coach TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS dashboard_semanal 
                      (fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP, peso REAL, cintura REAL, sueno REAL, adherencia REAL, pecho REAL, espalda REAL, brazos REAL, piernas REAL, hombros REAL, core REAL)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS nutrition_targets 
                      (fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP, kcal REAL, protein REAL, carbs REAL, fats REAL)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS personal_measurements 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, alimento TEXT UNIQUE, unidad_personal TEXT, gramos_equivalentes REAL, estado TEXT, kcal_100g REAL, protein_100g REAL, carbs_100g REAL, fats_100g REAL)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS food_log 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha DATE DEFAULT (DATE('now')), momento TEXT, alimento TEXT, cantidad REAL, unidad TEXT, estado TEXT, kcal REAL, protein REAL, carbs REAL, fats REAL)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS workout_log 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha DATE DEFAULT (DATE('now')), grupo_muscular TEXT, ejercicio TEXT, serie_num INTEGER, peso REAL, reps INTEGER, rir_rpe REAL, al_fallo INTEGER, notas TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS body_measurements 
                      (fecha DATE DEFAULT (DATE('now')), peso REAL, cintura REAL, brazo REAL, pecho REAL, muslo REAL)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS daily_recovery_log 
                      (fecha DATE DEFAULT (DATE('now')), horas_sueno REAL, calidad_sueno INTEGER, pasos INTEGER, energia INTEGER, fatiga INTEGER, hambre INTEGER)''')

    cursor.execute("SELECT COUNT(*) FROM nutrition_targets")
    if cursor.fetchone()[0] == 0:
        # Valores de partida neutros/orientativos. Cada usuario debe ajustar
        # sus propios objetivos reales desde la pestaña "Auditoría
        # Longitudinal (14 Días) -> Aplicar Reajuste Nutricional Directo",
        # o simplemente actualizándolos ahí antes de empezar a registrar.
        cursor.execute("INSERT INTO nutrition_targets (kcal, protein, carbs, fats) VALUES (2200, 150, 220, 70)")

    # No se precarga ninguna calibración de medida casera: cada usuario debe
    # crear la suya propia desde la pestaña "Calibrar Medidas Caseras", ya
    # que depende de sus recipientes físicos (vasos, tazas, cazos, etc.).

    conn.commit()
    conn.close()

# --- FUNCIONES DE REGISTRO DE ENTRENAMIENTO ---

def guardar_registro_serie(grupo, ejercicio, serie_num, peso, reps, rir, al_fallo, notas):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO workout_log (grupo_muscular, ejercicio, serie_num, peso, reps, rir_rpe, al_fallo, notas) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                   (grupo, ejercicio, serie_num, peso, reps, rir, 1 if al_fallo else 0, notas))
    conn.commit()
    conn.close()

def obtener_series_hoy():
    """Devuelve las series de hoy en orden CRONOLÓGICO (más antigua primero).
    Importante: este orden es el que se usa también para construir el prompt
    de la auditoría IA, así que debe reflejar el orden real en que se
    ejecutaron los ejercicios (primero el bloque que se hizo primero)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, grupo_muscular, ejercicio, serie_num, peso, reps, rir_rpe, al_fallo, notas FROM workout_log WHERE fecha = DATE('now') ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def obtener_series_de_ejercicio_hoy(ejercicio, grupo):
    """Series ya guardadas HOY para un ejercicio+grupo concreto (para mostrar
    el desglose mientras se está registrando ese ejercicio)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""SELECT id, grupo_muscular, ejercicio, serie_num, peso, reps, rir_rpe, al_fallo, notas 
                       FROM workout_log 
                       WHERE fecha = DATE('now') AND ejercicio = ? AND grupo_muscular = ?
                       ORDER BY serie_num ASC""", (ejercicio, grupo))
    rows = cursor.fetchall()
    conn.close()
    return rows

def obtener_siguiente_numero_serie(ejercicio, grupo):
    """Calcula automáticamente qué número de serie toca a continuación para
    ese ejercicio+grupo, hoy."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""SELECT COALESCE(MAX(serie_num), 0) FROM workout_log 
                       WHERE fecha = DATE('now') AND ejercicio = ? AND grupo_muscular = ?""", (ejercicio, grupo))
    maximo = cursor.fetchone()[0]
    conn.close()
    return maximo + 1

def eliminar_serie_hoy(serie_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM workout_log WHERE id = ?", (serie_id,))
    conn.commit()
    conn.close()

# --- FUNCIONES NUTRIONALES Y OTROS ---

def obtener_objetivos_nutricion():
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor(); cursor.execute("SELECT kcal, protein, carbs, fats FROM nutrition_targets ORDER BY fecha DESC LIMIT 1"); row = cursor.fetchone(); conn.close(); return row if row else (2850, 180, 365, 75)

def actualizar_objetivos_nutricion(kcal, protein, carbs, fats):
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor(); cursor.execute("INSERT INTO nutrition_targets (kcal, protein, carbs, fats) VALUES (?, ?, ?, ?)", (kcal, protein, carbs, fats)); conn.commit(); conn.close()

def guardar_equivalencia_personal(alimento, unidad_personal, gramos_eq, estado, k100, p100, c100, g100):
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor(); cursor.execute("""INSERT OR REPLACE INTO personal_measurements (alimento, unidad_personal, gramos_equivalentes, estado, kcal_100g, protein_100g, carbs_100g, fats_100g) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", (alimento, unidad_personal, gramos_eq, estado, k100, p100, c100, g100)); conn.commit(); conn.close()

def obtener_equivalencias_personales():
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor(); cursor.execute("SELECT alimento, unidad_personal, gramos_equivalentes, estado, kcal_100g, protein_100g, carbs_100g, fats_100g FROM personal_measurements ORDER BY alimento ASC"); rows = cursor.fetchall(); conn.close(); return rows

def guardar_registro_comida(momento, alimento, cantidad, unidad, estado, kcal, p, c, g):
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor(); cursor.execute("INSERT INTO food_log (momento, alimento, cantidad, unidad, estado, kcal, protein, carbs, fats) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (momento, alimento, cantidad, unidad, estado, kcal, p, c, g)); conn.commit(); conn.close()

def obtener_comidas_hoy():
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor(); cursor.execute("SELECT id, momento, alimento, cantidad, unidad, estado, kcal, protein, carbs, fats FROM food_log WHERE fecha = DATE('now') ORDER BY id DESC"); rows = cursor.fetchall(); conn.close(); return rows

def eliminar_comida_hoy(comida_id):
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor(); cursor.execute("DELETE FROM food_log WHERE id = ?", (comida_id,)); conn.commit(); conn.close()

def obtener_macros_dia_actual():
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor(); cursor.execute("SELECT SUM(kcal), SUM(protein), SUM(carbs), SUM(fats) FROM food_log WHERE fecha = DATE('now')"); row = cursor.fetchone(); conn.close(); return (row[0] or 0.0, row[1] or 0.0, row[2] or 0.0, row[3] or 0.0)

def guardar_recuperacion_diaria(sueno_hrs, calidad, pasos, energia, fatiga, hambre):
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor(); cursor.execute("INSERT INTO daily_recovery_log (horas_sueno, calidad_sueno, pasos, energia, fatiga, hambre) VALUES (?, ?, ?, ?, ?, ?)", (sueno_hrs, calidad, pasos, energia, fatiga, hambre)); conn.commit(); conn.close()

def obtener_tendencia_peso_2semanas():
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor(); cursor.execute("SELECT fecha, peso, cintura FROM dashboard_semanal ORDER BY fecha DESC LIMIT 3"); rows = cursor.fetchall(); conn.close(); return rows

def obtener_resumen_entreno_2semanas():
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor(); cursor.execute("SELECT grupo_muscular, COUNT(*), AVG(peso), AVG(rir_rpe) FROM workout_log WHERE fecha >= DATE('now', '-14 days') GROUP BY grupo_muscular"); rows = cursor.fetchall(); conn.close(); return rows

def obtener_recuperacion_promedio_2semanas():
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor(); cursor.execute("SELECT AVG(horas_sueno), AVG(pasos), AVG(fatiga), AVG(energia) FROM daily_recovery_log WHERE fecha >= DATE('now', '-14 days')"); row = cursor.fetchone(); conn.close(); return row if row else (0, 0, 0, 0)

def obtener_perfil():
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor(); cursor.execute("SELECT nombre, edad, peso, objetivo, nivel FROM perfil LIMIT 1"); row = cursor.fetchone(); conn.close(); return row

def guardar_perfil(nombre, edad, peso, objetivo, nivel):
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor(); cursor.execute("DELETE FROM perfil"); cursor.execute("INSERT INTO perfil VALUES (?, ?, ?, ?, ?)", (nombre, edad, peso, objetivo, nivel)); conn.commit(); conn.close()

def obtener_day_one():
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor(); cursor.execute("SELECT rutina, horas, habitos, historia FROM day_one LIMIT 1"); row = cursor.fetchone(); conn.close(); return row

def guardar_day_one(rutina, horas, habitos, historia):
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor(); cursor.execute("DELETE FROM day_one"); cursor.execute("INSERT INTO day_one VALUES (?, ?, ?, ?)", (rutina, horas, habitos, historia)); conn.commit(); conn.close()

def registrar_modificacion(tipo, peso, descripcion):
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor(); cursor.execute("INSERT INTO modificaciones (tipo, peso, descripcion) VALUES (?, ?, ?)", (tipo, peso, descripcion)); conn.commit(); conn.close()

def obtener_modificaciones():
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor(); cursor.execute("SELECT fecha, tipo, peso, descripcion FROM modificaciones ORDER BY fecha DESC"); rows = cursor.fetchall(); conn.close(); return rows

def guardar_feedback(agente, val, com):
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor(); cursor.execute("INSERT INTO feedback (agente, valoracion, comentario) VALUES (?, ?, ?)", (agente, val, com)); conn.commit(); conn.close()

def guardar_diario(grupo, ejercicios, comidas, sensaciones, analisis):
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor(); cursor.execute("INSERT INTO diario (grupo_muscular, ejercicios, comidas, sensaciones, analisis_coach) VALUES (?, ?, ?, ?, ?)", (grupo, ejercicios, comidas, sensaciones, analisis)); conn.commit(); conn.close()

def obtener_historial_diario():
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor(); cursor.execute("SELECT fecha, grupo_muscular, ejercicios, comidas, analisis_coach FROM diario ORDER BY fecha DESC"); rows = cursor.fetchall(); conn.close(); return rows

def registrar_dashboard_semanal(p, c, s, a, pe, es, br, pi, ho, co):
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor(); cursor.execute("INSERT INTO dashboard_semanal (peso, cintura, sueno, adherencia, pecho, espalda, brazos, piernas, hombros, core) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (p, c, s, a, pe, es, br, pi, ho, co)); conn.commit(); conn.close()

def obtener_historial_dashboard():
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor(); cursor.execute("SELECT fecha, peso, cintura, sueno, adherencia, pecho, espalda, brazos, piernas, hombros, core FROM dashboard_semanal ORDER BY fecha ASC"); rows = cursor.fetchall(); conn.close(); return rows
