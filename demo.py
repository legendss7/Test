import streamlit as st
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from fpdf import FPDF

# === CONFIGURACIÓN DEL CORREO ===
EMAIL_REMITENTE = "tu_correo@gmail.com"  # 👈 TU correo Gmail
CONTRASEÑA_APP = "abcd efgh ijkl mnop"  # 👈 Tu contraseña de aplicación de 16 dígitos
EMAIL_DESTINO = "jo.tajtaj@gmail.com"

# === PREGUNTAS DISC ===
preguntas = [
    "Soy directo/a y decidido/a.",
    "Me gusta entusiasmar a otros.",
    "Soy paciente y constante.",
    "Soy preciso/a y meticuloso/a.",
    "Me gusta asumir el control.",
    "Soy sociable y comunicativo/a.",
    "Prefiero un ambiente estable y armonioso.",
    "Me gusta seguir reglas y procedimientos.",
    "Soy competitivo/a y orientado/a a resultados.",
    "Soy optimista y expresivo/a.",
    "Soy un/a buen/a oyente.",
    "Me preocupo por los detalles y la exactitud.",
    "Me gusta tomar decisiones rápidas.",
    "Disfruto trabajando en equipo y motivando.",
    "Soy cooperativo/a y servicial.",
    "Soy analítico/a y lógico/a.",
    "Soy audaz y me gusta asumir riesgos.",
    "Soy entusiasta y carismático/a.",
    "Soy leal y confiable.",
    "Soy perfeccionista y organizado/a.",
    "Soy firme y me gusta resolver problemas.",
    "Soy animado/a y creativo/a.",
    "Soy tranquilo/a y evito conflictos.",
    "Soy reflexivo/a y me gusta planificar.",
    "Soy independiente y autosuficiente.",
    "Soy persuasivo/a y me gusta influir.",
    "Soy empático/a y comprensivo/a.",
    "Soy riguroso/a y me gusta la calidad."
]

# === INICIALIZAR SESIÓN ===
if 'respuestas' not in st.session_state:
    st.session_state.respuestas = [None] * 28
if 'indice' not in st.session_state:
    st.session_state.indice = 0
if 'finalizado' not in st.session_state:
    st.session_state.finalizado = False
if 'pdf_generado' not in st.session_state:
    st.session_state.pdf_generado = False

# === FUNCIÓN: Generar PDF ===
def generar_pdf(puntuaciones, estilo_predominante, descripcion):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Informe del Test DISC", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Resultados:", ln=True)
    pdf.set_font("Arial", "", 12)
    for estilo, puntos in puntuaciones.items():
        pdf.cell(0, 8, f"{estilo}: {puntos} puntos", ln=True)

    pdf.ln(8)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Perfil predominante:", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 8, f"{estilo_predominante}\n{descripcion}")

    pdf.ln(10)
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, "Este informe fue generado automáticamente por la aplicación Test DISC.", ln=True, align="C")

    nombre_pdf = "resultado_disc.pdf"
    pdf.output(nombre_pdf)
    return nombre_pdf

# === FUNCIÓN: Enviar correo con PDF ===
def enviar_correo_con_pdf(pdf_path):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_REMITENTE
        msg['To'] = EMAIL_DESTINO
        msg['Subject'] = "📄 Resultado del Test DISC"

        cuerpo = "Hola,\n\nAdjunto encontrarás el resultado del Test DISC.\n\nSaludos."
        msg.attach(MIMEText(cuerpo, 'plain'))

        with open(pdf_path, "rb") as adjunto:
            parte = MIMEBase('application', 'octet-stream')
            parte.set_payload(adjunto.read())
        encoders.encode_base64(parte)
        parte.add_header('Content-Disposition', f'attachment; filename= {os.path.basename(pdf_path)}')
        msg.attach(parte)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_REMITENTE, CONTRASEÑA_APP)
        texto = msg.as_string()
        server.sendmail(EMAIL_REMITENTE, EMAIL_DESTINO, texto)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error al enviar el correo: {e}")
        return False

