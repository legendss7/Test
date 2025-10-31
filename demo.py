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
    "¿Sufre usted de los nervos?",
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

# Categorías conductuales asociadas a cada pregunta.
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

DIM_COUNTS = {
    "E": CATEGORIES.count("E"),  # 7
    "N": CATEGORIES.count("N"),  # 8
    "P": CATEGORIES.count("P"),  # 8
    "S": CATEGORIES.count("S"),  # 7
}

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
    if "scores_raw" not in st.session_state:
        st.session_state.scores_raw = {"E": 0, "N": 0, "P": 0, "S": 0}
    if "scores_scaled" not in st.session_state:
        st.session_state.scores_scaled = {"E": 0, "N": 0, "P": 0, "S": 0}
    if "final_report" not in st.session_state:
        st.session_state.final_report = None
    if "_needs_rerun" not in st.session_state:
        st.session_state._needs_rerun = False
    if "email_sent" not in st.session_state:
        st.session_state.email_sent = False

init_state()

# ============================================================
# CÁLCULO DE PUNTAJES CRUDOS Y ESCALADOS
# ============================================================
def compute_scores_raw(answers: Dict[int, int]) -> Dict[str, int]:
    """
    answers[i] = 1 si respondió Sí, 0 si respondió No.

    Para E y N sumamos Sí (1).
    Para P y S sumamos No (0) como punto "positivo":
      - en P/S: No=1, Sí=0.
    """
    scores = {"E": 0, "N": 0, "P": 0, "S": 0}
    for idx, cat in enumerate(CATEGORIES):
        ans = answers.get(idx)
        if ans is None:
            continue
        if cat in ["P", "S"]:
            val = 1 if ans == 0 else 0
        else:
            val = ans
        scores[cat] += val
    return scores

def scale_scores_0_to_6(raw_scores: Dict[str, int]) -> Dict[str, int]:
    """
    Normaliza cada dimensión a una escala común 0–6
    para poder compararla con los rangos del cargo.
    """
    out = {}
    for dim, raw_val in raw_scores.items():
        total_items_dim = DIM_COUNTS[dim]
        scaled = round((raw_val / total_items_dim) * 6)
        out[dim] = scaled
    return out

# ============================================================
# CLASIFICACIÓN DE APTITUD (USA ESCALA 0–6)
# ============================================================
def evaluate_fit_for_job(scaled_scores: Dict[str, int], profile: dict):
    """
    Compara al candidato con el perfil del cargo usando los
    puntajes escalados (0–6). Además arma info para RRHH.
    Reglas:
      - contamos cuántas dimensiones (E,N,P,S) están en rango.
      - >=3 en rango    => APTO
      - ==2 en rango    => RIESGO PARCIAL
      - <=1 en rango    => NO APTO DIRECTO
    """
    req = profile["requirements"]
    issues = []
    dim_fit = {}
    in_range_count = 0
    per_dim_detail = {}

    for dim in ["E", "N", "P", "S"]:
        val = scaled_scores[dim]
        mn = req[dim]["min"]
        mx = req[dim]["max"]
        ok = (val >= mn and val <= mx)
        dim_fit[dim] = ok
        per_dim_detail[dim] = {
            "scaled": val,
            "expected_min": mn,
            "expected_max": mx,
            "ok": ok,
        }
        if ok:
            in_range_count += 1
        else:
            if val < mn:
                issues.append(f"{dim}: bajo el rango esperado para {profile['title']}")
            elif val > mx:
                issues.append(f"{dim}: sobre el rango esperado para {profile['title']}")

    if in_range_count >= 3:
        level = "APTO"
    elif in_range_count == 2:
        level = "RIESGO PARCIAL"
    else:
        level = "NO APTO DIRECTO"

    # % ajuste = dimensiones en rango / 4
    match_pct = round((in_range_count / 4) * 100)

    return {
        "matchLevel": level,
        "issues": issues,
        "dim_fit": dim_fit,
        "in_range_count": in_range_count,
        "match_pct": match_pct,
        "per_dim_detail": per_dim_detail,  # para tabla numérica en PDF
    }

