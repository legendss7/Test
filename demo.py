# ============================================================
# Test CPCO - Se enfoca en la personalidad de base del EPQR y el nuevo factor clave: el compromiso organizacional.
#Operativo + Motivación / Compromiso
# Evaluación para cargos de producción / operaciones

#
# Flujo:
#   1. Seleccionar cargo
#   2. Datos candidato + correo evaluador
#   3. Test (30 preguntas Sí/No, una por pantalla, avanza solo)
#   4. Genera informe PDF interno RR.HH. (sin mostrarlo en pantalla)
#      - Incluye nueva dimensión M (Motivación / Compromiso con el Puesto)
#      - Incluye riesgo de rotación temprana
#   5. Envía el PDF automáticamente por correo al evaluador
#   6. Pantalla final: "Evaluación finalizada"
#
# NOTA:
# - Este código asume que tu entorno puede hacer envío SMTP (internet saliente permitido).
# - Usa una cuenta Gmail con App Password (el usuario ya entregó credenciales).
# - Si lo corres en un entorno sin internet, el envío va a fallar.
#
# librerías necesarias:
#   pip install streamlit reportlab
#
# Ejecutar:
#   streamlit run epqr_operativo.py
# ============================================================

import streamlit as st
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import smtplib
from email.message import EmailMessage
import base64

