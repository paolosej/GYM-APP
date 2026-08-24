import form_components as fc
import streamlit as st
import database as db
import ai_coach as coach
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="AI Fitness & Nutrition Coach", page_icon="🏋️‍♂️", layout="wide")

db.init_db()

st.title("🏋️‍♂️ AI Fitness & Nutrition System")

# Pestañas principales
tab_entreno, tab_nutricion, tab_historial, tab_dash, tab_long, tab_mods, tab_dayone, tab_perfil = st.tabs([
    "🏋️‍♂️ Biomecánica & Entreno",
    "🥗 Nutrición & Flexibilidad",
    "📜 Historial Diario",
    "📊 Gym Dashboard & Registro Diario",
    "🧠 Auditoría Longitudinal (14 Días)",
    "🔄 Modificaciones / Eventos",
    "🚀 Day One (Base)", 
    "👤 Perfil Inicial"
])

# --- 1. BIOMECÁNICA Y ENTRENO ---
with tab_entreno:
    st.header("🏋️‍♂️ Registro por Bloques de Rutina y Auditoría Biomecánica")
    perfil = db.obtener_perfil()
    d1 = db.obtener_day_one()
    
    if not perfil:
        st.warning("⚠️ Completa primero la pestaña 'Perfil Inicial'.")
    else:
        # Formulario de entrada de datos por Bloque
        fc.render_form_series()
        st.divider()
        
        # Resumen dinámico de las series registradas hoy
        st.subheader("📝 Desglose de Series Registradas Hoy")
        series_hoy = db.obtener_series_hoy()
        
        if not series_hoy:
            st.info("Aún no has añadido series para la rutina de hoy.")
        else:
            for s in series_hoy:
                s_id, g_bloque, ej, s_num, p, r, rir, fallo, not_txt = s
                col_s1, col_s2 = st.columns([6, 1])
                with col_s1:
                    fallo_str = " 🔥 [AL FALLO]" if fallo else ""
                    st.write(f"• **[{g_bloque}]** {ej} | Serie {s_num}: **{p} kg** x **{r} reps** (RIR {rir}){fallo_str} | *{not_txt}*")
                with col_s2:
                    if st.button("🗑️", key=f"del_serie_{s_id}"):
                        db.eliminar_serie_hoy(s_id)
                        st.rerun()

        st.divider()
        st.subheader("🤖 Consultar Auditoría al Agente Biomecánico")
        
        with st.form("form_entreno_ia"):
            sensaciones = st.text_input("Sensaciones Globales o Molestias Articulares de la Sesión", "Buena congestión general, sin molestias articulares.")
            sub_ent = st.form_submit_button("Analizar Rutina Completa de Hoy con la IA 🚀")
        
        if sub_ent:
            if not series_hoy:
                st.warning("Añade al menos una serie en el desglose de arriba antes de consultar al Agente.")
            else:
                # Formateamos todas las series registradas para el prompt de la IA
                resumen_ejercicios_texto = "\n".join([
                    f"- Bloque/Grupo: {s[1]} | Ejercicio: {s[2]} | Serie {s[3]}: {s[4]}kg x {s[5]}reps (RIR {s[6]}) | Notas: {s[8]}" 
                    for s in series_hoy
                ])
                
                mods = db.obtener_modificaciones()
                with st.spinner("El Agente Biomecánico está auditando la rutina completa..."):
                    res_e = coach.analizar_entrenamiento(perfil, d1, mods, "Rutina por Bloques de Hoy", resumen_ejercicios_texto, sensaciones)
                    st.session_state["res_entreno"] = res_e
                    db.guardar_diario("Rutina Completa", resumen_ejercicios_texto, "N/A", sensaciones, res_e)

        if "res_entreno" in st.session_state:
            st.markdown("---")
            st.markdown(st.session_state["res_entreno"])

