import streamlit as st
import database as db
import ai_coach as coach

# Definición de Bloques Principales
BLOQUES_RUTINA = [
    "🔥 Empuje: Pecho / Tríceps / Hombro",
    "💪 Tracción: Espalda / Bíceps / Antebrazo",
    "🦵 Pierna A: Cuádriceps focus",
    "🦵 Pierna B: Cadena Posterior & Gemelo focus",
    "🔀 Variante / Full Body / Específico"
]

GRUPOS_MUSCULARES = [
    "Pecho", "Espalda", "Hombros", "Bíceps", "Tríceps", 
    "Antebrazos", "Cuádriceps", "Isquios/Glúteo", "Gemelos", "Core/Abdomen"
]


def render_form_series():
    st.subheader("📋 Registro Dinámico por Bloques de Rutina")

    if "ejercicio_actual" not in st.session_state:
        st.session_state.ejercicio_actual = None

    bloque_sel = st.selectbox("🎯 Selecciona la Rutina / Bloque del Día", BLOQUES_RUTINA)

    if "Variante" in bloque_sel:
        st.info("💡 Modo Variante activado: Puedes seleccionar libremente cualquier parte del cuerpo.")

    st.markdown("---")

    # ------------------------------------------------------------------
    # PASO 1: Si no hay ejercicio activo, se elige/escribe uno nuevo
    # ------------------------------------------------------------------
    if st.session_state.ejercicio_actual is None:
        st.write("##### ➕ ¿Qué ejercicio vas a registrar ahora?")
        with st.form("form_nuevo_ejercicio", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                grupo_especifico = st.selectbox("Grupo Muscular Concreto", GRUPOS_MUSCULARES)
            with c2:
                ejercicio = st.text_input("Nombre del Ejercicio (escribe libremente)", "")

            iniciar = st.form_submit_button("▶️ Empezar a registrar series de este ejercicio")

            if iniciar:
                if not ejercicio.strip():
                    st.error("Escribe el nombre del ejercicio antes de continuar.")
                else:
                    st.session_state.ejercicio_actual = {
                        "bloque": bloque_sel,
                        "grupo": grupo_especifico,
                        "ejercicio": ejercicio.strip(),
                    }
                    st.rerun()

    # ------------------------------------------------------------------
    # PASO 2: Ejercicio activo -> añadir series una a una sin repetir datos
    # ------------------------------------------------------------------
    else:
        actual = st.session_state.ejercicio_actual
        grupo_guardado = f"{actual['bloque']} -> {actual['grupo']}"

        st.success(f"✍️ Registrando series de: **{actual['ejercicio']}** ({actual['grupo']})")

        series_previas = db.obtener_series_de_ejercicio_hoy(actual["ejercicio"], grupo_guardado)
        if series_previas:
            st.write("**Series ya añadidas a este ejercicio:**")
            for s in series_previas:
                fallo_str = " 🔥 [AL FALLO]" if s[7] else ""
                st.write(f"- Serie {s[3]}: **{s[4]} kg** x **{s[5]} reps** (RIR {s[6]}){fallo_str} — *{s[8]}*")

        siguiente_num = db.obtener_siguiente_numero_serie(actual["ejercicio"], grupo_guardado)

        with st.form("form_add_serie", clear_on_submit=True):
            st.caption(f"Añadiendo Serie {siguiente_num} de **{actual['ejercicio']}**")
            c1, c2, c3 = st.columns(3)
            with c1:
                peso = st.number_input("Peso (kg)", 0.0, 500.0, 20.0, step=2.5)
            with c2:
                reps = st.number_input("Repeticiones", 1, 100, 10)
            with c3:
                rir = st.number_input("RIR (Reps en Recámara)", 0.0, 5.0, 1.0, step=0.5)

            al_fallo = st.checkbox("¿Fue al Fallo Muscular?")
            notas = st.text_area("Observación de esta serie", "Ej. serie de aproximación / al fallo / buenas sensaciones...")

            añadir = st.form_submit_button(f"➕ Añadir Serie {siguiente_num}")

            if añadir:
                db.guardar_registro_serie(
                    grupo=grupo_guardado,
                    ejercicio=actual["ejercicio"],
                    serie_num=siguiente_num,
                    peso=peso,
                    reps=reps,
                    rir=rir,
                    al_fallo=al_fallo,
                    notas=notas,
                )
                st.rerun()

        st.markdown("---")
        if st.button("🔄 Terminar este ejercicio / Registrar otro"):
            st.session_state.ejercicio_actual = None
            st.rerun()


def render_form_comidas():
    st.subheader("➕ Registrar Comida")

    momento = st.selectbox("Momento del Día", ["Desayuno", "Almuerzo/Comida", "Merienda", "Cena", "Snack/Post-Entreno"])

    modo = st.radio(
        "¿Cómo quieres registrar la comida?",
        ["🤖 Describir la comida completa (recomendado)", "📏 Alimento Calibrado", "✍️ Manual / Valores exactos"],
        horizontal=False,
    )

    # ------------------------------------------------------------------
    # MODO 1: Descripción libre -> IA calcula los macros
    # ------------------------------------------------------------------
    if modo == "🤖 Describir la comida completa (recomendado)":
        descripcion = st.text_area(
            "Describe lo que has comido (puedes incluir cantidades aproximadas si quieres más precisión)",
            "Ej. Arroz con pollo, salsa de tomate y judías verdes",
        )

        if st.button("🤖 Calcular macros con IA"):
            with st.spinner("Estimando alimentos y macros..."):
                try:
                    items = coach.estimar_macros_de_comida(descripcion)
                    st.session_state["comida_ia_pendiente"] = items
                    st.session_state["comida_ia_momento"] = momento
                except coach.AICoachError as e:
                    st.error(str(e))

        # Revisión/edición antes de guardar definitivamente
        if st.session_state.get("comida_ia_pendiente"):
            st.markdown("---")
            st.write("**Revisa y ajusta si algo no cuadra antes de guardar:**")

            items_editados = []
            for i, item in enumerate(st.session_state["comida_ia_pendiente"]):
                st.markdown(f"**{item['alimento']}** ({item['cantidad_estimada']})")
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    kcal_e = st.number_input("Kcal", 0.0, 6000.0, float(item["kcal"]), key=f"ia_kcal_{i}")
                with c2:
                    p_e = st.number_input("Proteína (g)", 0.0, 500.0, float(item["protein"]), key=f"ia_p_{i}")
                with c3:
                    c_e = st.number_input("Carbos (g)", 0.0, 500.0, float(item["carbs"]), key=f"ia_c_{i}")
                with c4:
                    g_e = st.number_input("Grasas (g)", 0.0, 500.0, float(item["fats"]), key=f"ia_g_{i}")

                items_editados.append({
                    "alimento": item["alimento"],
                    "cantidad_estimada": item["cantidad_estimada"],
                    "kcal": kcal_e, "protein": p_e, "carbs": c_e, "fats": g_e,
                })

            total_kcal = sum(x["kcal"] for x in items_editados)
            st.caption(f"Total estimado: {total_kcal:.0f} kcal")

            col_ok, col_cancel = st.columns(2)
            with col_ok:
                if st.button("✅ Guardar esta comida en el registro de hoy"):
                    momento_guardado = st.session_state.get("comida_ia_momento", momento)
                    for item in items_editados:
                        db.guardar_registro_comida(
                            momento_guardado, item["alimento"], 1,
                            item["cantidad_estimada"], "estimado_ia",
                            item["kcal"], item["protein"], item["carbs"], item["fats"],
                        )
                    st.session_state["comida_ia_pendiente"] = None
                    st.success("¡Comida guardada!")
                    st.rerun()
            with col_cancel:
                if st.button("❌ Descartar"):
                    st.session_state["comida_ia_pendiente"] = None
                    st.rerun()

    # ------------------------------------------------------------------
    # MODO 2: Alimento calibrado (equivalencias caseras)
    # ------------------------------------------------------------------
    elif modo == "📏 Alimento Calibrado":
        eqs = db.obtener_equivalencias_personales()
        if not eqs:
            st.info("Aún no tienes alimentos calibrados. Usa la pestaña 'Calibrar Medidas Caseras'.")
        else:
            opciones_alimentos = [e[0] for e in eqs]
            alimento_sel = st.selectbox("Selecciona un alimento calibrado", opciones_alimentos)
            data_alim = next((item for item in eqs if item[0] == alimento_sel), None)
            if data_alim:
                _, uni_pers, gr_eq, est, k100, p100, c100, g100 = data_alim
                st.info(f"📏 Calibración Guardada: 1 **{uni_pers}** = {gr_eq}g ({est})")

                unidades_cant = st.number_input(f"Cantidad de ({uni_pers})", 0.1, 20.0, 1.0, step=0.5)
                gramos_totales = unidades_cant * gr_eq

                kcal_tot = (gramos_totales / 100.0) * k100
                p_tot = (gramos_totales / 100.0) * p100
                c_tot = (gramos_totales / 100.0) * c100
                g_tot = (gramos_totales / 100.0) * g100

                st.caption(f"Totales calculados ({gramos_totales:.1f}g): {kcal_tot:.0f} kcal | P: {p_tot:.1f}g | C: {c_tot:.1f}g | G: {g_tot:.1f}g")

                if st.button("Guardar Registro de Comida 🍽️"):
                    db.guardar_registro_comida(momento, alimento_sel, unidades_cant, uni_pers, est, kcal_tot, p_tot, c_tot, g_tot)
                    st.success(f"¡{alimento_sel} añadido con éxito!")
                    st.rerun()

    # ------------------------------------------------------------------
    # MODO 3: Manual, valores exactos introducidos a mano
    # ------------------------------------------------------------------
    else:
        with st.form("form_food_custom"):
            col1, col2 = st.columns(2)
            with col1:
                alim_custom = st.text_input("Nombre del Alimento", "Ej. Pechuga de Pollo")
                cant_custom = st.number_input("Cantidad", 0.0, 2000.0, 200.0)
                unidad_custom = st.text_input("Unidad de Medida", "gramos")
            with col2:
                kcal_c = st.number_input("Calorías Totales (kcal)", 0.0, 3000.0, 220.0)
                p_c = st.number_input("Proteínas (g)", 0.0, 300.0, 46.0)
                c_c = st.number_input("Carbohidratos (g)", 0.0, 300.0, 0.0)
                g_c = st.number_input("Grasas (g)", 0.0, 300.0, 3.5)

            if st.form_submit_button("Guardar Alimento Personalizado 🍽️"):
                db.guardar_registro_comida(momento, alim_custom, cant_custom, unidad_custom, "directo", kcal_c, p_c, c_c, g_c)
                st.success(f"¡{alim_custom} añadido!")
                st.rerun()


def render_form_calibracion_casera():
    st.subheader("⚖️ Calibración de Medida Casera Personal")
    st.caption("Define el peso real de tus recipientes habituales (tazas, vasos, cazos) para no tener que pesar cada día.")
    
    with st.form("form_calib"):
        col1, col2 = st.columns(2)
        with col1:
            alim_nombre = st.text_input("Alimento", "Ej. Arroz cocido / Avena")
            unidad_nombre = st.text_input("Tu Medida Casera", "Ej. Vaso de cristal / Cazo azul")
            gramos_eq = st.number_input("Gramos equivalentes a 1 unidad", 1.0, 1000.0, 250.0)
            estado = st.selectbox("Estado del alimento", ["cooked", "raw", "dry"])
        with col2:
            st.write("**Valores por cada 100g de alimento:**")
            k100 = st.number_input("Kcal / 100g", 0.0, 900.0, 130.0)
            p100 = st.number_input("Proteína / 100g", 0.0, 100.0, 2.7)
            c100 = st.number_input("Carbos / 100g", 0.0, 100.0, 28.0)
            g100 = st.number_input("Grasas / 100g", 0.0, 100.0, 0.3)
            
        if st.form_submit_button("💾 Guardar Equivalencia Personal"):
            db.guardar_equivalencia_personal(alim_nombre, unidad_nombre, gramos_eq, estado, k100, p100, c100, g100)
            st.success(f"¡Calibración guardada! Ahora podrás seleccionar '{unidad_nombre}' en tus registros.")


def render_form_recuperacion_diaria():
    st.subheader("😴 Registro Diario de Recuperación y Fatiga")
    with st.form("form_recuperacion"):
        col1, col2, col3 = st.columns(3)
        with col1:
            sueno = st.number_input("Horas de Sueño", 0.0, 15.0, 7.5, step=0.5)
            calidad = st.slider("Calidad del Sueño (1-10)", 1, 10, 8)
        with col2:
            pasos = st.number_input("Pasos Diarios (NEAT)", 0, 50000, 8000, step=500)
            energia = st.slider("Nivel de Energía (1-10)", 1, 10, 7)
        with col3:
            fatiga = st.slider("Fatiga Percibida (1-10)", 1, 10, 4)
            hambre = st.slider("Nivel de Hambre (1-10)", 1, 10, 5)
            
        if st.form_submit_button("💾 Guardar Métricas de Recuperación"):
            db.guardar_recuperacion_diaria(sueno, calidad, pasos, energia, fatiga, hambre)
            st.success("¡Datos de recuperación guardados correctamente!")