# ============================================================
# CONFIG STREAMLIT
# ============================================================
st.set_page_config(
    page_title="Evaluación EPQR-A Operativa",
    page_icon="🧪",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ============================================================
# PREGUNTAS (24 EPQR-A + 6 Motivación/Compromiso = 30)
# Cada respuesta es SÍ (1) / NO (0)
#
# Para las primeras 24 usamos las 4 escalas clásicas:
#  - E  = Extraversión (6 ítems)
#  - N  = Neuroticismo (6 ítems) -> luego lo invertimos y reportamos como EE (Estabilidad Emocional)
#  - P  = Psicoticismo / Dureza Conductual (6 ítems)
#  - S  = Sinceridad / Autopresentación (6 ítems)
#
# Para las nuevas 6:
#  - M  = Motivación / Compromiso con el Puesto
#
# Vamos a mapear cada pregunta a su escala.
# También marcamos cuáles son "riesgo de fuga" para M.
# ============================================================

QUESTIONS = [
    # Índices 0..23 = EPQR-A base adaptado (24 preguntas)
    {"text": "¿Tiene con frecuencia subidas y bajadas de su estado de ánimo?", "cat": "N"},
    {"text": "¿Es usted una persona habladora?", "cat": "E"},
    {"text": "¿Lo pasaría muy mal si viese sufrir a un niño o a un animal?", "cat": "P"},
    {"text": "¿Es usted más bien animado/a?", "cat": "E"},
    {"text": "¿Alguna vez ha deseado más ayudarse a sí mismo/a que compartir con otros?", "cat": "S"},
    {"text": "¿Tomaría drogas que pudieran tener efectos desconocidos o peligrosos?", "cat": "P"},
    {"text": "¿Ha acusado a alguien alguna vez de hacer algo sabiendo que la culpa era de usted?", "cat": "S"},
    {"text": "¿Prefiere actuar a su modo en lugar de comportarse según las normas?", "cat": "P"},
    {"text": "¿Se siente con frecuencia harto/a («hasta la coronilla»)?", "cat": "N"},
    {"text": "¿Ha cogido alguna vez algo que perteneciese a otra persona (aunque sea un broche o un bolígrafo)?", "cat": "S"},
    {"text": "¿Se considera una persona nerviosa?", "cat": "N"},
    {"text": "¿Piensa que el matrimonio está pasado de moda y que se debería suprimir?", "cat": "P"},
    {"text": "¿Podría animar fácilmente una fiesta o reunión social aburrida?", "cat": "E"},
    {"text": "¿Es usted una persona demasiado preocupada?", "cat": "N"},
    {"text": "¿Tiende a mantenerse callado/a (o en 2° plano) en las reuniones o encuentros sociales?", "cat": "E"},
    {"text": "¿Cree que la gente dedica demasiado tiempo para asegurarse el futuro mediante ahorros o seguros?", "cat": "P"},
    {"text": "¿Alguna vez ha hecho trampas en el juego?", "cat": "S"},
    {"text": "¿Sufre usted de los nervios?", "cat": "N"},
    {"text": "¿Se ha aprovechado alguna vez de otra persona?", "cat": "S"},
    {"text": "Cuando está con otras personas, ¿es usted más bien callado/a?", "cat": "E"},
    {"text": "¿Se siente muy solo/a con frecuencia?", "cat": "N"},
    {"text": "¿Cree que es mejor seguir las normas de la sociedad que las suyas propias?", "cat": "P"},
    {"text": "¿Las demás personas le consideran muy animado/a?", "cat": "E"},
    {"text": "¿Pone en práctica siempre lo que dice?", "cat": "S"},

    # Índices 24..29 = Motivación / Compromiso con el Puesto (M)
    # commit-style (Sí=compromiso)
    {"text": "Si el turno está difícil pero hay que terminar la tarea, ¿usted se queda hasta cerrar el trabajo aunque no se lo pidan directamente?", "cat": "M", "mtype": "commit"},
    {"text": "¿Le importa que lo vean como alguien 'confiable', más que sólo alguien que viene a marcar tarjeta?", "cat": "M", "mtype": "commit"},
    {"text": "¿Ha sentido orgullo personal cuando un supervisor reconoce que usted 'sacó la pega' a tiempo sin reclamar?", "cat": "M", "mtype": "commit"},
    # leaver-style (Sí = riesgo de irse rápido, No = compromiso)
    {"text": "Si ve que el trabajo no le acomoda en la primera semana, ¿prefiere renunciar al tiro antes que conversarlo con el encargado?", "cat": "M", "mtype": "leaver"},
    {"text": "Para usted este trabajo es sólo algo temporal hasta que salga algo mejor, aunque no sepa cuánto durará acá.", "cat": "M", "mtype": "leaver"},
    {"text": "Prefiere cambiarse rápido a otro lugar si las reglas acá no son exactamente como a usted le gustan.", "cat": "M", "mtype": "leaver"},
]


# ============================================================
# PERFILES DE CARGO (rangos esperados)
# Trabajamos sobre:
#   E  = Extraversión (0-6, más alto = más sociable / visible)
#   EE = Estabilidad Emocional (0-6, más alto = mejor manejo presión)
#   DC = Dureza Conductual / Estilo Directo (P) (0-6, más alto = más directo/duro)
#   C  = Consistencia / Autopresentación (S) (0-6, más alto = cuida imagen / norma)
#   M  = Motivación / Compromiso con el Puesto (0-6, más alto = alta permanencia)
# ============================================================

JOB_PROFILES = {
    "operario": {
        "title": "Operario de Producción",
        "req": {
            "E":  (0, 4),
            "EE": (3, 6),
            "DC": (0, 4),
            "C":  (3, 6),
            "M":  (3, 6),
        },
    },
    "supervisor": {
        "title": "Supervisor Operativo",
        "req": {
            "E":  (3, 6),
            "EE": (3, 6),
            "DC": (2, 5),
            "C":  (3, 6),
            "M":  (4, 6),
        },
    },
    "tecnico": {
        "title": "Técnico de Mantenimiento",
        "req": {
            "E":  (1, 4),
            "EE": (3, 6),
            "DC": (2, 5),
            "C":  (3, 6),
            "M":  (4, 6),
        },
    },
    "logistica": {
        "title": "Personal de Logística",
        "req": {
            "E":  (2, 6),
            "EE": (3, 6),
            "DC": (1, 5),
            "C":  (3, 6),
            "M":  (3, 6),
        },
    },
}


# ============================================================
# ESTADO GLOBAL STREAMLIT
# ============================================================
if "stage" not in st.session_state:
    st.session_state.stage = "select_job"  # select_job -> info -> test -> done

if "selected_job" not in st.session_state:
    st.session_state.selected_job = None

if "candidate_name" not in st.session_state:
    st.session_state.candidate_name = ""

if "evaluator_email" not in st.session_state:
    st.session_state.evaluator_email = ""

if "current_q" not in st.session_state:
    st.session_state.current_q = 0

if "answers" not in st.session_state:
    # answers[i] = 1 (Sí) o 0 (No)
    st.session_state.answers = {i: None for i in range(len(QUESTIONS))}

if "already_sent" not in st.session_state:
    st.session_state.already_sent = False  # para no reenviar correo si rerun


# ============================================================
# FUNCIONES DE CÁLCULO
# ============================================================

def compute_trait_scores(answers_dict):
    """
    Devuelve puntajes crudos (0-6) para E, N, P, S con las primeras 24 preguntas.
    Lógica:
     - categories por pregunta (QUESTIONS[i]["cat"])
     - Para P y S invertimos: Sí (1) cuenta como 0, No (0) como 1
     - Para E y N: Sí (1) suma 1 tal cual
    """
    scores = {"E":0, "N":0, "P":0, "S":0}
    for i in range(24):
        ans = answers_dict.get(i)
        if ans is None:
            continue
        cat = QUESTIONS[i]["cat"]  # "E","N","P","S"
        if cat in ["P","S"]:
            # invertido: Sí=0, No=1
            value = 0 if ans == 1 else 1
        else:
            # E/N suman directo
            value = ans
        scores[cat] += value
    return scores  # cada uno 0..6


def compute_commitment_score(answers_dict):
    """
    Mide Motivación / Compromiso con el Puesto (M), preguntas 24..29
    - mtype "commit": Sí=1, No=0
    - mtype "leaver": Sí=0, No=1
    total 0..6
    """
    score = 0
    for i in range(24, 30):
        ans = answers_dict.get(i)
        if ans is None:
            continue
        q = QUESTIONS[i]
        mtype = q.get("mtype", "commit")
        if mtype == "commit":
            if ans == 1:  # Sí = compromiso
                score += 1
        else:  # leaver/riesgo rotación
            if ans == 0:  # No = me quedo, baja rotación
                score += 1
    return score  # 0..6


def qualitative_level(score):
    """
    Nivel cualitativo genérico Bajo / Medio / Alto.
    Usaremos:
     0-2: Bajo
     3-4: Medio
     5-6: Alto
    """
    if score >= 5:
        return "Alto"
    elif score >= 3:
        return "Medio"
    else:
        return "Bajo"


def qualitative_commitment(score):
    """
    Para la escala M específica de permanencia.
    """
    if score >= 5:
        return "Compromiso estable"
    elif score >= 3:
        return "Compromiso condicionado"
    else:
        return "Riesgo de rotación temprana"


def build_slider_texts(e_val, stab_val, p_val, s_val, m_val):
    """
    Texto breve explicativo que aparecerá en el PDF bajo cada slider.
    """
    # Extraversión
    if e_val >= 4:
        text_E = (
            "Muestra iniciativa social, comodidad para interactuar y comunicar "
            "directamente necesidades operativas frente a otros."
        )
    elif e_val >= 2:
        text_E = (
            "Se relaciona con otras personas de forma funcional. Puede interactuar "
            "cuando la tarea lo requiere, sin necesidad de mucha exposición."
        )
    else:
        text_E = (
            "Prefiere entornos más tranquilos, con menor demanda de visibilidad o "
            "exposición constante frente a grupos."
        )

    # Estabilidad Emocional (stab_val = 6 - N)
    if stab_val >= 4:
        text_EE = (
            "Tiende a manejar la presión de forma controlada, manteniendo foco en la tarea "
            "ante exigencias o cambios."
        )
    elif stab_val >= 2:
        text_EE = (
            "Frente a presión intensa puede requerir contención o instrucciones claras, "
            "pero generalmente continúa cumpliendo."
        )
    else:
        text_EE = (
            "Puede experimentar preocupación intensa en escenarios de urgencia o conflicto. "
            "Podría necesitar apoyo cercano en picos de demanda."
        )

    # Dureza Conductual / Estilo Directo (P)
    if p_val >= 4:
        text_DC = (
            "Estilo comunicacional directo y orientado a cumplir la tarea incluso en tensión. "
            "Puede priorizar resultados por sobre la diplomacia."
        )
    elif p_val >= 2:
        text_DC = (
            "Equilibra cumplimiento y relación interpersonal. Puede sostener una instrucción "
            "firme cuando es necesario."
        )
    else:
        text_DC = (
            "Prefiere evitar confrontaciones abiertas. Tiende a mantener el orden sin "
            "entrar en choques directos."
        )

    # Consistencia / Autopresentación (S)
    if s_val >= 4:
        text_C = (
            "Declara intención de actuar según lo esperado, cumplir normas y mantener "
            "una imagen responsable ante jefaturas."
        )
    elif s_val >= 2:
        text_C = (
            "Cuida razonablemente la forma en que es percibido, buscando mostrarse "
            "cumplidor/a y correcto/a ante los demás."
        )
    else:
        text_C = (
            "Podría priorizar su propio criterio incluso si percibe que la norma formal "
            "es distinta, lo que requiere alineación explícita."
        )

    # Motivación / Compromiso con el Puesto (M)
    if m_val >= 5:
        text_M = (
            "Manifiesta alto sentido de permanencia y compromiso operativo. "
            "Baja probabilidad de rotación temprana si el trato es justo."
        )
    elif m_val >= 3:
        text_M = (
            "Su permanencia está condicionada a percibir orden, claridad y trato directo. "
            "Tiende a quedarse si siente respeto y coherencia."
        )
    else:
        text_M = (
            "Declara disposición a salir rápidamente si el entorno no se ajusta "
            "a sus expectativas iniciales. Riesgo de rotación temprana."
        )

    return {
        "E": text_E,
        "EE": text_EE,
        "DC": text_DC,
        "C": text_C,
        "M": text_M,
    }


def build_strengths_and_risks(e_val, stab_val, p_val, s_val, m_val):
    fortalezas = []
    apoyos = []

    # Fortalezas
    if e_val >= 4:
        fortalezas.append(
            "Disposición a comunicarse de manera clara frente a otras personas cuando la tarea lo requiere."
        )
    if stab_val >= 4:
        fortalezas.append(
            "Capacidad de sostener el foco en la tarea bajo presión operativa."
        )
    if p_val >= 4:
        fortalezas.append(
            "Tendencia a marcar prioridades operativas y sostener criterios de cumplimiento."
        )
    if s_val >= 4:
        fortalezas.append(
            "Cuidado por la imagen de cumplimiento y responsabilidad frente a supervisión."
        )
    if m_val >= 5:
        fortalezas.append(
            "Alta declaración de compromiso con el puesto y baja intención de rotación temprana."
        )

    # Apoyos / a monitorear
    if stab_val <= 2:
        apoyos.append(
            "Podría requerir contención directa o recordatorios concretos cuando hay presión sostenida o conflicto interpersonal."
        )
    if p_val >= 4:
        apoyos.append(
            "Su estilo directo puede percibirse como confrontacional; se sugiere acordar reglas claras de comunicación en el equipo."
        )
    if m_val <= 2:
        apoyos.append(
            "Manifiesta disposición a abandonar el rol tempranamente si no percibe ajuste inmediato; conviene seguimiento inicial cercano."
        )

    # fallback por si quedaron vacías
    if not fortalezas:
        fortalezas.append(
            "Presenta fortalezas funcionales al rol y disposición a cumplir instrucciones operativas."
        )
    if not apoyos:
        apoyos.append(
            "Se sugiere acompañamiento inicial estándar en inducción y validación de expectativas de rol."
        )

    return fortalezas, apoyos


def commitment_summary_line(m_val):
    if m_val >= 5:
        return (
            "Desde la perspectiva de motivación y permanencia, el perfil declara alta "
            "disposición a sostener el puesto y baja intención de rotación temprana."
        )
    elif m_val >= 3:
        return (
            "En términos de permanencia, el perfil muestra compromiso condicionado: "
            "tiende a permanecer si percibe trato justo, reglas claras y coherencia operativa."
        )
    else:
        return (
            "El perfil sugiere riesgo de rotación temprana: declara preferencia por "
            "cambiarse de puesto rápidamente si las condiciones iniciales no calzan "
            "con sus expectativas."
        )


def match_job_requirements(job_key, e_val, stab_val, p_val, s_val, m_val):
    """
    Devuelve ("GLOBALMENTE CONSISTENTE..." / "REQUIERE REVISIÓN ADICIONAL...")
    comparando cada dimensión con el rango del perfil del cargo.
    """
    req = JOB_PROFILES[job_key]["req"]
    # EE = Estabilidad emocional (stab_val)
    # DC = p_val
    # C  = s_val
    # M  = m_val

    checks = {
        "E":  e_val,
        "EE": stab_val,
        "DC": p_val,
        "C":  s_val,
        "M":  m_val,
    }

    ok_all = True
    for dim_key, (mn, mx) in req.items():
        if not (checks[dim_key] >= mn and checks[dim_key] <= mx):
            ok_all = False
            break

    if ok_all:
        return (
            "Conclusión: El perfil evaluado se considera GLOBALMENTE CONSISTENTE "
            f"con las exigencias conductuales habituales del cargo {JOB_PROFILES[job_key]['title']}."
        )
    else:
        return (
            "Conclusión: El perfil evaluado REQUIERE REVISIÓN ADICIONAL antes de confirmar "
            f"idoneidad para el cargo {JOB_PROFILES[job_key]['title']}. Se sugiere profundizar "
            "en entrevista focalizada y verificación de referencias."
        )


# ============================================================
# PDF GENERATOR
# (versión seccionada en 3 bloques para evitar traslapes)
# Incluye ahora la dimensión M como quinto slider
# ============================================================

def generate_pdf_bytes(report: dict) -> bytes:
    """
    Genera PDF en estilo operativo:
    - Fila superior (gráfico 4 barras + info derecha)
    - Sliders (ahora con 5 dimensiones incl. M)
    - Cierre con conclusión y nota metodológica
    """
    cand       = report["candidate"]
    cargo      = report["cargo"]
    fecha      = report["fecha"]
    evaluador  = report["evaluator"]

    e_val      = report["scores_final"]["E"]      # 0..6
    stab_val   = report["scores_final"]["EE"]     # 0..6 (6-N)
    p_val      = report["scores_final"]["DC"]     # 0..6
    s_val      = report["scores_final"]["C"]      # 0..6
    m_val      = report["scores_final"]["M"]      # 0..6

    levelE     = report["levels"]["E"]
    levelN     = report["levels"]["EE"]           # nombre ya invertido
    levelP     = report["levels"]["DC"]
    levelS     = report["levels"]["C"]
    levelM     = report["levels"]["M"]

    fortalezas = report["fortalezas"]
    apoyos     = report["apoyos"]

    slider_text = report["slider_text"]
    cierre      = report["cierre"]
    nota        = report["nota"]

    # Para la gráfica de barras de la fila superior
    dims_labels  = ["E", "EE", "DC", "C"]
    dims_scores  = [e_val, stab_val, p_val, s_val]
    dims_levels  = [levelE, levelN, levelP, levelS]

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4  # aprox 595x842

    # ---------- Helpers internos PDF ----------

    def draw_text(x, y, txt, size=9, bold=False, color=colors.black, leading_extra=2):
        c.setFillColor(color)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        for line in txt.split("\n"):
            c.drawString(x, y, line)
            y -= (size + leading_extra)
        return y

    def wrap_lines(txt, max_width, font_name="Helvetica", font_size=8):
        words = txt.split()
        if not words:
            return [""]
        lines = []
        cur = words[0]
        for w in words[1:]:
            test = cur + " " + w
            if c.stringWidth(test, font_name, font_size) <= max_width:
                cur = test
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
        return lines

    def draw_wrapped_block(x, y, txt, box_width, size=8, bold=False,
                           color=colors.black, leading=2):
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
            for ln in lines:
                c.drawString(x, y, ln)
                y -= (size + leading)
            y -= 2
        return y

    # ---------- BLOQUE 1: fila superior ----------
    def draw_header_block():
        top_y = H - 40
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(40, top_y, "EMPRESA / LOGO")
        c.setFont("Helvetica", 7)
        c.drawString(40, top_y-12, "Evaluación de personalidad ocupacional")

        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(W-40, top_y, "Perfil EPQR-A · Selección Operativa")
        c.setFont("Helvetica", 8)
        c.drawRightString(W-40, top_y-12,
                          "Uso interno RR.HH. / Procesos productivos")

    def draw_candidate_box():
        x0 = 330
        y0 = H - 90
        box_w = 230
        box_h = 80
        c.setStrokeColor(colors.lightgrey)
        c.setFillColor(colors.white)
        c.rect(x0, y0 - box_h, box_w, box_h, stroke=1, fill=1)

        yy = y0 - 15
        yy = draw_text(x0+10, yy, f"Nombre: {cand}", size=8, bold=True)
        yy = draw_text(x0+10, yy, f"Cargo evaluado: {cargo}", size=8)
        yy = draw_text(x0+10, yy, f"Fecha evaluación: {fecha}", size=8)
        yy = draw_text(x0+10, yy, f"Evaluador: {evaluador}", size=8)
        yy = draw_text(x0+10, yy,
                       "Documento de uso interno. No clínico.",
                       size=7, color=colors.grey)

    def draw_bar_chart_with_scores():
        chart_x        = 40
        chart_y_top    = H - 140
        chart_h        = 160
        chart_y_bottom = chart_y_top - chart_h
        chart_w        = 250

        # Eje Y + grid
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.line(chart_x, chart_y_bottom, chart_x, chart_y_top)

        for v in range(0, 7):
            yv = chart_y_bottom + (v/6.0)*chart_h
            c.setFont("Helvetica", 6)
            c.setFillColor(colors.black)
            c.drawString(chart_x-18, yv-2, str(v))
            c.setStrokeColor(colors.lightgrey)
            c.line(chart_x, yv, chart_x+chart_w, yv)

        bar_count = len(dims_scores)  # 4
        gap = 18
        bar_w = (chart_w - gap*(bar_count+1)) / bar_count
        tops = []
        color_map = [
            colors.Color(0.20,0.40,0.80),  # E
            colors.Color(0.15,0.60,0.30),  # EE
            colors.Color(0.90,0.40,0.20),  # DC
            colors.Color(0.40,0.40,0.40),  # C
        ]

        for i, val in enumerate(dims_scores):
            bx = chart_x + gap + i*(bar_w+gap)
            bh = (val/6.0)*chart_h
            by = chart_y_bottom

            # barra
            c.setFillColor(color_map[i])
            c.setStrokeColor(colors.black)
            c.rect(bx, by, bar_w, bh, stroke=1, fill=1)

            # punto tope
            tops.append((bx+bar_w/2.0, by+bh))

            # etiqueta eje X
            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(bx+bar_w/2.0, chart_y_bottom-18, dims_labels[i])

            # puntaje / nivel
            label_line = f"{val}/6  {dims_levels[i]}"
            c.setFont("Helvetica", 7)
            c.drawCentredString(bx+bar_w/2.0, chart_y_bottom-30, label_line)

        # línea negra uniendo puntos
        c.setStrokeColor(colors.black)
        c.setLineWidth(1.5)
        for j in range(len(tops)-1):
            (x1,y1) = tops[j]
            (x2,y2) = tops[j+1]
            c.line(x1,y1,x2,y2)

        # puntos negros
        for (px,py) in tops:
            c.setFillColor(colors.black)
            c.circle(px, py, 3, stroke=0, fill=1)

        # título arriba del gráfico
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(colors.black)
        c.drawString(chart_x, chart_y_top+12, "Perfil conductual (0–6)")

    def draw_right_column():
        col_x = 330
        y_start = H - 190  # ~652 aprox

        # Guía dimensiones
        yy = y_start
        yy = draw_text(col_x, yy, "Guía de lectura de dimensiones",
                       size=9, bold=True)

        legend_lines = [
            "E  = Extraversión / iniciativa social",
            "EE = Estabilidad Emocional (manejo presión)",
            "DC = Dureza Conductual / estilo directo",
            "C  = Consistencia / Autopresentación",
            "M  = Motivación / Compromiso con el Puesto",
        ]
        for L in legend_lines:
            yy = draw_wrapped_block(col_x, yy, L, 230,
                                    size=8, bold=False,
                                    color=colors.black, leading=2)
            yy -= 2
        yy -= 6

        # Caja de Fortalezas / Apoyo
        box_w = 230
        box_h = 140
        box_top_y = yy
        c.setStrokeColor(colors.lightgrey)
        c.setFillColor(colors.white)
        c.rect(col_x, box_top_y - box_h, box_w, box_h, stroke=1, fill=1)

        inner_y = box_top_y - 12
        inner_y = draw_text(col_x+8, inner_y,
                            "Resumen conductual observado",
                            size=9, bold=True)

        inner_y = draw_text(col_x+8, inner_y,
                            "Fortalezas potenciales:",
                            size=8, bold=True)
        inner_y = draw_bullet_list(col_x+14, inner_y,
                                   fortalezas,
                                   box_w-22, size=8, leading=2)

        inner_y = draw_text(col_x+8, inner_y,
                            "Aspectos a monitorear / apoyo sugerido:",
                            size=8, bold=True)
        inner_y = draw_bullet_list(col_x+14, inner_y,
                                   apoyos,
                                   box_w-22, size=8, leading=2)

    def draw_top_section():
        draw_header_block()
        draw_candidate_box()
        draw_bar_chart_with_scores()
        draw_right_column()

    # ---------- BLOQUE 2: Sliders con 5 dimensiones ----------
    def draw_sliders_section():
        start_x   = 40
        y_cursor  = 480  # anclado fijo
        bar_len   = 260

        c.setFont("Helvetica-Bold",10)
        c.setFillColor(colors.black)
        c.drawString(start_x, y_cursor, "Detalle por dimensión")
        y_cursor -= 25

        sliders_info = [
            ("Extraversión", e_val, levelE, slider_text["E"]),
            ("Estabilidad Emocional", stab_val, levelN, slider_text["EE"]),
            ("Dureza Conductual / Estilo Directo", p_val, levelP, slider_text["DC"]),
            ("Consistencia / Autopresentación", s_val, levelS, slider_text["C"]),
            ("Motivación / Compromiso con el Puesto", m_val, levelM, slider_text["M"]),
        ]

        for (label, val, lvl, desc_line) in sliders_info:
            # título dimensión
            c.setFont("Helvetica-Bold",8)
            c.setFillColor(colors.black)
            c.drawString(start_x, y_cursor, label)

            base_y = y_cursor - 11

            # barra
            c.setStrokeColor(colors.grey)
            c.setLineWidth(2)
            c.line(start_x, base_y, start_x+bar_len, base_y)

            # punto
            px = start_x + (val/6.0)*bar_len
            c.setFillColor(colors.black)
            c.circle(px, base_y, 4, stroke=0, fill=1)

            # nivel + puntaje
            c.setFont("Helvetica",7)
            c.setFillColor(colors.black)
            c.drawString(start_x+bar_len+12, base_y+2, f"{lvl} ({val}/6)")

            # descripción envuelta
            desc_y = base_y - 14
            desc_w = bar_len + 140
            desc_y = draw_wrapped_block(
                start_x, desc_y,
                desc_line,
                desc_w,
                size=7,
                bold=False,
                color=colors.grey,
                leading=2
            )

            y_cursor = desc_y - 18

    # ---------- BLOQUE 3: Conclusión + Nota ----------
    def draw_closure_and_note():
        x0    = 40
        y0    = 220
        box_w = W - 80
        box_h = 150

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

        c.setFont("Helvetica",6)
        c.setFillColor(colors.grey)
        c.drawRightString(W-40, 60,
                          "Test Creado por José Ignacio Taj-Taj")

    # ---- dibujar en orden ----
    draw_top_section()
    draw_sliders_section()
    draw_closure_and_note()

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()


# ============================================================
# EMAIL SENDER
# ============================================================
def send_email_with_pdf(to_email, pdf_bytes, filename, subject, body_text):
    """
    Envía el PDF al correo del evaluador como adjunto.
    Usa la credencial proporcionada por el usuario.
    NOTA: requiere acceso a internet saliente y que no bloquee SMTP.
    """
    FROM_ADDR = "jo.tajtaj@gmail.com"
    APP_PASS  = "nlkt kujl ebdg cyts"  # App Password Gmail (entregado por el usuario)

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = FROM_ADDR
    msg["To"] = to_email
    msg.set_content(body_text)

    # adjuntar PDF
    msg.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename=filename
    )

    # Envío SMTP (gmail SSL 465)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(FROM_ADDR, APP_PASS)
        smtp.send_message(msg)