# === INTERFAZ STREAMLIT ===
st.set_page_config(page_title="Test DISC con Envío", page_icon="📧", layout="centered")
st.title("📧 Test DISC con Envío Automático")
st.markdown("Responde las 28 preguntas. Al finalizar, **tu resultado se enviará a jo.tajtaj@gmail.com**.")

if st.session_state.finalizado:
    # Calcular resultados
    puntuaciones = {'D': 0, 'I': 0, 'S': 0, 'C': 0}
    letras = ['D', 'I', 'S', 'C']
    for i, resp in enumerate(st.session_state.respuestas):
        if resp is not None:
            estilo = letras[resp]
            puntuaciones[estilo] += 1

    max_puntos = max(puntuaciones.values())
    estilos_principales = [k for k, v in puntuaciones.items() if v == max_puntos]

    if len(estilos_principales) == 1:
        estilo = estilos_principales[0]
        descripciones = {
            'D': "Eres directo, decidido y orientado a resultados. Te gusta asumir el control y resolver problemas.",
            'I': "Eres sociable, entusiasta y persuasivo. Te encanta interactuar y motivar a otros.",
            'S': "Eres paciente, leal y cooperativo. Valoras la armonía y la estabilidad en las relaciones.",
            'C': "Eres preciso, analítico y meticuloso. Te enfocas en la calidad, los detalles y la exactitud."
        }
        descripcion = descripciones[estilo]
        st.subheader(f"Tu estilo DISC predominante es: {estilo}")
        st.info(descripcion)
    else:
        estilo = " y ".join(estilos_principales)
        descripcion = f"Tienes un perfil combinado: {estilo}."
        st.subheader("Perfil combinado")
        st.info(descripcion)

    st.bar_chart(puntuaciones)

    # Botón para enviar
    if st.button("📤 Enviar Resultado a jo.tajtaj@gmail.com"):
        with st.spinner("Generando PDF y enviando correo..."):
            pdf_file = generar_pdf(puntuaciones, estilo, descripcion)
            exito = enviar_correo_con_pdf(pdf_file)
            if exito:
                st.success("✅ ¡Resultado enviado correctamente a jo.tajtaj@gmail.com!")
                # Opcional: eliminar el PDF después de enviar
                if os.path.exists(pdf_file):
                    os.remove(pdf_file)
            else:
                st.error("❌ No se pudo enviar el correo. Revisa la configuración.")

    if st.button("🔄 Reiniciar Test"):
        st.session_state.respuestas = [None] * 28
        st.session_state.indice = 0
        st.session_state.finalizado = False
        st.rerun()

else:
    idx = st.session_state.indice
    st.subheader(f"Pregunta {idx + 1} de 28")
    st.markdown(f"**{preguntas[idx]}**")

    opciones = [
        "Dominancia (D): Directo, decidido, firme",
        "Influencia (I): Sociable, entusiasta, persuasivo",
        "Estabilidad (S): Paciente, leal, cooperativo",
        "Cumplimiento (C): Preciso, analítico, meticuloso"
    ]

    respuesta_actual = st.session_state.respuestas[idx] if st.session_state.respuestas[idx] is not None else 0
    seleccion = st.radio("Selecciona la opción que mejor te describe:", opciones, index=respuesta_actual)

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if idx > 0:
            if st.button("⬅️ Anterior"):
                st.session_state.respuestas[idx] = opciones.index(seleccion)
                st.session_state.indice -= 1
                st.rerun()

    with col2:
        if idx < 27:
            if st.button("Siguiente ➡️"):
                st.session_state.respuestas[idx] = opciones.index(seleccion)
                st.session_state.indice += 1
                st.rerun()
        else:
            if st.button("✅ Finalizar Test"):
                st.session_state.respuestas[idx] = opciones.index(seleccion)
                st.session_state.finalizado = True
                st.rerun()

    st.progress((idx + 1) / 28)
