import streamlit as st
import pandas as pd
from datetime import datetime
import os
import speech_recognition as sr
import tempfile
import urllib.parse

st.set_page_config(page_title="CIRCE - Asistente Médico", page_icon="🩺", layout="centered")

if "step" not in st.session_state:
    st.session_state.step = "home"
if "symptom" not in st.session_state:
    st.session_state.symptom = ""
if "intensity" not in st.session_state:
    st.session_state.intensity = "Leve"

SINTOMAS = ["Dolor de cabeza", "Tos", "Mareo", "Fiebre", "Dolor en el pecho", "Dolor general"]
INTENSIDADES = ["Leve", "Moderado", "Intenso"]
ARCHIVO_EXCEL = "historial_circe.xlsx"

def transcribir_audio(audio_bytes):
    r = sr.Recognizer()
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        with sr.AudioFile(tmp_path) as source:
            audio = r.record(source)
            texto = r.recognize_google(audio, language="es-MX")
        os.remove(tmp_path)
        return texto
    except:
        return "No entendí el audio"

def guardar_en_excel(sintoma, intensidad):
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nuevo = pd.DataFrame([{"Fecha": fecha, "Sintoma": sintoma, "Intensidad": intensidad}])
    if os.path.exists(ARCHIVO_EXCEL):
        viejo = pd.read_excel(ARCHIVO_EXCEL)
        final = pd.concat([viejo, nuevo], ignore_index=True)
    else:
        final = nuevo
    final.to_excel(ARCHIVO_EXCEL, index=False)
    return final

def enviar_whatsapp_celular(sintoma, intensidad, numero):
    mensaje = f"Alerta CIRCE: {sintoma} ({intensidad}) - {datetime.now().strftime('%d/%m %H:%M')}"
    mensaje_cod = urllib.parse.quote(mensaje)
    numero_limpio = numero.replace("+", "").replace(" ", "")
    link = f"https://wa.me/{numero_limpio}?text={mensaje_cod}"
    st.link_button(f"Enviar WhatsApp a {numero}", link)
    return link

def go_to(step):
    st.session_state.step = step
    st.rerun()

def render_home():
    st.title("🩺 CIRCE - ¿Cómo se siente hoy?")
    st.caption("Orientación informativa. No es un diagnóstico. Consulte a su médico.")
    audio = st.audio_input("Presione para grabar")
    if audio:
        with st.spinner("Transcribiendo..."):
            texto = transcribir_audio(audio.getvalue())
            st.success(f"Entendí: '{texto}'")
            st.session_state.symptom = texto
    if st.button("📋 Consultar síntomas"): go_to("symptoms")
    if st.button("⏰ Ver historial"): go_to("reminders")
    if st.button("🚨 Necesito ayuda urgente", type="primary"): go_to("emergency")

def render_symptoms():
    st.title("¿Cómo se siente?")
    if st.session_state.symptom:
        st.info(f"Usted dijo: {st.session_state.symptom}")
    sintoma = st.radio("Seleccione síntoma:", SINTOMAS, index=0)
    intensidad = st.select_slider("Intensidad:", options=INTENSIDADES, value="Leve")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Volver"): go_to("home")
    with col2:
        if st.button("Continuar ➡️"):
            st.session_state.symptom = sintoma
            st.session_state.intensity = intensidad
            guardar_en_excel(sintoma, intensidad)
            go_to("result")

def render_result():
    st.title("Orientación de CIRCE")
    es_alarma = st.session_state.symptom == "Dolor en el pecho" or st.session_state.intensity == "Intenso"
    if es_alarma:
        st.error("⚠️ Señal de alarma: Busque atención médica inmediata. Si está en México marque 911.")
    else:
        st.success(f"Registré {st.session_state.symptom} ({st.session_state.intensity}) para su consulta.")
    numero = st.text_input("Número familiar con +52", value="+52")
    if st.button("📞 Preparar WhatsApp"):
        enviar_whatsapp_celular(st.session_state.symptom, st.session_state.intensity, numero)
    if st.button("🏠 Volver al inicio"): go_to("home")

def render_reminders():
    st.title("⏰ Historial")
    if os.path.exists(ARCHIVO_EXCEL):
        df = pd.read_excel(ARCHIVO_EXCEL)
        st.dataframe(df, use_container_width=True)
    else:
        st.write("Aún no hay registros")
    if st.button("🏠 Volver al inicio"): go_to("home")

def render_emergency():
    st.title("🚨 EMERGENCIA")
    st.error("Alerta activada. Marque 911 si es necesario.")
    numero = st.text_input("Número de emergencia", value="+52")
    if st.button("Enviar WhatsApp de emergencia"):
        enviar_whatsapp_celular("EMERGENCIA ACTIVADA", "INTENSO", numero)
    if st.button("🏠 Volver al inicio"): go_to("home")

if st.session_state.step == "home": render_home()
elif st.session_state.step == "symptoms": render_symptoms()
elif st.session_state.step == "result": render_result()
elif st.session_state.step == "reminders": render_reminders()
elif st.session_state.step == "emergency": render_emergency()