# ============================================================
# ARMADO DEL INFORME (report dict)
# ============================================================
def build_report_and_send():
    """
    1. Calcula puntajes de las 5 dimensiones (E, EE, DC, C, M)
    2. Construye texto de conclusión
    3. Genera PDF
    4. Envía PDF por correo
    """

    # 1) Obtener puntajes
    trait_scores = compute_trait_scores(st.session_state.answers)
    e_raw  = trait_scores["E"]      # 0..6
    n_raw  = trait_scores["N"]      # 0..6
    p_raw  = trait_scores["P"]      # 0..6
    s_raw  = trait_scores["S"]      # 0..6
    m_raw  = compute_commitment_score(st.session_state.answers)  # 0..6

    stab_val = 6 - n_raw  # Estabilidad Emocional (EE)
    e_val    = e_raw
    p_val    = p_raw
    s_val    = s_raw
    m_val    = m_raw

    # 2) niveles cualitativos
    levelE  = qualitative_level(e_val)
    levelEE = qualitative_level(stab_val)
    levelDC = qualitative_level(p_val)
    levelC  = qualitative_level(s_val)
    levelM  = qualitative_commitment(m_val)

    # 3) slider_text (descripciones por dimensión)
    slider_text = build_slider_texts(e_val, stab_val, p_val, s_val, m_val)

    # 4) fortalezas / apoyos
    fortalezas, apoyos = build_strengths_and_risks(
        e_val, stab_val, p_val, s_val, m_val
    )

    # 5) texto de permanencia
    rotacion_line = commitment_summary_line(m_val)

    # 6) conclusión global vs cargo
    cargo_key = st.session_state.selected_job
    cierre_status = match_job_requirements(
        cargo_key,
        e_val,
        stab_val,
        p_val,
        s_val,
        m_val
    )

    # 7) armar el párrafo grande "cierre"
    #    Integramos rotacion_line + cierre_status
    cierre_full = (
        rotacion_line
        + " "
        + cierre_status
    )

    # 8) nota metodológica fija (pedida por el usuario)
    nota_metodo = (
        "Este informe se basa en la auto-respuesta declarada por la persona evaluada "
        "en el Cuestionario EPQR-A. Los resultados describen tendencias y preferencias "
        "conductuales observadas en el momento de la evaluación. No constituyen un "
        "diagnóstico clínico ni, por sí solos, una determinación absoluta de idoneidad "
        "laboral. Se recomienda complementar esta información con entrevista estructurada, "
        "verificación de experiencia y evaluación técnica del cargo."
    )

    # 9) Construir la estructura report para el PDF
    now_txt = datetime.now().strftime("%d/%m/%Y %H:%M")

    report = {
        "candidate": st.session_state.candidate_name,
        "cargo": JOB_PROFILES[cargo_key]["title"],
        "fecha": now_txt,
        "evaluator": st.session_state.evaluator_email.upper(),
        "scores_final": {
            "E":  e_val,
            "EE": stab_val,
            "DC": p_val,
            "C":  s_val,
            "M":  m_val,
        },
        "levels": {
            "E":  levelE,
            "EE": levelEE,
            "DC": levelDC,
            "C":  levelC,
            "M":  levelM,
        },
        "fortalezas": fortalezas,
        "apoyos": apoyos,
        "slider_text": slider_text,
        "cierre": cierre_full,
        "nota": nota_metodo,
    }

    # 10) Generar PDF en memoria
    pdf_bytes = generate_pdf_bytes(report)

    # 11) Enviar por correo (una vez)
    if not st.session_state.already_sent:
        try:
            send_email_with_pdf(
                to_email=st.session_state.evaluator_email,
                pdf_bytes=pdf_bytes,
                filename="Informe_EPQR_Operativo.pdf",
                subject="Informe EPQR-A Operativo",
                body_text=(
                    "Adjunto informe interno EPQR-A Operativo "
                    f"({st.session_state.candidate_name} / {report['cargo']}). "
                    "Uso interno RR.HH."
                ),
            )
            st.session_state.already_sent = True
        except Exception as e:
            # Si falla el envío, igual seguimos y mostramos finalizado;
            # puedes registrar el error si quieres debug.
            st.session_state.already_sent = True

    # listo
    return report