# ============================================================
# INTERPRETACIÓN CUALITATIVA (FORTALEZAS / RIESGOS)
# ============================================================
def build_strengths_and_risks(raw_scores: Dict[str, int]) -> Dict[str, List[str]]:
    """
    Devuelve fortalezas y riesgos textuales interpretando la
    forma en que respondió el candidato (sin esconder contradicciones).
    """
    strengths = []
    risks = []

    N = raw_scores["N"]  # alto N = más tensión emocional reportada
    E = raw_scores["E"]  # alto E = más sociable/asertivo
    P = raw_scores["P"]  # alto P = más "control impulsivo" según inversión
    S = raw_scores["S"]  # alto S = más apego a normas según inversión

    # N (control emocional / manejo del estrés)
    if N <= 3:
        strengths.append("Muestra control emocional en situaciones de presión.")
    else:
        risks.append("Reporta nerviosismo o irritabilidad bajo presión directa de planta.")

    # S (apego a normas / honestidad declarada)
    if S >= 4:
        strengths.append("Declara respeto por las normas, reporte transparente y cumplimiento formal.")
    else:
        risks.append("Podría requerir supervisión adicional para asegurar apego estricto a normas y protocolos.")

    # E (comunicación / visibilidad)
    if E >= 3:
        strengths.append("Tiende a comunicarse, dar indicaciones y pedir apoyo cuando es necesario.")
    else:
        strengths.append("Muestra un perfil más reservado y con baja confrontación directa.")
        risks.append("Podría no escalar incidentes críticos de inmediato si no se le consulta directamente.")

    # P (tolerancia a la presión / control conductual)
    if 2 <= P <= 5:
        strengths.append("Presenta tolerancia a la presión operativa y capacidad de actuar en escenarios exigentes.")
    elif P < 2:
        strengths.append("Estilo cooperativo, poca confrontación.")
        risks.append("Puede tener dificultades para frenar conductas inseguras de terceros en piso de planta.")
    else:  # P > 5
        risks.append("Podría actuar por cuenta propia sin informar, lo que implica riesgo de desalineación con el supervisor.")

    return {"strengths": strengths, "risks": risks}

# ============================================================
# ARMAR INFORME FINAL (SE GUARDA EN SESIÓN)
# ============================================================
def build_final_report():
    """
    Arma todo lo que va al PDF/correo y lo deja en sesión.
    Incluye valores numéricos.
    """
    # 1. scores crudos y escalados
    raw_scores = compute_scores_raw(st.session_state.answers)
    scaled = scale_scores_0_to_6(raw_scores)

    st.session_state.scores_raw = raw_scores
    st.session_state.scores_scaled = scaled

    # 2. cargo seleccionado
    sel_job_key = st.session_state.selected_job
    sel_profile = JOB_PROFILES[sel_job_key]

    # 3. evaluación contra ese cargo
    fit_selected = evaluate_fit_for_job(scaled, sel_profile)

    # 4. fortalezas / riesgos (texto)
    qual = build_strengths_and_risks(raw_scores)

    # 5. recomendación final
    if fit_selected["matchLevel"] == "APTO":
        rec_text = (
            "El perfil declarado es consistente con las exigencias conductuales "
            f"del cargo {sel_profile['title']}. Se considera capacitado para "
            "asumir funciones propias del puesto."
        )
    elif fit_selected["matchLevel"] == "RIESGO PARCIAL":
        rec_text = (
            "El candidato presenta un ajuste parcial al cargo "
            f"{sel_profile['title']}. Se sugiere entrevista conductual y "
            "observación directa en terreno antes de asignar turno definitivo."
        )
    else:
        rec_text = (
            f"El candidato muestra diferencias relevantes frente al perfil "
            f"esperado para {sel_profile['title']}. Requiere evaluación "
            "adicional antes de asignar tareas críticas o de seguridad."
        )

    # 6. mapa de ajuste a otros cargos (para RRHH)
    all_fits = []
    for key, prof in JOB_PROFILES.items():
        fit_other = evaluate_fit_for_job(scaled, prof)
        all_fits.append({
            "job_key": key,
            "title": prof["title"],
            "desc": prof["desc"],
            "matchLevel": fit_other["matchLevel"],
            "match_pct": fit_other["match_pct"],
        })

    st.session_state.final_report = {
        "candidate_name": st.session_state.candidate_name,
        "evaluator_email": st.session_state.evaluator_email,
        "selected_job_key": sel_job_key,
        "selected_job_title": sel_profile["title"],

        # numérico
        "raw_scores": raw_scores,           # bruto por dimensión
        "scaled_scores": scaled,            # 0-6 por dimensión
        "fit_selected": fit_selected,       # matchLevel, match_pct, per_dim_detail
        "all_fits": all_fits,               # otros cargos

        # descriptivo
        "qual_strengths": qual["strengths"],
        "qual_risks": qual["risks"],
        "recommendation": rec_text,
    }