# --- 2. NUTRICIÓN Y FLEXIBILIDAD ---
with tab_nutricion:
    st.header("🥗 Nutrición, Registro Cuantitativo y Flexibilidad")
    perfil = db.obtener_perfil()
    
    if not perfil:
        st.warning("⚠️ Completa primero la pestaña 'Perfil Inicial'.")
    else:
        obj_k, obj_p, obj_c, obj_g = db.obtener_objetivos_nutricion()
        cur_k, cur_p, cur_c, cur_g = db.obtener_macros_dia_actual()
        
        rem_k = obj_k - cur_k
        rem_p = obj_p - cur_p
        rem_c = obj_c - cur_c
        rem_g = obj_g - cur_g
        
        st.write("### 📊 Estado de Macros de Hoy")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Calorías", f"{cur_k:.0f} / {obj_k:.0f} kcal", f"{rem_k:.0f} kcal restantes")
        m2.metric("Proteína", f"{cur_p:.1f} / {obj_p:.0f} g", f"{rem_p:.1f} g restantes")
        m3.metric("Carbohidratos", f"{cur_c:.1f} / {obj_c:.0f} g", f"{rem_c:.1f} g restantes")
        m4.metric("Grasas", f"{cur_g:.1f} / {obj_g:.0f} g", f"{rem_g:.1f} g restantes")

        with st.expander("🎯 Ajustar mis objetivos diarios de macros"):
            st.caption("Define aquí tus propios objetivos de kcal/proteína/carbos/grasas. Se aplican desde ya a la barra de arriba.")
            with st.form("form_objetivos_nutricion"):
                o1, o2, o3, o4 = st.columns(4)
                with o1:
                    new_obj_k = st.number_input("Calorías (kcal)", 0.0, 8000.0, float(obj_k), step=50.0)
                with o2:
                    new_obj_p = st.number_input("Proteína (g)", 0.0, 500.0, float(obj_p), step=5.0)
                with o3:
                    new_obj_c = st.number_input("Carbohidratos (g)", 0.0, 800.0, float(obj_c), step=10.0)
                with o4:
                    new_obj_g = st.number_input("Grasas (g)", 0.0, 300.0, float(obj_g), step=5.0)

                if st.form_submit_button("💾 Guardar mis objetivos"):
                    db.actualizar_objetivos_nutricion(new_obj_k, new_obj_p, new_obj_c, new_obj_g)
                    st.success("¡Objetivos actualizados!")
                    st.rerun()

        st.divider()

        sub_tab_add, sub_tab_list, sub_tab_flex, sub_tab_calib = st.tabs([
            "➕ Registrar Alimento/Porción", 
            "📋 Registro de Hoy", 
            "💡 Coach de Flexibilidad", 
            "⚖️ Calibrar Medidas Caseras"
        ])
        
        with sub_tab_add:
            fc.render_form_comidas()
            
        with sub_tab_list:
            st.subheader("📋 Alimentos Registrados Hoy")
            comidas_hoy = db.obtener_comidas_hoy()
            if not comidas_hoy:
                st.info("Aún no has añadido alimentos hoy.")
            else:
                for row in comidas_hoy:
                    c_id, mom, alim, cant, uni, est, k, p, c, g = row
                    col_info, col_del = st.columns([5, 1])
                    with col_info:
                        st.write(f"**[{mom}]** {alim} - {cant} {uni} ({est}) ➡️ **{k:.0f} kcal** | P: {p:.1f}g | C: {c:.1f}g | G: {g:.1f}g")
                    with col_del:
                        if st.button("🗑️ Eliminar", key=f"del_food_{c_id}"):
                            db.eliminar_comida_hoy(c_id)
                            st.rerun()

        with sub_tab_flex:
            st.subheader("💡 Asistente Nutricional de Autonomía")
            tipo_consulta = st.radio("¿En qué te ayudo ahora?", [
                "¿Qué me falta exactamente hoy y con qué opciones puedo completarlo?",
                "Tengo ciertos alimentos disponibles en casa, ¿cómo armo mi comida?",
                "He comido fuera / Tengo una comida social, ¿cómo compenso el resto del día?"
            ])
            contexto_user = st.text_input("Ingredientes disponibles o detalles opcionales", "Ej: Tengo huevos, yogur griego y plátanos.")
            if st.button("Consultar Opciones Flexibles 🚀"):
                with st.spinner("Calculando combinaciones adaptadas a tus macros restantes..."):
                    res_flex = coach.responder_flexibilidad_nutricional(tipo_consulta, (rem_k, rem_p, rem_c, rem_g), contexto_user)
                    st.markdown("---")
                    st.markdown(res_flex)

        with sub_tab_calib:
            fc.render_form_calibracion_casera()

