import streamlit as st
from typing import Dict
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

.kpi-box{
  background:#fff;
  border:1px solid #e5e7eb;
  border-radius:.75rem;
  padding:.75rem .9rem;
  box-shadow:0 10px 20px -6px rgba(0,0,0,.08);
  margin-bottom:1rem;
}
.kpi-label{
  font-size:.7rem;
  text-transform:uppercase;
  letter-spacing:.03em;
  color:#6b7280;
  margin-bottom:.25rem;
}
.kpi-value{
  font-size:1.5rem;
  font-weight:700;
  color:#111827;
  line-height:1.2;
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

/* Botones Sí / No */
.btn-yes{
  background:#10b981;
  width:100%;
  color:#fff;
  font-weight:600;
  text-align:center;
  border-radius:.75rem;
  padding:.9rem 1rem;
  border:0;
  box-shadow:0 20px 24px -8px rgba(16,185,129,.4);
  font-size:1rem;
}
.btn-no{
  background:#ef4444;
  width:100%;
  color:#fff;
  font-weight:600;
  text-align:center;
  border-radius:.75rem;
  padding:.9rem 1rem;
  border:0;
  box-shadow:0 20px 24px -8px rgba(239,68,68,.4);
  font-size:1rem;
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

# 24 originales + 6 adicionales en la misma línea conductual / emocional.
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

    # Ítems nuevos agregados para llegar a 30
    "¿Pierde la calma fácilmente cuando algo no resulta en el trabajo?",
    "¿Le resulta natural dar instrucciones claras a otras personas?",
    "¿Alguna vez ocultó un error propio para evitar un llamado de atención?",
    "¿Le cuesta desconectarse mentalmente de las preocupaciones?",
    "¿Siente que puede mantener la cabeza fría en una emergencia?",
    "¿Le cuesta seguir reglas que considera innecesarias?"
]

# Asignamos cada ítem a una dimensión:
# E = Extraversión / Asertividad social
# N = Neuroticismo / Inestabilidad emocional
# P = Psicoticismo / Impulsividad / dureza conductual
# S = Sinceridad / Apego a normas / deseabilidad social
#
# Para mantener coherencia con las 24 primeras, seguimos el mismo mapeo que venías usando
# y agregamos categorías razonables para las 6 nuevas.
CATEGORIES = [
    "N", "E", "P", "E", "S", "P", "S", "P", "N", "S",
    "N", "P", "E", "N", "E", "P", "S", "N", "S", "E",
    "N", "P", "E", "S",
    # nuevas
    "N",  # pierde la calma fácilmente -> emocional
    "E",  # dar instrucciones claras -> extraversión/asertividad
    "S",  # ocultó error -> sinceridad/adh.normas invertida
    "N",  # no desconectarse de preocupaciones -> emocional
    "P",  # cabeza fría en emergencia -> dureza/control impulsivo (lo tratamos tipo P directo)
    "P",  # saltarse reglas innecesarias -> impulsividad / desafío normas
]

# ============================================================
# PERFILES DE CARGO
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
# ESTADO (SESSION_STATE)
# fases: "role" -> "candidate" -> "test" -> "done"
# "done" = pantalla final verde SIN mostrar informe
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
# CÁLCULO DE PUNTAJES Y APTITUD
# ============================================================
def compute_scores(answers: Dict[int, int]) -> Dict[str, int]:
    """
    answers[i] = 1 si respondió Sí, 0 si respondió No.

    Regla:
    - Para E y N sumamos "Sí" (1) directo.
    - Para P y S seguimos tu lógica anterior: se interpreta que
      responder "No" (0) suma 1 punto de "control/ajuste", y "Sí" suma 0.
      Eso penaliza conductas impulsivas o poco sinceras.
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


def evaluate_fit_for_job(scores: Dict[str, int], profile: dict):
    """
    Devuelve nivel de ajuste al cargo:
    - APTO: cumple todos los rangos
    - RIESGO PARCIAL: sólo 1 desajuste
    - NO APTO DIRECTO: 2 o más desajustes
    """
    req = profile["requirements"]
    issues = []
    for scale in ["E", "N", "P", "S"]:
        val = scores[scale]
        mn = req[scale]["min"]
        mx = req[scale]["max"]
        if val < mn:
            issues.append(f"{scale} bajo (mín {mn}, obtuvo {val})")
        elif val > mx:
            issues.append(f"{scale} alto (máx {mx}, obtuvo {val})")

    if len(issues) == 0:
        level = "APTO"
    elif len(issues) == 1:
        level = "RIESGO PARCIAL"
    else:
        level = "NO APTO DIRECTO"

    return {"matchLevel": level, "issues": issues}


def build_final_report():
    """
    Calcula puntajes, evalúa cargo elegido y también otros cargos.
    Guarda todo en session_state.final_report.
    """
    scores = compute_scores(st.session_state.answers)
    st.session_state.scores = scores

    sel_job_key = st.session_state.selected_job
    sel_profile = JOB_PROFILES[sel_job_key]

    fit_selected = evaluate_fit_for_job(scores, sel_profile)

    all_fits = []
    for key, prof in JOB_PROFILES.items():
        fit = evaluate_fit_for_job(scores, prof)
        all_fits.append({
            "job_key": key,
            "title": prof["title"],
            "desc": prof["desc"],
            "matchLevel": fit["matchLevel"],
            "issues": fit["issues"],
        })

    st.session_state.final_report = {
        "candidate_name": st.session_state.candidate_name,
        "evaluator_email": st.session_state.evaluator_email,
        "selected_job_key": sel_job_key,
        "selected_job_title": sel_profile["title"],
        "scores": scores,
        "fit_selected": fit_selected,
        "all_fits": all_fits,
    }

# ============================================================
# GENERAR PDF (para enviar por correo)
# ============================================================
def generate_pdf_bytes(report: dict) -> bytes:
    """
    Crea un PDF simple (A4) con los resultados completos.
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

    write("Informe EPQR-A / Selección Operativa", size=14, bold=True, gap=18)
    write(f"Candidato: {report['candidate_name']}", size=11, bold=False)
    write(f"Evaluador: {report['evaluator_email']}", size=11, bold=False)
    write(f"Cargo evaluado: {report['selected_job_title']}", size=11, bold=False)
    write(" ", gap=10)

    write("Puntajes escalares:", size=12, bold=True, gap=16)
    scores = report["scores"]
    write(f"E (Sociabilidad / Asertividad): {scores['E']}")
    write(f"N (Inestabilidad emocional): {scores['N']}")
    write(f"P (Impulsividad / Dureza)*: {scores['P']}")
    write(f"S (Apego a normas / Honestidad percibida)*: {scores['S']}")
    write("*En P y S una respuesta 'No' suma control/normativa.\n", gap=16)

    fit_sel = report["fit_selected"]
    write("Evaluación del cargo postulado:", size=12, bold=True, gap=16)
    write(f"Resultado global: {fit_sel['matchLevel']}", bold=True)
    if len(fit_sel["issues"]) == 0:
        write("Observaciones críticas: Ninguna")
    else:
        write("Observaciones críticas:", bold=True)
        for it in fit_sel["issues"]:
            write(f" - {it}")

    write(" ", gap=10)
    write("Ajuste potencial en otros cargos productivos:", size=12, bold=True, gap=16)
    for fit in report["all_fits"]:
        write(f"- {fit['title']}: {fit['matchLevel']}", bold=True)
        if fit["issues"]:
            for it in fit["issues"]:
                write(f"   · {it}")
        else:
            write("   · Sin observaciones críticas")
        write(f"   Perfil del rol: {fit['desc']}\n")

    write("Notas de uso interno:", size=12, bold=True, gap=16)
    write(
        "Este informe es confidencial. No reemplaza entrevista conductual,\n"
        "pruebas técnicas ni evaluaciones médicas. Uso exclusivo RR.HH."
    )

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()

# ============================================================
# ENVÍO DE CORREO AUTOMÁTICO CON PDF ADJUNTO
# ============================================================
def send_report_via_email(report: dict):
    """
    Envía automáticamente el PDF a la casilla indicada.
    Se usa la casilla fija y la clave app que entregaste.
    """
    if st.session_state.email_sent:
        return  # evita mandarlo más de una vez

    pdf_bytes = generate_pdf_bytes(report)

    msg = EmailMessage()
    msg["Subject"] = f"Informe EPQR-A - {report['candidate_name']} - {report['selected_job_title']}"
    msg["From"] = "jo.tajtaj@gmail.com"
    msg["To"] = "jo.tajtaj@gmail.com"

    body_lines = [
        f"Candidato: {report['candidate_name']}",
        f"Cargo evaluado: {report['selected_job_title']}",
        f"Resultado global: {report['fit_selected']['matchLevel']}",
        "",
        "Se adjunta PDF con detalle completo (puntajes, riesgos, ajuste a otros cargos).",
    ]
    msg.set_content("\n".join(body_lines))

    # Adjuntar PDF
    filename = f"EPQRA_{report['candidate_name'].replace(' ','_')}.pdf"
    msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=filename)

    # SMTP Gmail (puerto TLS 587)
    gmail_user = "jo.tajtaj@gmail.com"
    gmail_pass = "nlkt kujl ebdg cyts"  # app password entregada

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
    answer_val = 1 (Sí) o 0 (No)
    Guarda respuesta y avanza automáticamente.
    Al terminar la última pregunta:
      - Calcula el informe
      - Lo guarda en session_state
      - Envía el correo con el PDF
      - Cambia a fase "done"
    """
    idx = st.session_state.q_idx
    st.session_state.answers[idx] = answer_val

    # ¿Quedan más preguntas?
    if idx < len(QUESTIONS) - 1:
        st.session_state.q_idx = idx + 1
        st.session_state._needs_rerun = True
    else:
        # Última pregunta -> generar informe + enviar + pantalla final
        build_final_report()
        send_report_via_email(st.session_state.final_report)
        st.session_state.phase = "done"
        st.session_state._needs_rerun = True

def reset_all():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_state()


# ============================================================
# RENDER FASES
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
            Este test clasifica al candidato en <b>APTO</b>,
            <b>RIESGO PARCIAL</b> o <b>NO APTO DIRECTO</b> según el
            cargo productivo seleccionado. Se envía informe completo por correo interno.
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
            Esta información será usada para generar y enviar el informe PDF interno.
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

    # HEADER
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

    # BARRA PROGRESO
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

    # PREGUNTA + BOTONES
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

    # Mensaje confidencial
    st.markdown(
        """
        <div class="card" style="background:#f9fafb;">
            <div style="display:flex;gap:.5rem;align-items:flex-start;">
                <div style="font-size:.8rem;color:#4f46e5;font-weight:600;">⚠ Confidencial</div>
                <div class="muted" style="font-size:.8rem;">
                    Responda honestamente. Esta evaluación mide estabilidad emocional,
                    ajuste a normas de seguridad, confiabilidad y autocontrol
                    bajo presión en ambiente productivo.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_phase_done():
    # Pantalla final verde y nada más.
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
# AUTO-RERUN DESPUÉS DE CADA RESPUESTA SIN DOBLE CLIC
# ============================================================
if st.session_state._needs_rerun:
    st.session_state._needs_rerun = False
    st.rerun()