# ============================================================
# GENERAR PDF (AHORA CON NÚMEROS)
# ============================================================
def generate_pdf_bytes(report: dict) -> bytes:
    """
    Genera PDF interno RR.HH. incluyendo:
    - puntajes crudos
    - puntajes escala 0–6
    - % ajuste al cargo
    - tabla de cada dimensión vs rango esperado
    - fortalezas / riesgos / recomendación
    """
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    line_y = height - 40

    def write(txt, size=10, bold=False, gap=14):
        nonlocal line_y
        if line_y < 60:
            c.showPage()
            line_y = height - 40
        if bold:
            c.setFont("Helvetica-Bold", size)
        else:
            c.setFont("Helvetica", size)
        for line in txt.split("\n"):
            c.drawString(40, line_y, line)
            line_y -= gap

    def write_table_header():
        nonlocal line_y
        c.setFont("Helvetica-Bold", 9)
        headers = [
            "DIM", "Bruto", "Escala 0-6", "Rango Cargo", "¿En rango?"
        ]
        x_positions = [40, 80, 130, 200, 300]
        if line_y < 80:
            c.showPage()
            line_y = height - 40
        line_y -= 4
        for x, h in zip(x_positions, headers):
            c.drawString(x, line_y, h)
        line_y -= 12
        c.setFont("Helvetica", 9)

    def write_table_row(dim, raw_val, scaled_val, mn, mx, ok_flag):
        nonlocal line_y
        if line_y < 60:
            c.showPage()
            line_y = height - 40
            write_table_header()
        x_positions = [40, 80, 130, 200, 300]
        cells = [
            dim,
            str(raw_val),
            str(scaled_val),
            f"{mn}-{mx}",
            "✔" if ok_flag else "✖",
        ]
        for x, cell in zip(x_positions, cells):
            c.drawString(x, line_y, cell)
        line_y -= 12

    # Encabezado
    write("Informe Conductual EPQR-A / Selección Operativa", size=14, bold=True, gap=18)

    write(f"Candidato: {report['candidate_name']}", size=11)
    write(f"Evaluador responsable: {report['evaluator_email']}", size=11)
    write(f"Cargo evaluado: {report['selected_job_title']}", size=11)

    cargo_fit = report["fit_selected"]
    write(f"Ajuste declarado al cargo: {cargo_fit['matchLevel']} ({cargo_fit['match_pct']}% de ajuste)", size=11, bold=True)

    write(" ", gap=10)

    # Tabla numérica por dimensión
    write("Resumen numérico por dimensión:", size=12, bold=True, gap=16)
    write_table_header()

    # usamos per_dim_detail que tiene: scaled, expected_min, expected_max, ok
    for dim in ["E", "N", "P", "S"]:
        detail = cargo_fit["per_dim_detail"][dim]
        write_table_row(
            dim=dim,
            raw_val=report["raw_scores"][dim],
            scaled_val=detail["scaled"],
            mn=detail["expected_min"],
            mx=detail["expected_max"],
            ok_flag=detail["ok"]
        )

    write(" ", gap=10)

    # Observaciones fuera de rango
    write("Dimensiones fuera de rango del cargo:", size=11, bold=True, gap=16)
    if cargo_fit["issues"]:
        for it in cargo_fit["issues"]:
            write(f" - {it}")
    else:
        write(" - Todas las dimensiones están dentro del rango esperado para este cargo.")

    write(" ", gap=10)

    # Fortalezas / Riesgos
    write("Fortalezas conductuales observadas:", size=12, bold=True, gap=16)
    if report["qual_strengths"]:
        for s in report["qual_strengths"]:
            write(f" • {s}")
    else:
        write(" • (Sin fortalezas destacables registradas)")

    write(" ", gap=10)

    write("Riesgos / puntos de vigilancia:", size=12, bold=True, gap=16)
    if report["qual_risks"]:
        for r in report["qual_risks"]:
            write(f" • {r}")
    else:
        write(" • Sin riesgos críticos declarados.")

    write(" ", gap=10)

    # Recomendación final
    write("Recomendación final para este cargo:", size=12, bold=True, gap=16)
    write(report["recommendation"])

    write(" ", gap=10)

    # Otros cargos
    write("Ajuste orientativo en otros cargos productivos:", size=12, bold=True, gap=16)
    for alt in report["all_fits"]:
        write(f"- {alt['title']}: {alt['matchLevel']}  ({alt['match_pct']}% de ajuste)")
        write(f"   {alt['desc']}\n")

    write("Notas RR.HH.:", size=12, bold=True, gap=16)
    write(
        "Este informe es confidencial. No reemplaza entrevista conductual, "
        "observación en terreno, exámenes de salud ocupacional ni verificación de referencias."
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
        return

    pdf_bytes = generate_pdf_bytes(report)

    msg = EmailMessage()
    msg["Subject"] = f"Informe EPQR-A - {report['candidate_name']} - {report['selected_job_title']}"
    msg["From"] = "jo.tajtaj@gmail.com"
    msg["To"] = "jo.tajtaj@gmail.com"

    msg.set_content(
        "Se adjunta el informe conductual EPQR-A.\n"
        "Incluye puntajes crudos, escala 0–6, % de ajuste al cargo,\n"
        "fortalezas, riesgos y recomendación final.\n"
    )

    filename = f"EPQRA_{report['candidate_name'].replace(' ','_')}.pdf"
    msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=filename)

    gmail_user = "jo.tajtaj@gmail.com"
    gmail_pass = "nlkt kujl ebdg cyts"  # clave app que tú definiste

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
    Guarda Sí (1) o No (0) y avanza.
    Al terminar:
      - arma informe final con números
      - envía el correo
      - muestra pantalla final verde
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
            Este test clasifica al candidato como <b>APTO</b>, <b>RIESGO PARCIAL</b>
            o <b>NO APTO DIRECTO</b> para el cargo seleccionado.
            Al finalizar, se genera un informe PDF con puntajes,
            % de ajuste al cargo, fortalezas, riesgos y recomendación final.
            El PDF se envía automáticamente al correo interno.
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

    st.markdown(
        """
        <div class="card" style="background:#f9fafb;">
            <div style="display:flex;gap:.5rem;align-items:flex-start;">
                <div style="font-size:.8rem;color:#4f46e5;font-weight:600;">⚠ Confidencial</div>
                <div class="muted" style="font-size:.8rem;">
                    Responda honestamente. Esta evaluación mide manejo emocional,
                    apego a normas y confiabilidad operativa.
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