# --- 3. HISTORIAL DIARIO ---
with tab_historial:
    st.header("📜 Historial de Registros y Análisis Guardados")
    historial = db.obtener_historial_diario()
    if not historial:
        st.info("Aún no hay registros en el diario.")
    else:
        for h in historial:
            with st.expander(f"📅 {h[0]} — {h[1]}"):
                if h[2] != "N/A": st.write(f"🏋️ **Desglose de Rutina:**\n{h[2]}")
                if h[3] != "N/A": st.write(f"🥗 **Comidas:** {h[3]}")
                st.markdown("---")
                st.markdown(f"**Análisis del Coach:**\n\n{h[4]}")

# --- 4. DASHBOARD & REGISTRO DIARIO ---
with tab_dash:
    st.header("📊 Gym Dashboard & Registro Diario")
    fc.render_form_recuperacion_diaria()
    st.divider()
    
    with st.expander("➕ Actualizar Medición Semanal (Cintura, Radar, Sueño)"):
        with st.form("form_dash"):
            col_d1, col_d2, col_d3 = st.columns(3)
            with col_d1:
                peso_s = st.number_input("Peso Corporal (kg)", 40.0, 200.0, perfil[2] if perfil else 75.0)
                cintura_s = st.number_input("Cintura (cm)", 50.0, 150.0, 80.0)
            with col_d2:
                sueno_s = st.number_input("Sueño Diario Promedio (hrs)", 3.0, 12.0, 7.5)
                adh_s = st.slider("Adherencia Nutricional (%)", 0, 100, 85)
            with col_d3:
                p_pecho = st.slider("Pecho", 0, 100, 70)
                p_espalda = st.slider("Espalda", 0, 100, 70)
                p_brazos = st.slider("Brazos", 0, 100, 70)
                p_piernas = st.slider("Piernas", 0, 100, 70)
                p_hombros = st.slider("Hombros", 0, 100, 70)
                p_core = st.slider("Core", 0, 100, 70)

            if st.form_submit_button("Guardar Registro Semanal 📈"):
                db.registrar_dashboard_semanal(peso_s, cintura_s, sueno_s, adh_s, p_pecho, p_espalda, p_brazos, p_piernas, p_hombros, p_core)
                st.success("¡Medición semanal guardada!")

    dash_data = db.obtener_historial_dashboard()
    if dash_data:
        cols = ["Fecha", "Peso", "Cintura", "Sueño", "Adherencia", "Pecho", "Espalda", "Brazos", "Piernas", "Hombros", "Core"]
        df = pd.DataFrame(dash_data, columns=cols)
        ult = df.iloc[-1]
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Peso Actual", f"{ult['Peso']} kg")
        m2.metric("Cintura", f"{ult['Cintura']} cm")
        m3.metric("Sueño Promedio", f"{ult['Sueño']} hrs")
        m4.metric("Adherencia Dieta", f"{ult['Adherencia']}%")
        st.divider()

        col_rad, col_lin = st.columns(2)
        with col_rad:
            st.subheader("🕸️ Perfil de Desarrollo Muscular (Radar)")
            categories = ['Pecho', 'Espalda', 'Brazos', 'Piernas', 'Hombros', 'Core']
            values = [ult['Pecho'], ult['Espalda'], ult['Brazos'], ult['Piernas'], ult['Hombros'], ult['Core']]
            fig_radar = go.Figure(data=go.Scatterpolar(r=values + [values[0]], theta=categories + [categories[0]], fill='toself'))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False)
            st.plotly_chart(fig_radar, use_container_width=True)

        with col_lin:
            st.subheader("📈 Evolución de Peso y Cintura")
            fig_line = px.line(df, x="Fecha", y=["Peso", "Cintura"], markers=True)
            st.plotly_chart(fig_line, use_container_width=True)