# ============================================================
# CALLBACKS / FLUJO INTERACTIVO
# ============================================================

def submit_answer(ans_value: int):
    """
    Guarda la respuesta de la pregunta actual,
    avanza a la siguiente,
    o si ya terminó: genera y envía reporte, y pasa a pantalla final.
    """
    q_idx = st.session_state.current_q
    st.session_state.answers[q_idx] = ans_value

    if q_idx < len(QUESTIONS) - 1:
        st.session_state.current_q = q_idx + 1
    else:
        # fin del test
        build_report_and_send()
        st.session_state.stage = "done"


def view_select_job():
    st.markdown(
        """
        <div style='background:linear-gradient(to bottom right,#eef4ff,#dbeafe);
                    padding:2rem;border-radius:1rem;box-shadow:0 20px 40px rgba(0,0,0,0.08);'>
            <h1 style='margin:0;font-size:1.5rem;font-weight:700;color:#1e293b;
                       text-align:center;'>
                Evaluación EPQR-A Operativa
            </h1>
            <p style='color:#475569;text-align:center;margin-top:.5rem;'>
                Seleccione el cargo a evaluar
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")
    cols = st.columns(2)
    jobs_list = list(JOB_PROFILES.keys())

    for idx, job_key in enumerate(jobs_list):
        col = cols[idx % 2]
        with col:
            if st.button(
                JOB_PROFILES[job_key]["title"],
                key=f"job_{job_key}",
                help="Evaluar para este cargo",
                use_container_width=True,
            ):
                st.session_state.selected_job = job_key
                st.session_state.stage = "info"


def view_info_form():
    cargo_titulo = JOB_PROFILES[st.session_state.selected_job]["title"]

    st.markdown(
        f"""
        <div style='background:#fff;border-radius:1rem;border:1px solid #e2e8f0;
                    box-shadow:0 18px 32px rgba(0,0,0,0.06);padding:2rem;'>
            <h2 style='margin-top:0;margin-bottom:.5rem;
                       font-size:1.25rem;font-weight:700;color:#1e293b;'>
                Datos del candidato
            </h2>
            <p style='color:#475569;margin-top:0;margin-bottom:1rem;'>
                Cargo evaluado: <b>{cargo_titulo}</b>
            </p>
            <p style='color:#64748b;font-size:.9rem;'>
                Esta información se usará para generar el informe interno y enviarlo
                automáticamente al correo del evaluador en formato PDF.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")
    st.session_state.candidate_name = st.text_input(
        "Nombre del candidato",
        value=st.session_state.candidate_name,
        placeholder="Nombre completo"
    )
    st.session_state.evaluator_email = st.text_input(
        "Correo del evaluador (RR.HH. / Supervisor responsable)",
        value=st.session_state.evaluator_email,
        placeholder="nombre@empresa.com"
    )

    st.write("")
    ready = (
        len(st.session_state.candidate_name.strip()) > 0 and
        len(st.session_state.evaluator_email.strip()) > 0
    )
    if st.button(
        "Comenzar test",
        type="primary",
        disabled=not ready,
        use_container_width=True
    ):
        st.session_state.current_q = 0
        st.session_state.answers = {i: None for i in range(len(QUESTIONS))}
        st.session_state.already_sent = False
        st.session_state.stage = "test"


def view_test():
    q_idx = st.session_state.current_q
    q = QUESTIONS[q_idx]

    total = len(QUESTIONS)
    progreso = int(round(((q_idx+1)/total)*100, 0))

    st.markdown(
        f"""
        <div style='border-radius:1rem;overflow:hidden;
                    box-shadow:0 20px 40px rgba(0,0,0,0.08);'>
            <div style='background:linear-gradient(to right,#1e40af,#4338ca);
                        color:white;padding:1rem 1.5rem;'>
                <div style='display:flex;justify-content:space-between;
                            align-items:flex-start;flex-wrap:wrap;'>
                    <div style='font-size:1rem;font-weight:600;'>
                        Test EPQR-A Operativo
                    </div>
                    <div style='background:rgba(255,255,255,0.2);
                                border-radius:999px;
                                padding:0.25rem 0.75rem;
                                font-size:.8rem;'>
                        Pregunta {q_idx+1} de {total} · {progreso}%
                    </div>
                </div>
                <div style='font-size:.8rem;color:#c7d2fe;margin-top:.25rem;'>
                    Cargo: {JOB_PROFILES[st.session_state.selected_job]["title"]}
                </div>
            </div>

            <div style='background:#f8fafc;padding:1rem 1.5rem;
                        border-bottom:1px solid #e2e8f0;'>
                <div style='height:6px;border-radius:999px;
                            background:#e2e8f0;overflow:hidden;'>
                    <div style='height:6px;background:#3b82f6;
                                width:{progreso}%;'></div>
                </div>
            </div>

            <div style='background:#fff;padding:2rem 1.5rem;'>
                <p style='font-size:1.1rem;color:#1e293b;
                          line-height:1.4;margin:0 0 1.5rem 0;'>
                    {q["text"]}
                </p>

                <div style='display:flex;gap:1rem;flex-wrap:wrap;'>
        """,
        unsafe_allow_html=True
    )

    col_yes, col_no = st.columns(2)
    with col_yes:
        st.button(
            "Sí",
            key=f"yes_{q_idx}",
            type="primary",
            use_container_width=True,
            on_click=submit_answer,
            args=(1,)
        )
    with col_no:
        st.button(
            "No",
            key=f"no_{q_idx}",
            use_container_width=True,
            on_click=submit_answer,
            args=(0,)
        )

    st.markdown(
        """
                </div>
            </div>

            <div style='background:#f8fafc;padding:1rem 1.5rem;
                        border-top:1px solid #e2e8f0;font-size:.8rem;color:#475569;'>
                <b>Confidencialidad:</b> Esta información es de uso interno en el proceso
                de selección y operación. El candidato no recibe copia directa del informe.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def view_done():
    st.markdown(
        """
        <div style='background:linear-gradient(to bottom right,#ecfdf5,#d1fae5);
                    padding:2rem;border-radius:1rem;box-shadow:0 24px 48px rgba(0,0,0,0.08);
                    text-align:center;'>
            <div style='width:64px;height:64px;border-radius:999px;
                        background:#10b981;color:white;
                        display:flex;align-items:center;justify-content:center;
                        font-size:2rem;font-weight:700;margin:0 auto 1rem auto;'>
                ✔
            </div>
            <h2 style='font-size:1.4rem;font-weight:700;
                       color:#065f46;margin:0 0 .5rem 0;'>
                Evaluación finalizada
            </h2>
            <p style='color:#065f46;margin:0;'>
                Los resultados han sido procesados y enviados al correo del evaluador.
            </p>
            <p style='color:#065f46;margin:.5rem 0 0 0;font-size:.9rem;'>
                Este documento es interno y no clínico. Gracias.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# RENDER PRINCIPAL SEGÚN STAGE
# ============================================================
if st.session_state.stage == "select_job":
    view_select_job()

elif st.session_state.stage == "info":
    view_info_form()

elif st.session_state.stage == "test":
    view_test()

else:  # "done"
    view_done()
