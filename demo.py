import streamlit as st
from typing import Dict
import smtplib
from email.message import EmailMessage
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors

# ============================================================
# CONFIG GENERAL STREAMLIT
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
# PREGUNTAS (30 ÍTEMS) Y CATEGORÍAS EPQR-A ADAPTADO
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

# CATEGORÍAS EPQR-A (adaptadas)
# E = Extraversión / energía social / iniciativa interpersonal
# N = Neuroticismo → reportaremos como Estabilidad Emocional invertida
# P = Dureza Conductual / estilo directo / tolerancia a conflicto
# S = Consistencia / Autopresentación / deseabilidad social
CATEGORIES = [
    "N", "E", "S", "E", "S", "P", "S", "P", "N", "S",
    "N", "P", "E", "N", "E", "P", "S", "N", "S", "E",
    "N", "P", "E", "S", "N", "E", "S", "N", "P", "P",
]

DIM_COUNTS = {
    "E": CATEGORIES.count("E"),
    "N": CATEGORIES.count("N"),
    "P": CATEGORIES.count("P"),
    "S": CATEGORIES.count("S"),
}

# ============================================================
# PERFILES DE CARGO Y RANGOS ESPERADOS (0–6)
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
        "desc": "Coordinación de equipos bajo presión, comunicación clara de instrucciones y control de desvíos.",
    },
    "tecnico": {
        "title": "Técnico de Mantenimiento",
        "requirements": {
            "E": {"min": 1, "max": 4},
            "N": {"min": 0, "max": 3},
            "P": {"min": 2, "max": 5},
            "S": {"min": 4, "max": 6},
        },
        "desc": "Diagnóstico técnico, reacción ante fallas, foco en procedimientos y reporte transparente.",
    },
    "logistica": {
        "title": "Personal de Logística",
        "requirements": {
            "E": {"min": 2, "max": 5},
            "N": {"min": 0, "max": 3},
            "P": {"min": 1, "max": 4},
            "S": {"min": 4, "max": 6},
        },
        "desc": "Movimiento ordenado de insumos, coordinación entre áreas y registro fiable.",
    },
}

# ============================================================
# ESTADO GLOBAL DE LA APP
# phases: "role" -> "candidate" -> "test" -> "done"
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
    if "final_report" not in st.session_state:
        st.session_state.final_report = None
    if "_needs_rerun" not in st.session_state:
        st.session_state._needs_rerun = False
    if "email_sent" not in st.session_state:
        st.session_state.email_sent = False

init_state()