# --- 5. AUDITORÍA LONGITUDINAL ---
with tab_long:
    st.header("🧠 Auditoría Longitudinal de 14 Días y Regla de las 2 Semanas")
    st.caption("Evaluación automática de progresiones de carga, tendencia de peso y reajuste dinámico de calorías.")
    
    perfil = db.obtener_perfil()
    tendencia_peso = db.obtener_tendencia_peso_2semanas()
    resumen_entreno = db.obtener_resumen_entreno_2semanas()
    recuperacion = db.obtener_recuperacion_promedio_2semanas()
    objetivos_act = db.obtener_objetivos_nutricion()
    
    if st.button("Ejecutar Auditoría Longitudinal con la IA 🧠"):
        with st.spinner("Analizando 14 días de datos bio-métricos, fatiga y progresiones..."):
            res_long = coach.auditar_progreso_longitudinal(perfil, tendencia_peso, resumen_entreno, recuperacion, objetivos_act)
            st.session_state["res_longitudinal"] = res_long

    if "res_longitudinal" in st.session_state:
        st.markdown("---")
        st.markdown(st.session_state["res_longitudinal"])
        
        st.divider()
        st.subheader("⚙️ Aplicar Reajuste Nutricional Directo")
        with st.form("form_update_targets"):
            st.caption("Si la IA recomendó un ajuste de calorías/carbos, actualízalo aquí para reflejarlo en la pestaña Nutrición:")
            c_k, c_p, c_c, c_g = st.columns(4)
            with c_k: new_k = st.number_input("Nuevas Kcal", value=float(objetivos_act[0]), step=50.0)
            with c_p: new_p = st.number_input("Nueva Proteína (g)", value=float(objetivos_act[1]), step=5.0)
            with c_c: new_c = st.number_input("Nuevos Carbos (g)", value=float(objetivos_act[2]), step=10.0)
            with c_g: new_g = st.number_input("Nuevas Grasas (g)", value=float(objetivos_act[3]), step=5.0)
            
            if st.form_submit_button("💾 Guardar Nuevos Objetivos de Macros"):
                db.actualizar_objetivos_nutricion(new_k, new_p, new_c, new_g)
                st.success("¡Objetivos nutricionales actualizados con éxito!")
                st.rerun()

# --- 6. MODIFICACIONES ---
with tab_mods:
    st.header("🔄 Registro de Modificaciones y Eventos")
    with st.form("form_modificacion"):
        tipo = st.selectbox("Tipo de Evento", ["Lesión / Molestia", "Cambio de Peso", "Parón / Vacaciones", "Cambio de Objetivo"])
        nuevo_peso = st.number_input("Peso Actual (kg)", 40.0, 200.0, perfil[2] if perfil else 75.0)
        descripcion = st.text_area("Detalles del evento", "Ej: Leve molestia en hombro al hacer press banca.")
        if st.form_submit_button("Registrar Evento 📌"):
            db.registrar_modificacion(tipo, nuevo_peso, descripcion)
            st.success("¡Evento registrado!")

    mods = db.obtener_modificaciones()
    for m in mods:
        st.info(f"**[{m[0]}] {m[1]}** | Peso: {m[2]}kg\n\n{m[3]}")

# --- 7. DAY ONE ---
with tab_dayone:
    st.header("🚀 Contexto Inicial (Day One)")
    d1 = db.obtener_day_one()
    with st.form("form_dayone"):
        rutina = st.text_area("Rutina Inicial", d1[0] if d1 else "Ej: Torso/Pierna 4 días")
        horas = st.number_input("Horas/Semana", 1.0, 30.0, d1[1] if d1 else 5.0)
        habitos = st.text_area("Hábitos Nutricionales Base", d1[2] if d1 else "Ej: 3 comidas al día")
        historia = st.text_area("Historia Previa", d1[3] if d1 else "Sin antecedentes")
        if st.form_submit_button("Guardar Day One 📌"):
            db.guardar_day_one(rutina, horas, habitos, historia)
            st.success("¡Contexto base guardado!")

# --- 8. PERFIL INICIAL ---
with tab_perfil:
    st.header("👤 Perfil Biológico Inicial")
    perfil = db.obtener_perfil()
    with st.form("form_perfil"):
        nombre = st.text_input("Nombre", perfil[0] if perfil else "Atleta")
        edad = st.number_input("Edad", 14, 90, perfil[1] if perfil else 25)
        peso = st.number_input("Peso Inicial (kg)", 40.0, 200.0, perfil[2] if perfil else 75.0)
        objetivo = st.selectbox("Objetivo Principal", ["Hipertrofia", "Fuerza", "Perdida de Grasa"])
        nivel = st.selectbox("Nivel", ["Principiante", "Intermedio", "Avanzado"])
        if st.form_submit_button("Guardar Perfil Base 💾"):
            db.guardar_perfil(nombre, edad, peso, objetivo, nivel)
            st.success("¡Perfil guardado!")