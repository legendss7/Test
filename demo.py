import streamlit as st
from typing import Dict, List
import smtplib
from email.message import EmailMessage
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# ============================================================
# CONFIG GENERAL
# ============================================================
st.set_page_config(
    page_title="EPQR-A | Evaluación Operativa",
    page_icon="🧪",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ============================================================
# ESTILOS CSS
# ============================================================
st.markdown("""
<style>
[data-testid="stSidebar"] { display:none !important; }

html, body, [data-testid="stAppViewContainer"]{
  background: radial-gradient(circle at 20% 20%, #eef2ff 0%, #fff 60%) !important;
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
  color:#111;
}
.block-container{
  max-width:720px;
  padding-top:1.5rem;
  padding-bottom:4rem;
}

.card{
  background:#ffffff;
  border:1px solid #e5e7eb;
  border-radius:1rem;
  box-shadow:0 24px 48px -12px rgba(0,0,0,.08);
  padding:1.5rem 1.25rem;
  margin-bottom:1rem;
}
.card-header{
  background:linear-gradient(90deg,#2563eb 0%,#4f46e5 100%);
  color:#fff;
  padding:1rem 1.25rem;
  border-radius:1rem 1rem 0 0;
  box-shadow:inset 0 0 30px rgba(255,255,255,.18);
  text-align:center;
}
.card-header h1,
.card-header h2,
.card-header h3{
  margin:0;
  font-weight:600;
  line-height:1.2;
}

.badge-pill{
  display:inline-block;
  font-size:.7rem;
  font-weight:600;
  line-height:1;
  padding:.4rem .6rem;
  border-radius:999px;
  background:rgba(255,255,255,.18);
  color:#fff;
  border:1px solid rgba(255,255,255,.4);
}

.muted{
  font-size:.8rem;
  color:#6b7280;
  line-height:1.4;
}

.alt-block{
  background:#f9fafb;
  border:1px solid #e5e7eb;
  border-radius:.75rem;
  padding:1rem;
  margin-bottom:.75rem;
  box-shadow:0 12px 20px -8px rgba(0,0,0,.05);
}
.alt-block h4{
  margin-top:0;
  margin-bottom:.25rem;
  font-size:.9rem;
  line-height:1.3;
  font-weight:600;
  color:#111827;
}
.alt-block p{
  margin:0;
  font-size:.8rem;
  color:#4b5563;
  line-height:1.4;
}

/* Pantalla final gigante */
.final-big{
  font-size:clamp(2rem,4vw,3rem);
  font-weight:800;
  color:#10b981;
  text-align:center;
  line-height:1.2;
  margin-bottom:1rem;
}
.final-sub{
  font-size:1rem;
  color:#374151;
  text-align:center;
  max-width:500px;
  margin:0 auto;
  line-height:1.4;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# PREGUNTAS (30 ÍTEMS) Y CATEGORÍAS
# ============================================================

QUESTIONS = [
    "¿Tiene con frecuencia subidas y bajadas de su estado de ánimo?",
    "¿Es usted una persona habladora?",
    "¿Lo pasaría muy mal si viese sufrir a un niño o a un animal?",
    "¿Es usted más bien animado/a?",
    "¿Alguna vez ha deseado más ayudarse a sí mismo/a que compartir con otros?",
    "¿Tomaría drogas que pudieran tener efectos desconocidos o peligrosos?",
    "¿Ha acusado a alguien alguna vez de hacer algo sabiendo que la culpa era de usted?",
    "¿Prefiere actuar a su modo en lugar de comportarse según las normas?",
    "¿Se siente con frecuencia harto/a («hasta la coronilla»)?",
    "¿Ha cogido alguna vez algo que perteneciese a otra persona (aunque sea un broche o un bolígrafo)?",
    "¿Se considera una persona nerviosa?",
    "¿Piensa que el matrimonio está pasado de moda y que se debería suprimir?",
    "¿Podría animar fácilmente una fiesta o reunión social aburrida?",
    "¿Es usted una persona demasiado preocupada?",
    "¿Tiende a mantenerse callado/a (o en un 2° plano) en las reuniones o encuentros sociales?",
    "¿Cree que la gente dedica demasiado tiempo para asegurarse el futuro mediante ahorros o seguros?",
    "¿Alguna vez ha hecho trampas en el juego?",
    "¿Sufre usted de los nervios?",
    "¿Se ha aprovechado alguna vez de otra persona?",
    "Cuando está con otras personas, ¿es usted más bien callado/a?",
    "¿Se siente muy solo/a con frecuencia?",
    "¿Cree que es mejor seguir las normas de la sociedad que las suyas propias?",
    "¿Las demás personas le consideran muy animado/a?",
    "¿Pone en práctica siempre lo que dice?",
    "¿Pierde la calma fácilmente cuando algo no resulta en el trabajo?",
    "¿Le resulta natural dar instrucciones claras a otras personas?",
    "¿Alguna vez ocultó un error propio para evitar un llamado de atención?",
    "¿Le cuesta desconectarse mentalmente de las preocupaciones?",
    "¿Siente que puede mantener la cabeza fría en una emergencia?",
    "¿Le cuesta seguir reglas que considera innecesarias?"
]

# Categoría de cada pregunta:
# E = Sociabilidad / Asertividad
# N = Estabilidad emocional inversa (tensión / nerviosismo)
# P = Impulsividad / dureza / tolerancia a presión / desafío a normas
# S = Sinceridad / apego a normas / confiabilidad declarada
CATEGORIES = [
    "N", "E", "P", "E", "S", "P", "S", "P", "N", "S",
    "N", "P", "E", "N", "E", "P", "S", "N", "S", "E",
    "N", "P", "E", "S",
    "N",  # pierde la calma
    "E",  # dar instrucciones
    "S",  # ocultar error
    "N",  # no desconectarse
    "P",  # cabeza fría
    "P",  # saltarse reglas
]

# cuántas preguntas tiene cada dimensión (para normalizar)
DIM_COUNTS = {
    "E": CATEGORIES.count("E"),
    "N": CATEGORIES.count("N"),
    "P": CATEGORIES.count("P"),
    "S": CATEGORIES.count("S"),
}
# En este set:
# N: 8
# P: 8
# E: 7
# S: 7

# ============================================================
# PERFILES DE CARGO Y RANGOS ESPERADOS (ESCALA 0–6)
# ============================================================
JOB_PROFILES = {
    "operario": {
        "title": "Operario de Producción",
        "requirements": {
            "E": {"min": 0, "max": 4},
            "N": {"min": 0, "max": 3},
            "P": {"min": 0, "max": 5},
            "S": {"min": 4, "max": 6},
        },
        "desc": "Ejecución estable y disciplinada. Cumplimiento estricto de normas de seguridad y ritmo constante.",
    },
    "supervisor": {
        "title": "Supervisor Operativo",
        "requirements": {
            "E": {"min": 3, "max": 6},
            "N": {"min": 0, "max": 3},
            "P": {"min": 2, "max": 5},
            "S": {"min": 4, "max": 6},
        },
        "desc": "Coordina equipos bajo presión, comunica instrucciones claras y corrige desvíos sin perder control emocional.",
    },
    "tecnico": {
        "title": "Técnico de Mantenimiento",
        "requirements": {
            "E": {"min": 1, "max": 4},
            "N": {"min": 0, "max": 3},
            "P": {"min": 2, "max": 5},
            "S": {"min": 4, "max": 6},
        },
        "desc": "Diagnóstico y solución de fallas. Necesita foco técnico, calma ante problemas y apego al reporte honesto.",
    },
    "logistica": {
        "title": "Personal de Logística",
        "requirements": {
            "E": {"min": 2, "max": 5},
            "N": {"min": 0, "max": 3},
            "P": {"min": 1, "max": 4},
            "S": {"min": 4, "max": 6},
        },
        "desc": "Movimiento de insumos y producto terminado. Requiere coordinación entre áreas y registro riguroso.",
    },
}

# ============================================================
# ESTADO
# fases: "role" -> "candidate" -> "test" -> "done"
# ============================================================
def init_state():
    if "phase" not in st.session_state:
        st.session_state.phase = "role"
    if "selected_job" not in st.session_state:
        st.session_state.selected_job = None
    if "candidate_name" not in st.session_state:
        st.session_state.candidate_name = ""
    if "evaluator_email" not in st.session_state:
        st.session_state.evaluator_email = ""
    if "q_idx" not in st.session_state:
        st.session_state.q_idx = 0
    if "answers" not in st.session_state:
        st.session_state.answers = {i: None for i in range(len(QUESTIONS))}
    if "scores" not in st.session_state:
        st.session_state.scores = {"E": 0, "N": 0, "P": 0, "S": 0}
    if "final_report" not in st.session_state:
        st.session_state.final_report = None
    if "_needs_rerun" not in st.session_state:
        st.session_state._needs_rerun = False
    if "email_sent" not in st.session_state:
        st.session_state.email_sent = False

init_state()

# ============================================================
# CÁLCULO DE PUNTAJES CRUDOS
# ============================================================
def compute_scores(answers: Dict[int, int]) -> Dict[str, int]:
    """
    answers[i] = 1 si respondió Sí, 0 si respondió No.

    Para E y N sumamos "Sí" (1).
    Para P y S, la lógica invertida:
      - responder "No" (0) suma 1 punto (control / honestidad),
      - responder "Sí" (1) suma 0.
    """
    scores = {"E": 0, "N": 0, "P": 0, "S": 0}
    for idx, cat in enumerate(CATEGORIES):
        ans = answers.get(idx)
        if ans is None:
            continue
        if cat in ["P", "S"]:
            # invertido: No=1, Sí=0
            val = 1 if ans == 0 else 0
            scores[cat] += val
        else:
            # directo: Sí=1, No=0
            scores[cat] += ans
    return scores

# ============================================================
# NORMALIZACIÓN A ESCALA 0–6 Y CLASIFICACIÓN DE APTITUD
# ============================================================
def evaluate_fit_for_job(raw_scores: Dict[str, int], profile: dict):
    """
    Compara al candidato con el perfil del cargo usando puntajes
    escalados a una base común 0–6.
    """
    req = profile["requirements"]
    issues = []
    scaled_scores = {}

    for dim in ["E", "N", "P", "S"]:
        total_items_dim = DIM_COUNTS[dim]    # p.ej. 7 u 8
        bruto = raw_scores[dim]              # conteo bruto
        # Normalizar a escala 0–6 y redondear
        scaled = round((bruto / total_items_dim) * 6)
        scaled_scores[dim] = scaled

        mn = req[dim]["min"]
        mx = req[dim]["max"]
        if scaled < mn:
            issues.append(f"{dim} bajo respecto al mínimo esperado")
        elif scaled > mx:
            issues.append(f"{dim} sobre el máximo aceptable")

    # Clasificación global
    if len(issues) == 0:
        level = "APTO"
    elif len(issues) == 1:
        level = "RIESGO PARCIAL"
    else:
        level = "NO APTO DIRECTO"

    return {
        "matchLevel": level,
        "issues": issues,
        "scaled_scores": scaled_scores,  # para depurar interno si quieres
    }

# ============================================================
# PERFIL CUALITATIVO (FORTALEZAS / RIESGOS)
# ============================================================
def build_strengths_and_risks(scores: Dict[str, int]) -> Dict[str, List[str]]:
    """
    Genera fortalezas y riesgos cualitativos sin números.
    """
    strengths = []
    risks = []

    N = scores["N"]
    E = scores["E"]
    P = scores["P"]
    S = scores["S"]

    # N (tensión emocional)
    if N <= 3:
        strengths.append("Maneja la presión sin desbordarse fácilmente.")
    else:
        risks.append("Puede presentar tensión emocional o irritabilidad bajo presión operativa.")

    # S (adhesión a normas)
    if S >= 4:
        strengths.append("Declara apego a normas y estándares formales.")
        strengths.append("Expresa disposición a actuar de forma correcta y transparente.")
    else:
        risks.append("Requiere supervisión para asegurar cumplimiento estricto de normas y reporte de incidentes.")

    # E (comunicación / visibilidad)
    if E >= 3:
        strengths.append("Puede comunicarse con otros, dar instrucciones o pedir apoyo cuando lo necesita.")
    else:
        strengths.append("Perfil más reservado, trabaja en silencio sin generar conflicto innecesario.")
        risks.append("Podría no escalar alertas críticas a tiempo si ocurre una falla en la línea.")

    # P (tolerancia a presión / control conductual)
    if 2 <= P <= 5:
        strengths.append("Muestra tolerancia al estrés operativo y capacidad para actuar en situaciones complejas.")
    elif P < 2:
        strengths.append("Tendencia cooperativa y poco confrontacional.")
        risks.append("Podría tener dificultad para imponer límites frente a conductas inseguras de otros.")
    else:  # P > 5
        risks.append("Podría tomar decisiones demasiado directas o arriesgadas sin consultar al supervisor.")

    return {"strengths": strengths, "risks": risks}

# ============================================================
# ARMAR INFORME FINAL (SIN NÚMEROS VISIBLES)
# ============================================================
def build_final_report():
    """
    Crea el paquete final que va al PDF / correo.
    """
    scores_raw = compute_scores(st.session_state.answers)
    st.session_state.scores = scores_raw

    sel_job_key = st.session_state.selected_job
    sel_profile = JOB_PROFILES[sel_job_key]

    # Ajuste al cargo elegido (usa puntajes escalados a 0–6)
    fit_selected = evaluate_fit_for_job(scores_raw, sel_profile)

    # Fortalezas / Riesgos cualitativos
    qual = build_strengths_and_risks(scores_raw)

    # Recomendación textual final
    if fit_selected["matchLevel"] == "APTO":
        rec_text = "El candidato se considera capacitado para ejercer el cargo seleccionado."
    elif fit_selected["matchLevel"] == "RIESGO PARCIAL":
        rec_text = ("El candidato presenta aspectos críticos puntuales. "
                    "Se sugiere verificación adicional en entrevista y en terreno antes de asignar el cargo.")
    else:
        rec_text = ("El candidato no cumple las condiciones conductuales mínimas declaradas "
                    "para desempeñar el cargo objetivo sin riesgos adicionales.")

    # Posibles reubicaciones sin mostrar números
    all_fits = []
    for key, prof in JOB_PROFILES.items():
        fit_other = evaluate_fit_for_job(scores_raw, prof)
        all_fits.append({
            "job_key": key,
            "title": prof["title"],
            "desc": prof["desc"],
            "matchLevel": fit_other["matchLevel"],
        })

    st.session_state.final_report = {
        "candidate_name": st.session_state.candidate_name,
        "evaluator_email": st.session_state.evaluator_email,
        "selected_job_key": sel_job_key,
        "selected_job_title": sel_profile["title"],
        "fit_selected": fit_selected,          # APTO / RIESGO PARCIAL / NO APTO DIRECTO
        "qual_strengths": qual["strengths"],   # lista de frases
        "qual_risks": qual["risks"],           # lista de frases
        "recommendation": rec_text,            # texto final
        "all_fits": all_fits,                  # sugerencias de ubicación alternativa
    }

# ============================================================
# GENERAR PDF PARA RR.HH. (SIN PUNTAJES)
# ============================================================
def generate_pdf_bytes(report: dict) -> bytes:
    """
    PDF confidencial del candidato. Sin puntajes numéricos.
    """
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    line_y = height - 40

    def write(text, size=10, bold=False, gap=14):
        nonlocal line_y
        if line_y < 60:
            c.showPage()
            line_y = height - 40
        if bold:
            c.setFont("Helvetica-Bold", size)
        else:
            c.setFont("Helvetica", size)
        for line in text.split("\n"):
            c.drawString(40, line_y, line)
            line_y -= gap

    # Encabezado
    write("Informe Conductual EPQR-A / Selección Operativa", size=14, bold=True, gap=18)

    # Datos
    write(f"Candidato: {report['candidate_name']}", size=11)
    write(f"Evaluador responsable: {report['evaluator_email']}", size=11)
    write(f"Cargo evaluado: {report['selected_job_title']}", size=11)

    write(" ", gap=10)

    # Resultado global cargo objetivo
    write("Evaluación del cargo objetivo:", size=12, bold=True, gap=16)
    write(f"Clasificación final: {report['fit_selected']['matchLevel']}", bold=True)

    if report['fit_selected']["issues"]:
        write("Observaciones relevantes detectadas:", bold=True)
        for it in report['fit_selected']["issues"]:
            write(f" - {it}")
    else:
        write("Sin observaciones críticas adicionales en los ejes evaluados.")

    write(" ", gap=10)

    # Fortalezas
    write("Fortalezas observadas para el desempeño operacional:", size=12, bold=True, gap=16)
    if report["qual_strengths"]:
        for s in report["qual_strengths"]:
            write(f" • {s}")
    else:
        write(" • (Sin fortalezas destacables registradas)")

    write(" ", gap=10)

    # Riesgos
    write("Aspectos a vigilar / Riesgos potenciales:", size=12, bold=True, gap=16)
    if report["qual_risks"]:
        for r in report["qual_risks"]:
            write(f" • {r}")
    else:
        write(" • No se identifican riesgos conductuales relevantes.")

    write(" ", gap=10)

    # Recomendación final
    write("Recomendación final:", size=12, bold=True, gap=16)
    write(report["recommendation"])

    write(" ", gap=10)

    # Alternativas posibles
    write("Posible ajuste en otros cargos productivos de la planta:", size=12, bold=True, gap=16)
    for alt in report["all_fits"]:
        write(f"- {alt['title']}: {alt['matchLevel']}")
        write(f"   {alt['desc']}\n")

    write("Notas internas RR.HH.:", size=12, bold=True, gap=16)
    write(
        "Este informe es confidencial. No reemplaza entrevista conductual,\n"
        "observación en terreno, exámenes de salud ocupacional\n"
        "ni verificación de referencias laborales."
    )

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()

# ============================================================
# ENVÍO AUTOMÁTICO DEL PDF POR CORREO
# ============================================================
def send_report_via_email(report: dict):
    """
    Envía automáticamente el PDF generado.
    """
    if st.session_state.email_sent:
        return  # evita doble envío si se refresca

    pdf_bytes = generate_pdf_bytes(report)

    msg = EmailMessage()
    msg["Subject"] = f"Informe EPQR-A - {report['candidate_name']} - {report['selected_job_title']}"
    msg["From"] = "jo.tajtaj@gmail.com"
    msg["To"] = "jo.tajtaj@gmail.com"

    body_lines = [
        f"Candidato: {report['candidate_name']}",
        f"Cargo evaluado: {report['selected_job_title']}",
        f"Clasificación final: {report['fit_selected']['matchLevel']}",
        "",
        "Se adjunta el informe conductual resumido (fortalezas, riesgos, recomendación final).",
        "Este PDF NO incluye puntajes numéricos.",
    ]
    msg.set_content("\n".join(body_lines))

    filename = f"EPQRA_{report['candidate_name'].replace(' ','_')}.pdf"
    msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=filename)

    gmail_user = "jo.tajtaj@gmail.com"
    gmail_pass = "nlkt kujl ebdg cyts"  # clave app entregada

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(gmail_user, gmail_pass)
        server.send_message(msg)

    st.session_state.email_sent = True

# ============================================================
# CALLBACKS DE FLUJO
# ============================================================
def select_job(job_key: str):
    st.session_state.selected_job = job_key
    st.session_state.phase = "candidate"

def start_test_if_ready():
    if st.session_state.candidate_name and st.session_state.evaluator_email:
        st.session_state.phase = "test"
        st.session_state.q_idx = 0
        st.session_state.answers = {i: None for i in range(len(QUESTIONS))}

def answer_question(answer_val: int):
    """
    Registra Sí (1) o No (0) y avanza.
    En la última pregunta:
      - arma informe,
      - envía correo,
      - muestra pantalla final.
    """
    idx = st.session_state.q_idx
    st.session_state.answers[idx] = answer_val

    if idx < len(QUESTIONS) - 1:
        st.session_state.q_idx = idx + 1
        st.session_state._needs_rerun = True
    else:
        build_final_report()
        send_report_via_email(st.session_state.final_report)
        st.session_state.phase = "done"
        st.session_state._needs_rerun = True

def reset_all():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_state()

# ============================================================
# RENDER DE CADA FASE
# ============================================================
def render_phase_role():
    st.markdown(
        """
        <div class="card-header">
            <h1 style="font-size:1.25rem;">Test EPQR-A · Selección Operativa</h1>
            <div class="badge-pill">Evaluación conductual interna</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="card">
            <p style="margin-top:0;color:#374151;font-size:.9rem;line-height:1.4;">
            Este test clasifica al candidato en <b>APTO</b>, <b>RIESGO PARCIAL</b>
            o <b>NO APTO DIRECTO</b> para el cargo de planta seleccionado.
            Al finalizar, se genera un informe en PDF con fortalezas,
            riesgos y recomendación final (sin puntajes) y se envía automáticamente
            al área interna.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="card">
            <h2 style="font-size:1rem;margin:0 0 .5rem 0;color:#111827;font-weight:600;">
                Seleccione el cargo a evaluar
            </h2>
        </div>
        """,
        unsafe_allow_html=True
    )

    for job_key, info in JOB_PROFILES.items():
        c1, c2 = st.columns([0.75, 0.25])
        with c1:
            st.markdown(
                f"""
                <div class="alt-block">
                    <h4>{info["title"]}</h4>
                    <p>{info["desc"]}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        with c2:
            st.button(
                "Evaluar",
                key=f"btnsel_{job_key}",
                on_click=select_job,
                args=(job_key,),
                use_container_width=True
            )

def render_phase_candidate():
    job_key = st.session_state.selected_job
    profile = JOB_PROFILES[job_key]

    st.markdown(
        f"""
        <div class="card-header">
            <h2 style="font-size:1.1rem;">Datos del Candidato</h2>
            <div class="badge-pill">{profile["title"]}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.form(key="candidate_form", clear_on_submit=False):
        st.session_state.candidate_name = st.text_input(
            "Nombre completo del candidato",
            value=st.session_state.candidate_name,
            placeholder="Ej: Juan Pérez"
        )
        st.session_state.evaluator_email = st.text_input(
            "Correo del evaluador (RR.HH. / Supervisor)",
            value=st.session_state.evaluator_email,
            placeholder="nombre@empresa.com"
        )
        st.markdown(
            """
            <div class="muted" style="margin-top:.5rem;">
            Estos datos aparecerán en el informe PDF interno.
            </div>
            """,
            unsafe_allow_html=True
        )
        submitted = st.form_submit_button(
            "Iniciar Test",
            use_container_width=True
        )

    if submitted:
        start_test_if_ready()
        st.rerun()

def render_phase_test():
    idx = st.session_state.q_idx
    total = len(QUESTIONS)
    pct = round(((idx + 1) / total) * 100)

    # header
    st.markdown(
        f"""
        <div class="card-header">
            <h3 style="font-size:1rem;margin:0 0 .25rem 0;font-weight:600;">
                EPQR-A · {JOB_PROFILES[st.session_state.selected_job]["title"]}
            </h3>
            <div style="font-size:.8rem;opacity:.9;">
                Pregunta {idx+1} de {total} · {pct}%
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # barra progreso
    st.markdown(
        f"""
        <div class="card" style="padding-bottom:.75rem;">
            <div style="font-size:.8rem;color:#4b5563;margin-bottom:.5rem;display:flex;justify-content:space-between;">
                <span>Avance</span><span>{pct}%</span>
            </div>
            <div style="width:100%;background:#e5e7eb;border-radius:999px;height:8px;overflow:hidden;">
                <div style="
                    width:{pct}%;
                    background:linear-gradient(90deg,#2563eb 0%,#4f46e5 100%);
                    height:8px;border-radius:999px;
                    transition:width .2s;">
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # pregunta
    st.markdown(
        f"""
        <div class="card" style="margin-top:1rem;">
            <div style="font-size:1rem;color:#111827;line-height:1.4;margin-bottom:1rem;font-weight:500;">
                {QUESTIONS[idx]}
            </div>
        """,
        unsafe_allow_html=True
    )

    col_yes, col_no = st.columns(2)
    with col_yes:
        st.button(
            "Sí",
            key=f"yes_{idx}",
            help="Marcar 'Sí' y avanzar",
            on_click=answer_question,
            args=(1,),
            use_container_width=True
        )
    with col_no:
        st.button(
            "No",
            key=f"no_{idx}",
            help="Marcar 'No' y avanzar",
            on_click=answer_question,
            args=(0,),
            use_container_width=True
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # nota confidencial
    st.markdown(
        """
        <div class="card" style="background:#f9fafb;">
            <div style="display:flex;gap:.5rem;align-items:flex-start;">
                <div style="font-size:.8rem;color:#4f46e5;font-weight:600;">⚠ Confidencial</div>
                <div class="muted" style="font-size:.8rem;">
                    Responda honestamente. Esta evaluación mide estabilidad emocional,
                    apego a normas de seguridad y confiabilidad para el rol.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_phase_done():
    st.markdown(
        """
        <div class="card-header" style="background:linear-gradient(90deg,#10b981 0%,#059669 100%);box-shadow:inset 0 0 30px rgba(255,255,255,.18);">
            <div style="
                width:3.5rem;height:3.5rem;
                background:#ffffff;
                border-radius:999px;
                display:flex;align-items:center;justify-content:center;
                margin:0 auto .75rem auto;
                box-shadow:0 20px 24px -8px rgba(255,255,255,.5);
            ">
                <svg xmlns="http://www.w3.org/2000/svg" style="color:#10b981;width:1.5rem;height:1.5rem;" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
            </div>
            <div class="final-big">TEST FINALIZADO</div>
            <div class="final-sub">
                Sus respuestas han sido registradas correctamente.
                El informe interno fue generado y enviado para evaluación.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ============================================================
# ROUTER PRINCIPAL
# ============================================================
if st.session_state.phase == "role":
    render_phase_role()
elif st.session_state.phase == "candidate":
    render_phase_candidate()
elif st.session_state.phase == "test":
    render_phase_test()
elif st.session_state.phase == "done":
    render_phase_done()
else:
    st.write("Estado inválido. Reiniciando…")
    reset_all()

# ============================================================
# AUTO-RERUN DESPUÉS DE CADA RESPUESTA SIN DOBLE CLICK
# ============================================================
if st.session_state._needs_rerun:
    st.session_state._needs_rerun = False
    st.rerun()