# ============================================================
# CÁLCULO DE PUNTAJES
# ============================================================
def compute_raw_scores(answers: Dict[int, int]) -> Dict[str, int]:
    """
    EPQR-A binario Sí(1)/No(0).
    Para P y S interpretamos "No"(0) como control/ajuste normativo → suma 1.
    Para E y N interpretamos "Sí"(1) como presencia del rasgo → suma 1.
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


def scale_scores_to_6(raw_scores: Dict[str, int]) -> Dict[str, int]:
    """
    Normaliza cada dimensión a escala 0–6 para comparar con rangos por cargo.
    scaled = round( (raw / max_raw_dim) * 6 )
    """
    scaled = {}
    for dim, raw_val in raw_scores.items():
        max_dim_items = DIM_COUNTS[dim]
        scaled_val = round((raw_val / max_dim_items) * 6)
        scaled[dim] = scaled_val
    return scaled


def level_label_numeric(scaled_val: int) -> str:
    """
    Pasa valor 0–6 a Bajo / Medio / Alto.
    """
    if scaled_val <= 2:
        return "Bajo"
    elif scaled_val <= 4:
        return "Medio"
    else:
        return "Alto"


def evaluate_fit_for_job(scaled_scores: Dict[str, int], profile: dict):
    """
    Compara con los requisitos del cargo (0–6 por dimensión).
    Devuelve matchLevel = APTO / RIESGO PARCIAL / NO APTO DIRECTO
    + match_pct, issues.
    """
    req = profile["requirements"]
    in_range_count = 0
    issues = []

    for dim in ["E", "N", "P", "S"]:
        val = scaled_scores[dim]
        mn = req[dim]["min"]
        mx = req[dim]["max"]
        ok = (val >= mn and val <= mx)
        if ok:
            in_range_count += 1
        else:
            if val < mn:
                issues.append(f"{dim}: bajo el rango esperado para {profile['title']}")
            elif val > mx:
                issues.append(f"{dim}: sobre el rango esperado para {profile['title']}")

    if in_range_count >= 3:
        matchLevel = "APTO"
    elif in_range_count == 2:
        matchLevel = "RIESGO PARCIAL"
    else:
        matchLevel = "NO APTO DIRECTO"

    match_pct = round((in_range_count / 4) * 100)

    return {
        "matchLevel": matchLevel,
        "match_pct": match_pct,
        "issues": issues,
        "in_range_count": in_range_count,
    }

# ============================================================
# DESCRIPTORES CUALITATIVOS
# ============================================================
def describe_extraversión(level:str):
    if level == "Alto":
        return {
            "conductual": "mostrarse activo/a socialmente, tomar la palabra y vincularse con otras personas de manera visible",
            "impacto": "la interacción directa, la comunicación cara a cara y la coordinación verbal",
            "contexto": "roles donde se requiere presencia frente a otros, dar instrucciones o resolver situaciones con personas en tiempo real",
        }
    if level == "Medio":
        return {
            "conductual": "adaptar su nivel de interacción según la situación, combinando espacios de colaboración con momentos de trabajo individual",
            "impacto": "mantener comunicación funcional cuando es necesaria",
            "contexto": "entornos donde se requieren intercambios puntuales pero también foco operativo",
        }
    return {
        "conductual": "mantener un perfil más reservado y evitar la exposición innecesaria",
        "impacto": "la concentración en la tarea y el trabajo silencioso",
        "contexto": "funciones estructuradas, con menor necesidad de interacción social constante",
    }

def describe_estabilidad(level:str):
    if level == "Alto":
        return {
            "estres": "mantener estabilidad emocional y una respuesta relativamente controlada ante presión o cambio",
            "impacto": "sostener ritmo en escenarios de alta demanda sin perder foco inmediato",
            "apoyo": "poca contención adicional en el día a día, salvo en crisis prolongadas",
        }
    if level == "Medio":
        return {
            "estres": "mostrar cierta inquietud bajo presión, pero recuperarse con apoyos claros y prioridades bien definidas",
            "impacto": "necesitar claridad operativa cuando hay exigencia sostenida",
            "apoyo": "beneficiarse de instrucciones directas cuando hay cambios bruscos",
        }
    return {
        "estres": "experimentar preocupación con mayor intensidad en escenarios de mucha presión",
        "impacto": "requerir contención verbal, validación rápida o acompañamiento cercano cuando hay urgencia prolongada",
        "apoyo": "beneficiarse de retroalimentación calmada y pasos concretos",
    }

def describe_dureza(level:str):
    if level == "Alto":
        return {
            "interpersonal": "expresarse de manera directa y enfocada en la tarea, con baja tolerancia a distracciones",
            "prioriza": "el resultado operativo y el cumplimiento inmediato",
            "conflicto": "tomar decisiones rápidas incluso si hay desacuerdo",
            "funcional": "ambientes en que se requiere firmeza para sostener estándares de producción o seguridad",
            "sensibilidad": "equipos que esperan acompañamiento emocional constante",
        }
    if level == "Medio":
        return {
            "interpersonal": "equilibrar franqueza con cierta lectura del entorno",
            "prioriza": "cumplimiento operativo sin generar fricción innecesaria",
            "conflicto": "marcar límites cuando es necesario, pero con disposición a coordinar",
            "funcional": "contextos donde se requiere foco en resultados pero también trabajo en equipo",
            "sensibilidad": "modelos muy rígidos o demasiado confrontativos",
        }
    return {
        "interpersonal": "mantener un estilo más cooperativo y de baja confrontación directa",
        "prioriza": "la relación interpersonal y la reducción de tensiones",
        "conflicto": "evitar choques abiertos y preferir acuerdos",
        "funcional": "equipos colaborativos que valoran trato diplomático",
        "sensibilidad": "escenarios que exigen frenar conductas de otros con firmeza inmediata",
    }

def describe_sinceridad(level:str):
    if level == "Alto":
        return {
            "transparencia": "responder de manera consistente con normas formales y expectativas de la organización",
            "imagen": "cuida activamente la forma en que se muestra frente a figuras de autoridad",
        }
    if level == "Medio":
        return {
            "transparencia": "presentarse de forma razonablemente directa, ajustando el discurso según contexto",
            "imagen": "busca quedar bien evaluado sin forzar demasiado la autoimagen",
        }
    return {
        "transparencia": "entregar respuestas más espontáneas y menos filtradas socialmente",
        "imagen": "muestra menor esfuerzo explícito por gestionar la impresión que genera",
    }

# ============================================================
# RESUMENES BULLETS
# ============================================================
def build_strength_bullets(levelE, levelN, levelP, levelS):
    out = []
    if levelE in ["Alto", "Medio"]:
        out.append("Disposición a comunicarse de manera clara frente a otras personas cuando la tarea lo requiere.")
    else:
        out.append("Capacidad para mantener foco individual en la tarea sin necesidad de alta interacción social.")
    if levelN in ["Alto", "Medio"]:
        out.append("Tendencia a sostener el ritmo de trabajo en escenarios de presión operativa inmediata.")
    else:
        out.append("Capacidad para identificar rápidamente cuando una situación le resulta demandante y pedir apoyo.")
    if levelP in ["Alto", "Medio"]:
        out.append("Capacidad para marcar prioridades operativas y sostener criterios de cumplimiento.")
    else:
        out.append("Preferencia por resolver diferencias mediante diálogo y acuerdos antes que confrontación directa.")
    if levelS in ["Alto", "Medio"]:
        out.append("Orientación a cumplir normas formales y protocolos establecidos.")
    else:
        out.append("Estilo espontáneo que puede facilitar conversaciones francas en terreno.")
    out.append("Tendencia a mantener la tarea como eje central del desempeño diario.")
    return out[:5]

def build_support_bullets(levelE, levelN, levelP, levelS):
    out = []
    if levelN == "Bajo":
        out.append("Podría requerir contención breve y recordatorios concretos en escenarios de alta urgencia sostenida.")
    if levelP == "Alto":
        out.append("Se sugiere acordar normas explícitas de comunicación para evitar que su estilo directo sea percibido como confrontacional.")
    elif levelP == "Bajo":
        out.append("Podría beneficiarse de apoyo para sostener límites firmes cuando otras personas no cumplen estándares operativos.")
    if levelE == "Bajo":
        out.append("Puede requerir que se valide explícitamente su voz en reuniones, para que comunique incidentes críticos a tiempo.")
    if levelS == "Alto":
        out.append("Se sugiere retroalimentación directa y específica, ya que la persona puede tender a responder según lo socialmente esperado.")
    if not out:
        out.append("Podría requerir retroalimentación clara y temprana cuando cambian prioridades de forma brusca.")
    return out[:4]

# ============================================================
# ARMAR INFORME NARRATIVO + RESUMEN PARA PDF
# ============================================================
def build_final_report():
    answers = st.session_state.answers
    candidate = st.session_state.candidate_name
    evaluator = st.session_state.evaluator_email
    cargo_key = st.session_state.selected_job
    cargo_title = JOB_PROFILES[cargo_key]["title"]
    fecha_eval = datetime.now().strftime("%d/%m/%Y %H:%M")

    raw_scores = compute_raw_scores(answers)
    scaled_scores = scale_scores_to_6(raw_scores)

    # niveles cualitativos por dimensión
    levelE = level_label_numeric(scaled_scores["E"])
    levelN_stability = level_label_numeric(6 - scaled_scores["N"])  # Estabilidad emocional
    levelP = level_label_numeric(scaled_scores["P"])
    levelS = level_label_numeric(scaled_scores["S"])

    # descripciones conductuales
    dE = describe_extraversión(levelE)
    dN = describe_estabilidad(levelN_stability)
    dP = describe_dureza(levelP)
    dS = describe_sinceridad(levelS)

    # ajuste con el cargo
    fit_info = evaluate_fit_for_job(scaled_scores, JOB_PROFILES[cargo_key])

    if fit_info["matchLevel"] == "APTO":
        cierre_final = (
            f"Conclusión: El perfil evaluado se considera GLOBALMENTE CONSISTENTE "
            f"con las exigencias conductuales habituales del cargo {cargo_title}."
        )
    else:
        cierre_final = (
            f"Conclusión: El perfil evaluado REQUIERE REVISIÓN ADICIONAL antes de confirmar "
            f"idoneidad para el cargo {cargo_title}. Se sugiere profundizar en entrevista "
            f"focalizada y verificación de referencias."
        )

    fortalezas = build_strength_bullets(levelE, levelN_stability, levelP, levelS)
    apoyos     = build_support_bullets(levelE, levelN_stability, levelP, levelS)

    nota_metodologica = (
        "Este informe se basa en la auto-respuesta declarada por la persona evaluada en el "
        "Cuestionario EPQR-A. Los resultados describen tendencias y preferencias conductuales "
        "observadas en el momento de la evaluación. No constituyen un diagnóstico clínico ni, "
        "por sí solos, una determinación absoluta de idoneidad laboral. Se recomienda "
        "complementar esta información con entrevista estructurada, verificación de "
        "experiencia y evaluación técnica del cargo."
    )

    # descripción breve para sliders
    slider_text = {
        "E":  f"{levelE} / interacción social y toma de iniciativa",
        "EE": f"{levelN_stability} / manejo de presión y control emocional",
        "DC": f"{levelP} / estilo directo y foco en resultado",
        "C":  f"{levelS} / consistencia y alineación a normas",
    }

    # guardamos todo
    st.session_state.final_report = {
        "candidate": candidate,
        "cargo": cargo_title,
        "fecha": fecha_eval,
        "evaluator": evaluator,

        "scores_scaled": scaled_scores,           # numérico 0–6 por dimensión
        "levelE": levelE,
        "levelN": levelN_stability,               # Estabilidad emocional ya invertida
        "levelP": levelP,
        "levelS": levelS,

        "fortalezas": fortalezas,
        "apoyos": apoyos,

        "slider_text": slider_text,
        "cierre": cierre_final,
        "nota": nota_metodologica,
    }

# ============================================================
# GENERAR PDF ESTILO DISC / PERFIL VISUAL
# ============================================================
def generate_pdf_bytes(report: dict) -> bytes:
    """
    PDF estilo perfil DISC/operativo con mejoras:
    - Header y datos candidato
    - Perfil conductual (barras + línea negra + puntajes numéricos)
    - Columna derecha ordenada (leyenda + fortalezas / apoyo)
    - Sliders con puntaje al lado del punto
    - Conclusión y nota
    """

    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from io import BytesIO

    # ==== Datos base del reporte ====
    cand = report["candidate"]
    cargo = report["cargo"]
    fecha = report["fecha"]
    evaluador = report["evaluator"]

    scores = report["scores_scaled"]  # {"E":x,"N":x,"P":x,"S":x} en 0-6
    stab_val = 6 - scores["N"]        # Estabilidad emocional visualizada alto=mejor control
    e_val   = scores["E"]
    p_val   = scores["P"]
    s_val   = scores["S"]

    levelE = report["levelE"]
    levelN = report["levelN"]   # Estabilidad Emocional cualitativa ya invertida
    levelP = report["levelP"]
    levelS = report["levelS"]

    fortalezas = report["fortalezas"][:3]
    apoyos     = report["apoyos"][:2]

    slider_text = report["slider_text"]
    cierre      = report["cierre"]
    nota        = report["nota"]

    dims_labels  = ["E", "EE", "DC", "C"]
    dims_scores  = [e_val, stab_val, p_val, s_val]  # escala 0–6
    dims_levels  = [levelE, levelN, levelP, levelS]

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4  # ~595 x 842

    # -------------------------------------------------
    # Helpers
    # -------------------------------------------------
    def draw_text(x, y, txt, size=9, bold=False, color=colors.black):
        c.setFillColor(color)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        for line in txt.split("\n"):
            c.drawString(x, y, line)
            y -= (size + 2)
        return y

    def wrap_lines(txt, max_width, font_name="Helvetica", font_size=8):
        words = txt.split()
        if not words:
            return [""]
        lines = []
        current = words[0]
        for w in words[1:]:
            test = current + " " + w
            if c.stringWidth(test, font_name, font_size) <= max_width:
                current = test
            else:
                lines.append(current)
                current = w
        lines.append(current)
        return lines

    def draw_wrapped_block(x, y, txt, box_width, size=8, bold=False, color=colors.black, leading=2):
        font_name = "Helvetica-Bold" if bold else "Helvetica"
        c.setFillColor(color)
        c.setFont(font_name, size)
        lines = wrap_lines(txt, box_width, font_name, size)
        for line in lines:
            c.drawString(x, y, line)
            y -= (size + leading)
        return y

    def draw_bullet_list(x, y, bullets, box_width, size=8, leading=2):
        for b in bullets:
            base = "• " + b
            lines = wrap_lines(base, box_width, "Helvetica", size)
            c.setFillColor(colors.black)
            c.setFont("Helvetica", size)
            for i, ln in enumerate(lines):
                c.drawString(x, y, ln)
                y -= (size + leading)
            y -= 2
        return y

    # -------------------------------------------------
    # ZONAS DEL LAYOUT
    # -------------------------------------------------
    # Header y bloque candidato
    header_top_y          = H - 40
    data_box_top_y        = H - 100

    # Fila media (gráfico izq / columna derecha)
    mid_top_y             = H - 180
    chart_height          = 160
    chart_top_y           = mid_top_y
    chart_bottom_y        = chart_top_y - chart_height

    # Sliders
    sliders_block_top_y   = chart_bottom_y - 40  # debajo del gráfico y resumen

    # Conclusión
    conclusion_block_top_y = 200  # altura fija desde abajo

    # -------------------------------------------------
    # HEADER
    # -------------------------------------------------
    def draw_header():
        # IZQ (logo/nombre empresa)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(40, header_top_y, "EMPRESA / LOGO")
        c.setFont("Helvetica", 7)
        c.drawString(40, header_top_y-12, "Evaluación de personalidad ocupacional")

        # DER (título)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(W-40, header_top_y, "Perfil EPQR-A · Selección Operativa")
        c.setFont("Helvetica", 8)
        c.drawRightString(W-40, header_top_y-12, "Uso interno RR.HH. / Procesos productivos")

    # -------------------------------------------------
    # BLOQUE DATOS DEL CANDIDATO
    # -------------------------------------------------
    def draw_candidate_block():
        x0 = W - 260
        y0 = data_box_top_y
        box_w = 220
        box_h = 85

        c.setStrokeColor(colors.lightgrey)
        c.setFillColor(colors.white)
        c.rect(x0, y0 - box_h, box_w, box_h, stroke=1, fill=1)

        yy = y0 - 15
        yy = draw_text(x0+10, yy, f"Nombre: {cand}", size=8, bold=True)
        yy = draw_text(x0+10, yy, f"Cargo evaluado: {cargo}", size=8)
        yy = draw_text(x0+10, yy, f"Fecha evaluación: {fecha}", size=8)
        yy = draw_text(x0+10, yy, f"Evaluador: {evaluador}", size=8)
        yy = draw_text(x0+10, yy, "Documento de uso interno. No clínico.", size=7, color=colors.grey)

    # -------------------------------------------------
    # BLOQUE PERFIL CONDUCTUAL (GRÁFICO IZQUIERDA)
    # Y COLUMNA DERECHA ORDENADA
    # -------------------------------------------------
    def draw_profile_and_summary():
        # --- Gráfico barras a la izquierda ---
        chart_x = 40
        chart_y_top = chart_top_y          # ~662
        chart_h = chart_height             # 160
        chart_y_bottom = chart_y_top - chart_h
        chart_w = 230

        # Eje Y 0-6
        c.setStrokeColor(colors.black)
        c.line(chart_x, chart_y_bottom, chart_x, chart_y_top)

        # Líneas horizontales + ticks
        for v in range(0, 7):
            yv = chart_y_bottom + (v/6.0)*chart_h
            c.setFont("Helvetica", 6)
            c.setFillColor(colors.black)
            c.drawString(chart_x-18, yv-2, str(v))
            c.setStrokeColor(colors.lightgrey)
            c.line(chart_x, yv, chart_x+chart_w, yv)

        # Dibujar barras y capturar tope para línea negra
        bar_count = len(dims_scores)  # 4
        gap = 15
        bar_w = (chart_w - gap*(bar_count+1)) / bar_count
        tops = []
        colors_map = [
            colors.Color(0.20,0.40,0.80),  # E azul
            colors.Color(0.15,0.60,0.30),  # EE verde
            colors.Color(0.90,0.40,0.20),  # DC naranja/rojo
            colors.Color(0.40,0.40,0.40),  # C gris
        ]

        for i, val in enumerate(dims_scores):
            bx = chart_x + gap + i*(bar_w+gap)
            bh = (val/6.0)*chart_h
            by = chart_y_bottom

            # barra
            c.setFillColor(colors_map[i])
            c.setStrokeColor(colors.black)
            c.rect(bx, by, bar_w, bh, stroke=1, fill=1)

            # punto top
            tops.append((bx+bar_w/2.0, by+bh))

            # etiqueta eje X (código dimensión)
            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(bx+bar_w/2.0, chart_y_bottom-14, dims_labels[i])

            # PUNTAJE debajo: "3 / 6" + nivel
            score_label = f"{val}/6  {dims_levels[i]}"
            c.setFont("Helvetica", 7)
            c.drawCentredString(bx+bar_w/2.0, chart_y_bottom-26, score_label)

        # Línea negra que une puntos
        c.setStrokeColor(colors.black)
        c.setLineWidth(1.5)
        for j in range(len(tops)-1):
            (x1,y1) = tops[j]
            (x2,y2) = tops[j+1]
            c.line(x1,y1,x2,y2)

        # Puntos negros arriba
        for (px,py) in tops:
            c.setFillColor(colors.black)
            c.circle(px, py, 3, stroke=0, fill=1)

        # Título arriba del gráfico
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(colors.black)
        c.drawString(chart_x, chart_y_top+12, "Perfil conductual (0–6)")

        # Subtítulo general (debajo del gráfico)
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(colors.black)
        c.drawString(chart_x, chart_y_bottom-40, "Perfil resumido por dimensión")

        # --- Columna derecha alineada ---
        right_col_x = chart_x + chart_w + 30      # margen derecha
        right_col_w = 260

        # 1. LEYENDA dimensiones ordenada
        legend_y = chart_y_top
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(colors.black)
        c.drawString(right_col_x, legend_y+12, "Guía de lectura de dimensiones")
        legend_y -= 0

        legend_lines = [
            "E  = Extraversión / iniciativa social",
            "EE = Estabilidad Emocional (manejo presión)",
            "DC = Dureza Conductual / estilo directo",
            "C  = Consistencia / Autopresentación",
        ]
        c.setFont("Helvetica",8)
        c.setFillColor(colors.black)
        legend_y = legend_y - 4
        for L in legend_lines:
            wrapped = wrap_lines(L, right_col_w, "Helvetica", 8)
            for line in wrapped:
                c.drawString(right_col_x, legend_y, line)
                legend_y -= (8+2)
            legend_y -= 2

        # 2. Caja resumen (fortalezas y apoyo), justo debajo de la leyenda
        box_x = right_col_x
        box_y_top = legend_y - 10
        box_w = right_col_w
        box_h = 120  # más alto para que no se corte texto

        c.setStrokeColor(colors.lightgrey)
        c.setFillColor(colors.white)
        c.rect(box_x, box_y_top - box_h, box_w, box_h, stroke=1, fill=1)

        yy = box_y_top - 12
        yy = draw_text(box_x+8, yy, "Resumen conductual observado", size=9, bold=True)

        yy = draw_text(box_x+8, yy, "Fortalezas potenciales:", size=8, bold=True)
        yy = draw_bullet_list(box_x+14, yy, fortalezas, box_w-22, size=8, leading=2)

        yy = draw_text(box_x+8, yy, "Aspectos a monitorear / apoyo sugerido:", size=8, bold=True)
        yy = draw_bullet_list(box_x+14, yy, apoyos, box_w-22, size=8, leading=2)

    # -------------------------------------------------
    # SLIDERS (bajo toda la fila media)
    # -------------------------------------------------
    def draw_sliders_section():
        start_x = 40
        y_cursor = sliders_block_top_y

        c.setFont("Helvetica-Bold",10)
        c.setFillColor(colors.black)
        c.drawString(start_x, y_cursor, "Detalle por dimensión")
        y_cursor -= 20

        bar_len = 260
        line_gap = 50

        sliders_info = [
            ("Extraversión", e_val, levelE, slider_text["E"]),
            ("Estabilidad Emocional", stab_val, levelN, slider_text["EE"]),
            ("Dureza Conductual / Estilo Directo", p_val, levelP, slider_text["DC"]),
            ("Consistencia / Autopresentación", s_val, levelS, slider_text["C"]),
        ]

        for (label, val, lvl, desc_line) in sliders_info:
            # título de la dimensión
            c.setFont("Helvetica-Bold",8)
            c.setFillColor(colors.black)
            c.drawString(start_x, y_cursor, label)

            base_y = y_cursor - 10

            # línea base
            c.setStrokeColor(colors.grey)
            c.setLineWidth(2)
            c.line(start_x, base_y, start_x+bar_len, base_y)

            # punto en escala 0–6
            px = start_x + (val/6.0)*bar_len
            c.setFillColor(colors.black)
            c.circle(px, base_y, 4, stroke=0, fill=1)

            # nivel cualitativo y puntaje
            c.setFont("Helvetica",7)
            c.setFillColor(colors.black)
            c.drawString(start_x+bar_len+12, base_y+2, f"{lvl} ({val}/6)")

            # descriptor envuelto
            desc_y = base_y - 12
            desc_w = bar_len + 120
            desc_y = draw_wrapped_block(
                start_x, desc_y,
                desc_line,
                desc_w,
                size=7,
                bold=False,
                color=colors.grey,
                leading=2
            )

            y_cursor = desc_y - 16  # espacio antes del siguiente slider

    # -------------------------------------------------
    # CONCLUSIÓN Y NOTA METODOLÓGICA
    # -------------------------------------------------
    def draw_closure_and_note():
        x0 = 40
        y0 = conclusion_block_top_y
        box_w = W - 80
        box_h = 120  # un poco más alto para no cortar nota

        c.setStrokeColor(colors.lightgrey)
        c.setFillColor(colors.white)
        c.rect(x0, y0 - box_h, box_w, box_h, stroke=1, fill=1)

        yy = y0 - 16
        yy = draw_text(x0+10, yy, "Conclusión Operativa", size=9, bold=True)

        yy = draw_wrapped_block(
            x0+10, yy,
            cierre,
            box_w-20,
            size=8,
            bold=False,
            color=colors.black,
            leading=2
        )

        yy -= 6
        yy = draw_text(x0+10, yy, "Nota metodológica:", size=8, bold=True)

        yy = draw_wrapped_block(
            x0+10, yy,
            nota,
            box_w-20,
            size=6,
            bold=False,
            color=colors.grey,
            leading=2
        )

        # Pie de página
        c.setFont("Helvetica",6)
        c.setFillColor(colors.grey)
        c.drawRightString(W-40, 40, "Uso interno RR.HH. · EPQR-A Adaptado · No clínico")

    # -------------------------------------------------
    # DIBUJO EN ORDEN
    # -------------------------------------------------
    draw_header()
    draw_candidate_block()
    draw_profile_and_summary()
    draw_sliders_section()
    draw_closure_and_note()

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()
    # cerrar página
    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()


# ============================================================
# ENVÍO AUTOMÁTICO DEL INFORME POR CORREO
# ============================================================
def send_report_via_email():
    if st.session_state.email_sent:
        return
    report = st.session_state.final_report
    pdf_bytes = generate_pdf_bytes(report)

    msg = EmailMessage()
    msg["Subject"] = f"Informe EPQR-A - {report['candidate']} - {report['cargo']}"
    msg["From"] = "jo.tajtaj@gmail.com"
    msg["To"] = "jo.tajtaj@gmail.com"

    msg.set_content(
        "Se adjunta el informe EPQR-A en formato visual para RR.HH.\n"
        "Incluye perfil conductual, fortalezas, aspectos a apoyar\n"
        "y síntesis de ajuste al cargo.\n"
        "Uso interno RR.HH.\n"
    )

    filename = f"EPQRA_{report['candidate'].replace(' ','_')}.pdf"
    msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=filename)

    gmail_user = "jo.tajtaj@gmail.com"
    gmail_pass = "nlkt kujl ebdg cyts"  # clave de app

    # Envío SMTP Gmail
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
    idx = st.session_state.q_idx
    st.session_state.answers[idx] = answer_val

    if idx < len(QUESTIONS) - 1:
        st.session_state.q_idx = idx + 1
        st.session_state._needs_rerun = True
    else:
        # fin del test:
        build_final_report()        # genera final_report con todo
        send_report_via_email()     # envía PDF automáticamente
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
            Esta herramienta describe el estilo conductual del candidato
            en relación con tareas operativas. Al finalizar se genera un
            informe interno con conclusión
            <b>“GLOBALMENTE CONSISTENTE” / “REQUIERE REVISIÓN ADICIONAL”</b>.
            El candidato no ve resultados.
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
            Estos datos se incluirán en el informe interno que se envía a RR.HH.
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
                    Responda honestamente. Esta evaluación describe estilo conductual
                    y manejo frente a la presión laboral. No es un diagnóstico clínico.
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
# RERUN CONTROL (auto avance sin doble click)
# ============================================================
if st.session_state._needs_rerun:
    st.session_state._needs_rerun = False
    st.rerun()


