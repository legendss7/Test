import streamlit as st
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from io import BytesIO

# === CONFIGURACIÓN DE CORREO ===
EMAIL_REMITENTE = "jo.tajtaj@gmail.com"
CONTRASEÑA_APP = "nlkt kujl ebdg cyts"
EMAIL_DESTINO = "jo.tajtaj@gmail.com"

# Intentar usar matplotlib solo para PDF
HAS_MPL = False
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    HAS_MPL = True
except:
    pass

# ---------------------------------------------------------------
# Preguntas DISC (28 ítems clásicos)
# ---------------------------------------------------------------
DISC_ITEMS = [
    ("Soy directo/a y decidido/a.", "Me gusta entusiasmar a otros.", "Soy paciente y constante.", "Soy preciso/a y meticuloso/a."),
    ("Me gusta asumir el control.", "Soy sociable y comunicativo/a.", "Prefiero un ambiente estable y armonioso.", "Me gusta seguir reglas y procedimientos."),
    ("Soy competitivo/a y orientado/a a resultados.", "Soy optimista y expresivo/a.", "Soy un/a buen/a oyente.", "Me preocupo por los detalles y la exactitud."),
    ("Me gusta tomar decisiones rápidas.", "Disfruto trabajando en equipo y motivando.", "Soy cooperativo/a y servicial.", "Soy analítico/a y lógico/a."),
    ("Soy audaz y me gusta asumir riesgos.", "Soy entusiasta y carismático/a.", "Soy leal y confiable.", "Soy perfeccionista y organizado/a."),
    ("Soy firme y me gusta resolver problemas.", "Soy animado/a y creativo/a.", "Soy tranquilo/a y evito conflictos.", "Soy reflexivo/a y me gusta planificar."),
    ("Soy independiente y autosuficiente.", "Soy persuasivo/a y me gusta influir.", "Soy empático/a y comprensivo/a.", "Soy riguroso/a y me gusta la calidad.")
]

QUESTIONS = []
for i, (d, i_, s, c) in enumerate(DISC_ITEMS):
    QUESTIONS.append({
        "text": f"Pregunta {i+1}",
        "options": [d, i_, s, c],
        "dims": ["D", "I", "S", "C"]
    })

# ---------------------------------------------------------------
# Estado
# ---------------------------------------------------------------
if "current" not in st.session_state:
    st.session_state.current = 0
    st.session_state.answers = [None] * 28
    st.session_state.finished = False

# ---------------------------------------------------------------
# Función para enviar PDF por correo
# ---------------------------------------------------------------
def enviar_pdf(pdf_bytes, fecha):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_REMITENTE
        msg['To'] = EMAIL_DESTINO
        msg['Subject'] = f"📄 Resultado DISC - Producción - {fecha}"
        cuerpo = "Resultado del Test DISC para roles de producción."
        msg.attach(MIMEText(cuerpo, 'plain'))
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(pdf_bytes)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename=DISC_Produccion.pdf')
        msg.attach(part)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_REMITENTE, CONTRASEÑA_APP.replace(" ", ""))
        server.sendmail(EMAIL_REMITENTE, EMAIL_DESTINO, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        return False

# ---------------------------------------------------------------
# Generar PDF simple (solo resultados relevantes)
# ---------------------------------------------------------------
def generar_pdf_simple(scores, fecha):
    if not HAS_MPL:
        return None
    buf = BytesIO()
    with PdfPages(buf) as pdf:
        fig = plt.figure(figsize=(8.27, 11.69))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis("off")
        ax.text(0.5, 0.95, "Test DISC — Roles de Producción", ha="center", fontsize=18, weight="bold")
        ax.text(0.5, 0.92, f"Fecha: {fecha}", ha="center", fontsize=10)
        y = 0.8
        for dim in ["D", "I", "S", "C"]:
            ax.text(0.1, y, f"{dim}: {scores[dim]}%", fontsize=12)
            y -= 0.04
        # Recomendación laboral simple
        perfil = max(scores, key=scores.get)
        if perfil == "S":
            rec = "✅ Ideal para operario de producción: estable, confiable, buen trabajo en equipo."
        elif perfil == "C":
            rec = "✅ Ideal para control de calidad o procesos: preciso, riguroso, sigue normas."
        elif perfil == "D":
            rec = "⚠️ Apto para supervisión, no para operario estándar: necesita autonomía y acción."
        else:  # I
            rec = "⚠️ Menos adecuado para producción repetitiva: prefiere interacción y dinamismo."
        ax.text(0.1, y - 0.05, "Recomendación para producción:", fontsize=12, weight="bold")
        ax.text(0.1, y - 0.1, rec, fontsize=11, wrap=True)
        pdf.savefig(fig)
        plt.close(fig)
    buf.seek(0)
    return buf.getvalue()

# ---------------------------------------------------------------
# Pantalla de resultados (solo lo relevante para producción)
# ---------------------------------------------------------------
if st.session_state.finished:
    # Calcular puntuaciones
    counts = {"D": 0, "I": 0, "S": 0, "C": 0}
    total = {"D": 7, "I": 7, "S": 7, "C": 7}
    for i, q in enumerate(QUESTIONS):
        ans = st.session_state.answers[i]
        if ans is not None:
            dim = q["dims"][ans]
            counts[dim] += 1
    scores = {d: round((counts[d] / total[d]) * 100, 1) for d in ["D", "I", "S", "C"]}
    perfil = max(scores, key=scores.get)
    
    # Mostrar solo resultado relevante
    st.title("✅ Test DISC completado")
    
    if perfil == "S":
        st.success("✅ **Recomendado para operario de producción**\n\nEstable, confiable, buen trabajo en equipo y bajo presión.")
    elif perfil == "C":
        st.success("✅ **Recomendado para control de calidad o procesos**\n\nPreciso, riguroso, sigue normas y detecta errores.")
    elif perfil == "D":
        st.warning("⚠️ **Apto para supervisión, no para operario estándar**\n\nNecesita autonomía, toma de decisiones y acción directa.")
    else:  # I
        st.warning("⚠️ **Menos adecuado para producción repetitiva**\n\nPrefiere interacción, dinamismo y entornos sociales.")
    
    # Enviar PDF automáticamente
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf_bytes = generar_pdf_simple(scores, fecha)
    if pdf_bytes:
        enviar_pdf(pdf_bytes, fecha)
        st.caption("📄 Informe enviado automáticamente a jo.tajtaj@gmail.com")
    
    if st.button("🔄 Reiniciar"):
        st.session_state.current = 0
        st.session_state.answers = [None] * 28
        st.session_state.finished = False
        st.rerun()

# ---------------------------------------------------------------
# Pantalla de preguntas (minimalista)
# ---------------------------------------------------------------
else:
    idx = st.session_state.current
    q = QUESTIONS[idx]
    st.progress((idx + 1) / 28)
    st.subheader(f"{idx + 1} de 28")
    selected = st.radio(
        "Selecciona la frase que **MEJOR** te describe:",
        q["options"],
        index=st.session_state.answers[idx] if st.session_state.answers[idx] is not None else 0
    )
    st.session_state.answers[idx] = q["options"].index(selected)
    
    if st.button("➡️ Siguiente" if idx < 27 else "✅ Finalizar"):
        if idx < 27:
            st.session_state.current += 1
        else:
            st.session_state.finished = True
        st.rerun()
