import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime

# =========================================================
# CONFIG STREAMLIT GENERAL
# =========================================================
st.set_page_config(
    page_title="EPQR-A Operativo",
    page_icon="🛠️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# =========================================================
# PREGUNTAS (40 ÍTEMS, 5 DIMENSIONES)
# E  = Extraversión / iniciativa social
# EE = Estabilidad Emocional / manejo presión
# DC = Dureza Conductual / estilo directo / foco en tarea
# C  = Consistencia / Autopresentación / cumplimiento normas
# M  = Motivación / Permanencia
# Cada ítem es Sí=1 / No=0
# =========================================================
QUESTIONS = [
    # ---- E (Extraversión) ----
    {"text": "Me siento cómodo/a hablando con personas que recién conozco.", "dim": "E"},
    {"text": "Puedo animar fácilmente una reunión aburrida si es necesario.", "dim": "E"},
    {"text": "Prefiero interactuar activamente con el equipo en lugar de trabajar aislado/a.", "dim": "E"},
    {"text": "Me gusta tomar la palabra cuando hay que resolver algo rápido.", "dim": "E"},
    {"text": "Me siento con energía cuando trabajo con otras personas cerca.", "dim": "E"},

    # ---- EE (Estabilidad Emocional / manejo de presión) ----
    {"text": "Bajo presión, mantengo la calma y sigo funcionando bien.", "dim": "EE"},
    {"text": "Cuando hay urgencia, puedo enfocarme sin perder el control.", "dim": "EE"},
    {"text": "En situaciones tensas, no me altero fácilmente.", "dim": "EE"},
    {"text": "Puedo tomar decisiones aun cuando el entorno está estresante.", "dim": "EE"},
    {"text": "En turnos exigentes, no pierdo la concentración por nervios.", "dim": "EE"},

    # ---- DC (Dureza Conductual / Estilo Directo / Firmeza) ----
    {"text": "Puedo decir lo que hay que hacer aunque a otros no les guste.", "dim": "DC"},
    {"text": "En el trabajo doy prioridad a la tarea por sobre las excusas.", "dim": "DC"},
    {"text": "Prefiero ser directo/a y claro/a antes que suavizar un mensaje.", "dim": "DC"},
    {"text": "Si alguien baja el ritmo, soy capaz de marcarle el estándar esperado.", "dim": "DC"},
    {"text": "En conflicto operativo, sostengo mi punto si sé que es lo correcto.", "dim": "DC"},

    # ---- C (Consistencia / Cumplimiento / Autopresentación) ----
    {"text": "Respeto las normas y procedimientos aunque parezcan repetitivos.", "dim": "C"},
    {"text": "Cumplo lo que digo que voy a hacer, incluso en detalles menores.", "dim": "C"},
    {"text": "Me preocupo de no cometer faltas o errores evitables.", "dim": "C"},
    {"text": "Me tomo en serio las políticas internas (seguridad, orden, registro).", "dim": "C"},
    {"text": "Me esfuerzo por dejar una buena impresión frente a supervisores.", "dim": "C"},

    # ---- M (Motivación / Permanencia / Compromiso) ----
    {"text": "Estoy interesado/a en permanecer en un puesto estable por un buen tiempo.", "dim": "M"},
    {"text": "Valoro más la estabilidad laboral que estar cambiando de empleo seguido.", "dim": "M"},
    {"text": "Mientras el trato sea justo, prefiero quedarme y crecer en la misma empresa.", "dim": "M"},
    {"text": "No suelo dejar un trabajo sólo porque aparece otra oferta con poca diferencia salarial.", "dim": "M"},
    {"text": "Me comprometo con un turno/rol si veo claridad en las reglas y el liderazgo directo.", "dim": "M"},

    # ---- Ítems extra por dimensión para completar 40 ----
    # E extra
    {"text": "No tengo problema en presentarme ante un grupo y explicar lo que estoy haciendo.", "dim": "E"},
    {"text": "Puedo responder consultas de otras áreas sin incomodarme.", "dim": "E"},
    {"text": "Prefiero conversar en persona en vez de evitar la interacción.", "dim": "E"},

    # EE extra
    {"text": "Cuando algo sale mal, recupero el foco sin quedarme pegado/a en el error.", "dim": "EE"},
    {"text": "Enfrento turno complicado sin entrar en pánico.", "dim": "EE"},
    {"text": "Puedo manejar correcciones directas sin desmotivarme de inmediato.", "dim": "EE"},

    # DC extra
    {"text": "Me siento cómodo/a diciendo 'esto no está bien' si el estándar baja.", "dim": "DC"},
    {"text": "Puedo sostener una indicación aunque la otra persona reaccione a la defensiva.", "dim": "DC"},
    {"text": "Soy más de actuar y corregir rápido que de dejar pasar un problema interno.", "dim": "DC"},

    # C extra
    {"text": "Procuro cumplir horario y registro sin excusas frecuentes.", "dim": "C"},
    {"text": "Intento alinear mi comportamiento con lo que la empresa espera formalmente.", "dim": "C"},
    {"text": "Prefiero evitar llamados de atención, así que sigo los procedimientos.", "dim": "C"},

    # M extra (motivación y 'preguntas trampa' sobre fuga temprana)
    {"text": "Si el ambiente es justo, no tengo intención de irme a las pocas semanas.", "dim": "M"},
    {"text": "No me considero alguien que abandona rápido cuando el trabajo se pone exigente.", "dim": "M"},
    {"text": "Me proyecto manteniéndome en el cargo mientras vea respeto y claridad operacional.", "dim": "M"},
    {"text": "No estoy buscando 'cualquier cosa pasajera'; busco estabilidad.", "dim": "M"},
    {"text": "Si siento que el rol me calza, prefiero continuidad antes que estar saltando entre trabajos.", "dim": "M"},
]

DIMENSIONS_INFO = {
    "E":  "Extraversión",
    "EE": "Estabilidad Emocional",
    "DC": "Dureza Conductual / Estilo Directo",
    "C":  "Consistencia / Autopresentación",
    "M":  "Motivación / Compromiso con el Puesto",
}

# =========================================================
# PERFILES DE CARGO (requisitos esperados aprox. 0-6)
# =========================================================
JOB_PROFILES = {
    "operario": {
        "name": "Operario de Producción",
        "req": {
            "E":  (2, 5),
            "EE": (3, 6),
            "DC": (2, 5),
            "C":  (3, 6),
            "M":  (3, 6),
        }
    },
    "logistica": {
        "name": "Personal de Logística",
        "req": {
            "E":  (2, 5),
            "EE": (3, 6),
            "DC": (2, 5),
            "C":  (3, 6),
            "M":  (3, 6),
        }
    },
    "supervisor": {
        "name": "Supervisor Operativo",
        "req": {
            "E":  (3, 6),
            "EE": (3, 6),
            "DC": (3, 6),
            "C":  (3, 6),
            "M":  (3, 6),
        }
    },
    "manto": {
        "name": "Técnico de Mantenimiento",
        "req": {
                "E":  (1, 4),
                "EE": (3, 6),
                "DC": (2, 5),
                "C":  (3, 6),
                "M":  (3, 6),
        }
    },
}

# =========================================================
# UTILIDADES
# =========================================================
def init_state():
    if "stage" not in st.session_state:
        st.session_state.stage = "setup"  # setup -> test -> done
    if "job_key" not in st.session_state:
        st.session_state.job_key = ""
    if "candidate_name" not in st.session_state:
        st.session_state.candidate_name = ""
    if "evaluator_email" not in st.session_state:
        st.session_state.evaluator_email = ""
    if "answers" not in st.session_state:
        st.session_state.answers = {}
    if "q_idx" not in st.session_state:
        st.session_state.q_idx = 0
    if "results" not in st.session_state:
        st.session_state.results = None
    if "_advance" not in st.session_state:
        st.session_state._advance = False

def qualitative_level(score_0to6: float) -> str:
    if score_0to6 >= 4.5:
        return "Alto"
    if score_0to6 >= 3:
        return "Medio"
    return "Bajo"

def _wrap(c, text, width_px, font_name, font_size):
    """
    Hace wrap manual en base a canvas.stringWidth para que el texto
    no se salga del recuadro en el PDF.
    width_px = ancho máximo usable en esa celda/bloque.
    """
    words = text.split()
    lines = []
    current = ""
    for w in words:
        test_line = (current + " " + w).strip()
        if c.stringWidth(test_line, font_name, font_size) <= width_px:
            current = test_line
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines

# =========================================================
# CÁLCULO DE PUNTAJES
# =========================================================
def compute_scores(answers_dict):
    """
    answers_dict: { idx_pregunta:int -> 0/1 }
    Devuelve:
      raw_scores: cuántas 'Sí' en cada dimensión
      norm_scores: escala 0-6 normalizada por nº de ítems de esa dimensión
    """
    counts = {"E":0,"EE":0,"DC":0,"C":0,"M":0}
    totals = {"E":0,"EE":0,"DC":0,"C":0,"M":0}

    for i,q in enumerate(QUESTIONS):
        d = q["dim"]
        totals[d] += 1
        ans = answers_dict.get(i,0)
        if ans == 1:
            counts[d] += 1

    norm = {}
    for d in counts:
        if totals[d] > 0:
            norm[d] = (counts[d]/totals[d])*6.0
        else:
            norm[d] = 0.0

    return counts, norm, totals

def build_descriptions(norm_scores):
    """
    Texto breve por dimensión para tabla.
    """
    desc = {}

    # Extraversión
    if norm_scores["E"] >= 4:
        desc["E"] = "Tendencia a interactuar, comunicar y sostener visibilidad en equipo."
    elif norm_scores["E"] >= 2.5:
        desc["E"] = "Comunicador funcional; se activa socialmente cuando la tarea lo exige."
    else:
        desc["E"] = "Perfil más reservado, preferencia por foco individual y comunicación directa puntual."

    # Estabilidad Emocional
    if norm_scores["EE"] >= 4:
        desc["EE"] = "Manejo estable en presión, regula tensión y mantiene foco operativo."
    elif norm_scores["EE"] >= 2.5:
        desc["EE"] = "Tolera exigencia moderada, podría requerir apoyo en picos de demanda."
    else:
        desc["EE"] = "Puede experimentar estrés intenso en alta urgencia; necesita contención clara y guía cercana."

    # Dureza Conductual
    if norm_scores["DC"] >= 4:
        desc["DC"] = "Capacidad para marcar prioridades y sostener estándares aun con resistencia."
    elif norm_scores["DC"] >= 2.5:
        desc["DC"] = "Directo/a cuando es necesario, tiende a equilibrar tarea y relación."
    else:
        desc["DC"] = "Prefiere evitar confrontaciones; podría dudar en frenar desvíos operativos."

    # Consistencia
    if norm_scores["C"] >= 4:
        desc["C"] = "Orientación a normas, cumplimiento y registro formal."
    elif norm_scores["C"] >= 2.5:
        desc["C"] = "Acepta lineamientos, aunque puede flexibilizarse si percibe baja supervisión."
    else:
        desc["C"] = "Podría tomar atajos frente a controles; requiere supervisión de cumplimiento."

    # Motivación / Compromiso
    if norm_scores["M"] >= 4:
        desc["M"] = "Disposición declarada a permanecer y sostener continuidad si hay trato justo."
    elif norm_scores["M"] >= 2.5:
        desc["M"] = "Motivación moderada; evalúa permanecer si percibe condiciones transparentes."
    else:
        desc["M"] = "Puede priorizar cambio rápido de puesto ante incomodidad inicial; riesgo de rotación temprana."

    return desc

def build_strengths_and_risks(norm_scores):
    fortalezas = []
    monitoreo = []

    # Fortalezas
    if norm_scores["E"] >= 3:
        fortalezas.append("Disposición a comunicarse con otras personas y sostener coordinación directa.")
    else:
        fortalezas.append("Perfil más contenido, con foco individual y baja distracción social.")
    if norm_scores["EE"] >= 3:
        fortalezas.append("Tendencia a mantener la calma en escenarios de presión operativa.")
    if norm_scores["DC"] >= 3:
        fortalezas.append("Capacidad para marcar prioridades operativas y sostener criterios de cumplimiento.")
    if norm_scores["C"] >= 3:
        fortalezas.append("Respeto declarado por normas, procedimientos y estándares formales.")
    if norm_scores["M"] >= 3:
        fortalezas.append("Disposición declarada a permanecer en el puesto siempre que existan condiciones percibidas como justas.")

    # Monitoreo / apoyo
    if norm_scores["EE"] < 3:
        monitoreo.append("Podría requerir apoyo cercano en picos de exigencia emocional o alta presión.")
    if norm_scores["DC"] >= 4.5:
        monitoreo.append("Estilo directo; se sugiere acordar normas de comunicación explícitas para evitar fricción.")
    if norm_scores["C"] < 3:
        monitoreo.append("Supervisar cumplimiento básico (asistencia, orden, seguridad) durante la fase inicial.")
    if norm_scores["M"] < 3:
        monitoreo.append("Riesgo de rotación temprana: alinear expectativas y condiciones del rol desde el inicio.")

    if not monitoreo:
        monitoreo.append("Sin observaciones críticas inmediatas; mantener retroalimentación clara y oportuna.")

    return fortalezas, monitoreo

def build_compromiso_text(norm_scores):
    if norm_scores["M"] >= 4:
        return ("Compromiso declarado: se mantendría en el cargo si percibe trato justo, "
                "claridad operativa y respeto de parte de la jefatura directa.")
    elif norm_scores["M"] >= 2.5:
        return ("Compromiso declarado moderado: planea permanecer si observa consistencia en las reglas "
                "y oportunidades básicas de estabilidad.")
    else:
        return ("Compromiso declarado bajo: podría abandonar de forma temprana si percibe conflicto, "
                "ambiente inestable o poca claridad en el rol.")

def build_final_adjustment_text(norm_scores, job_key):
    cargo_name = JOB_PROFILES[job_key]["name"]
    # Chequeo simple de “consistencia con cargo”:
    reqs = JOB_PROFILES[job_key]["req"]
    ok_dims = 0
    for dim, (lo, hi) in reqs.items():
        val = norm_scores[dim]
        if lo <= val <= hi:
            ok_dims += 1

    if ok_dims >= 4:
        # lo consideramos globalmente consistente
        return (f"Ajuste al cargo: El perfil evaluado se considera GLOBALMENTE CONSISTENTE "
                f"con las exigencias habituales del cargo {cargo_name}.")
    else:
        return (f"Ajuste al cargo: El perfil evaluado se considera REQUIERE REVISIÓN "
                f"antes de confirmar su ajuste al cargo {cargo_name}.")

def build_nota_text():
    return ("Este informe se basa en la auto-respuesta declarada por la persona evaluada "
            "en el Cuestionario EPQR-A adaptado a contexto laboral operativo. Los resultados "
            "describen tendencias y preferencias conductuales observadas en el momento de la "
            "evaluación. No constituyen un diagnóstico clínico ni, por sí solos, una determinación "
            "absoluta de idoneidad laboral. Se recomienda complementar esta información con "
            "entrevista estructurada, verificación de experiencia y evaluación técnica del cargo.")

# =========================================================
# PDF GENERATION (CON TODOS LOS CAMBIOS QUE PEDISTE)
# =========================================================

def generate_pdf(candidate_name,
                 cargo_name,
                 fecha_eval,
                 evaluator_email,
                 norm_scores,
                 raw_scores,
                 fortalezas,
                 monitoreo,
                 table_desc,
                 compromiso_text,
                 ajuste_text,
                 nota_text):

    buf = BytesIO()
    W, H = A4
    c = canvas.Canvas(buf, pagesize=A4)

    # -------- helpers internos --------
    def draw_wrapped_block(x, y_top, w, h, title, body_lines,
                           title_font="Helvetica-Bold",
                           title_size=8,
                           body_font="Helvetica",
                           body_size=7,
                           leading=10,
                           pad=8):
        # caja
        c.setStrokeColor(colors.lightgrey)
        c.setFillColor(colors.white)
        c.rect(x, y_top - h, w, h, stroke=1, fill=1)

        # título
        c.setFont(title_font, title_size)
        c.setFillColor(colors.black)
        c.drawString(x + pad, y_top - pad - 2, title)

        # body
        text_y = y_top - pad - 2 - leading - 2
        avail_w = w - 2*pad
        c.setFont(body_font, body_size)
        c.setFillColor(colors.black)

        wrapped = _wrap(c, body_lines, avail_w, body_font, body_size)
        for line in wrapped:
            if text_y < y_top - h + pad:
                break
            c.drawString(x + pad, text_y, line)
            text_y -= leading

        return text_y

    def draw_table_dimensiones(x, y_top, w, row_height, header_height, rows):
        """
        Tabla Detalle por dimensión — ahora de ancho completo.
        """
        total_h = header_height + row_height * len(rows)

        # caja global
        c.setStrokeColor(colors.lightgrey)
        c.setFillColor(colors.white)
        c.rect(x, y_top - total_h, w, total_h, stroke=1, fill=1)

        # título
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.black)
        c.drawString(x + 8, y_top - 14, "Detalle por dimensión")

        # columnas
        col_dim_x   = x + 8
        col_punt_x  = x + 140
        col_nivel_x = x + 210
        col_desc_x  = x + 260
        col_right   = x + w

        table_top = y_top - header_height  # parte vertical donde empiezan datos

        # encabezados
        c.setFont("Helvetica-Bold", 8)
        # línea superior de headers
        c.line(x, table_top + row_height, col_right, table_top + row_height)

        c.drawString(col_dim_x,  table_top + row_height - 12, "Dimensión")
        c.drawString(col_punt_x, table_top + row_height - 12, "Puntaje")
        c.drawString(col_nivel_x,table_top + row_height - 12, "Nivel")
        c.drawString(col_desc_x, table_top + row_height - 12, "Descripción breve")

        # línea bajo encabezados
        c.line(x, table_top, col_right, table_top)

        # separadores verticales
        c.line(col_punt_x - 6,  table_top + row_height, col_punt_x - 6,
               table_top - row_height*len(rows))
        c.line(col_nivel_x - 6, table_top + row_height, col_nivel_x - 6,
               table_top - row_height*len(rows))
        c.line(col_desc_x - 6,  table_top + row_height, col_desc_x - 6,
               table_top - row_height*len(rows))

        # filas
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.black)

        for i, row in enumerate(rows):
            row_top_y = table_top - i*row_height
            row_bot_y = table_top - (i+1)*row_height
            # línea inferior de fila
            c.line(x, row_bot_y, col_right, row_bot_y)

            # Dimensión (wrap hasta 3 líneas)
            dim_lines = _wrap(c, row["dim"],
                              (col_punt_x - 10) - col_dim_x,
                              "Helvetica-Bold", 8)
            c.setFont("Helvetica-Bold", 8)
            yy = row_top_y - 12
            for dl in dim_lines[:3]:
                c.drawString(col_dim_x, yy, dl)
                yy -= 10

            # Puntaje
            c.setFont("Helvetica", 8)
            c.drawString(col_punt_x, row_top_y - 12, row["puntaje"])

            # Nivel
            c.drawString(col_nivel_x, row_top_y - 12, row["nivel"])

            # Descripción breve (wrap hasta 5 líneas)
            desc_lines = _wrap(
                c,
                row["desc"],
                (col_right - 8) - col_desc_x,
                "Helvetica",
                8
            )
            yy2 = row_top_y - 12
            for dl2 in desc_lines[:5]:
                c.drawString(col_desc_x, yy2, dl2)
                yy2 -= 10

        return y_top - total_h

    # =====================================================
    # LAYOUT PDF
    # =====================================================

    W, H = A4
    margin_left  = 36
    margin_right = 36

    # Encabezado superior (izq/der)
    c.setFont("Helvetica-Bold",10)
    c.setFillColor(colors.black)
    c.drawString(margin_left, H-40, "EMPRESA / LOGO")
    c.setFont("Helvetica",7)
    c.drawString(margin_left, H-55, "Evaluación de personalidad ocupacional")

    c.setFont("Helvetica-Bold",11)
    c.drawRightString(W-margin_right, H-40, "Perfil EPQR-A · Selección Operativa")
    c.setFont("Helvetica",7)
    c.drawRightString(W-margin_right, H-55, "Uso interno RR.HH. / Procesos productivos")

    # -------------------- Gráfico de barras/linea (5 dims) --------------------
    chart_x = margin_left
    chart_y_bottom = H-260
    chart_w = 250
    chart_h = 120

    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    # eje Y
    c.line(chart_x, chart_y_bottom, chart_x, chart_y_bottom+chart_h)

    # rejilla + labels Y
    for lvl in range(0,7):
        yv = chart_y_bottom + (lvl/6.0)*chart_h
        c.setFont("Helvetica",6)
        c.setFillColor(colors.black)
        c.drawString(chart_x-15, yv-2, str(lvl))
        c.setStrokeColor(colors.lightgrey)
        c.line(chart_x, yv, chart_x+chart_w, yv)

    dims_order = [("E","E"),("EE","EE"),("DC","DC"),("C","C"),("M","M")]
    bar_colors = [
        colors.HexColor("#3b82f6"),  # azul
        colors.HexColor("#22c55e"),  # verde
        colors.HexColor("#f97316"),  # naranjo
        colors.HexColor("#6b7280"),  # gris
        colors.HexColor("#0ea5b7"),  # teal
    ]
    gap = 12
    bar_w = (chart_w - gap*(len(dims_order)+1)) / len(dims_order)
    tops = []

    for i,(key,label) in enumerate(dims_order):
        val_norm = norm_scores[key]  # 0-6
        bx = chart_x + gap + i*(bar_w+gap)
        bh = (val_norm/6.0)*chart_h
        by = chart_y_bottom

        c.setStrokeColor(colors.black)
        c.setFillColor(bar_colors[i])
        c.rect(bx, by, bar_w, bh, stroke=1, fill=1)

        tops.append((bx+bar_w/2.0, by+bh))

        lvl_txt = qualitative_level(val_norm)
        c.setFont("Helvetica-Bold",7)
        c.setFillColor(colors.black)
        c.drawCentredString(bx+bar_w/2.0, chart_y_bottom-14, label)

        c.setFont("Helvetica",6)
        c.drawCentredString(
            bx+bar_w/2.0,
            chart_y_bottom-26,
            f"{raw_scores[key]}/8  {val_norm:.1f}/6  {lvl_txt}"
        )

    # línea sobre los puntos
    c.setStrokeColor(colors.black)
    c.setLineWidth(1.2)
    for j in range(len(tops)-1):
        (x1,y1) = tops[j]
        (x2,y2) = tops[j+1]
        c.line(x1,y1,x2,y2)
    for (px,py) in tops:
        c.setFillColor(colors.black)
        c.circle(px,py,2.0,stroke=0,fill=1)

    c.setFont("Helvetica-Bold",8)
    c.setFillColor(colors.black)
    c.drawString(chart_x, chart_y_bottom+chart_h+12, "Perfil conductual (0–6)")

    # ---------- Caja datos candidato a la derecha ----------
    box_x = margin_left + chart_w + 30
    box_w = W - margin_right - box_x
    box_h = 70
    box_y_top = H-140

    c.setStrokeColor(colors.lightgrey)
    c.setFillColor(colors.white)
    c.rect(box_x, box_y_top-box_h, box_w, box_h, stroke=1, fill=1)

    yy = box_y_top-12
    c.setFont("Helvetica-Bold",8)
    c.setFillColor(colors.black)
    c.drawString(box_x+8, yy, f"Nombre: {candidate_name}")
    yy -= 12
    c.setFont("Helvetica",8)
    c.drawString(box_x+8, yy, f"Cargo evaluado: {cargo_name}")
    yy -= 12
    c.drawString(box_x+8, yy, f"Fecha evaluación: {fecha_eval}")
    yy -= 12
    c.drawString(box_x+8, yy, f"Evaluador: {evaluator_email.upper()}")
    yy -= 12
    c.setFont("Helvetica",6)
    c.setFillColor(colors.grey)
    c.drawString(box_x+8, yy, "Documento interno. No clínico.")

    # ---------- Guía de dimensiones (debajo datos candidato) ----------
    guide_h = 75
    guide_y_top = H-230
    c.setStrokeColor(colors.lightgrey)
    c.setFillColor(colors.white)
    c.rect(box_x, guide_y_top-guide_h, box_w, guide_h, stroke=1, fill=1)

    gy = guide_y_top-14
    c.setFont("Helvetica-Bold",8)
    c.setFillColor(colors.black)
    c.drawString(box_x+8, gy, "Guía de lectura de dimensiones")
    gy -= 12
    c.setFont("Helvetica",7)
    lines_dim = [
        "E  = Extraversión / Iniciativa social",
        "EE = Estabilidad Emocional (manejo de presión)",
        "DC = Dureza Conductual / Estilo directo",
        "C  = Consistencia / Autopresentación",
        "M  = Motivación / Compromiso con el Puesto",
    ]
    for gl in lines_dim:
        c.drawString(box_x+8, gy, gl)
        gy -= 10

    # =====================================================
    # TABLA DETALLE POR DIMENSIÓN (ANCHO COMPLETO)
    # =====================================================
    table_x = margin_left
    table_y_top = H - 360
    table_w = W - margin_right - margin_left
    row_h = 48
    header_h = 50

    dims_display = [
        ("E",  "Extraversión"),
        ("EE", "Estabilidad Emocional"),
        ("DC", "Dureza Conductual / Estilo Directo"),
        ("C",  "Consistencia / Autopresentación"),
        ("M",  "Motivación / Compromiso con el Puesto"),
    ]

    rows_for_table = []
    for key, label in dims_display:
        raw_v  = raw_scores[key]
        norm_v = norm_scores[key]
        lvl_v  = qualitative_level(norm_v)
        desc_v = table_desc[key]
        rows_for_table.append({
            "dim": label,
            "puntaje": f"{raw_v}/8   {norm_v:.1f}/6",
            "nivel": lvl_v,
            "desc": desc_v,
        })

    table_bottom_y = draw_table_dimensiones(
        table_x,
        table_y_top,
        table_w,
        row_height=row_h,
        header_height=header_h,
        rows=rows_for_table
    )

    # =====================================================
    # RESUMEN CONDUCTUAL OBSERVADO (ANCHO COMPLETO, DEBAJO TABLA)
    # =====================================================
    resumen_x = margin_left
    resumen_w = W - margin_right - margin_left
    resumen_h = 140
    resumen_top = table_bottom_y - 20  # espacio bajo la tabla

    c.setStrokeColor(colors.lightgrey)
    c.setFillColor(colors.white)
    c.rect(resumen_x, resumen_top - resumen_h, resumen_w, resumen_h, stroke=1, fill=1)

    inner_pad = 10
    yy2 = resumen_top - inner_pad

    # Título
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.black)
    c.drawString(resumen_x + inner_pad, yy2, "Resumen conductual observado")
    yy2 -= 14

    # Fortalezas
    c.setFont("Helvetica-Bold", 8)
    c.drawString(resumen_x + inner_pad, yy2, "Fortalezas potenciales:")
    yy2 -= 12

    c.setFont("Helvetica", 8)
    for ftxt in fortalezas:
        bullet_lines = _wrap(
            c,
            "• " + ftxt,
            resumen_w - 2*inner_pad,
            "Helvetica",
            8
        )
        for line in bullet_lines:
            if yy2 < (resumen_top - resumen_h + inner_pad + 20):
                break
            c.drawString(resumen_x + inner_pad + 5, yy2, line)
            yy2 -= 10
        yy2 -= 4

    # Monitoreo
    yy2 -= 4
    c.setFont("Helvetica-Bold", 8)
    c.drawString(resumen_x + inner_pad, yy2, "Aspectos a monitorear / apoyo sugerido:")
    yy2 -= 12

    c.setFont("Helvetica", 8)
    for mtxt in monitoreo:
        bullet_lines = _wrap(
            c,
            "• " + mtxt,
            resumen_w - 2*inner_pad,
            "Helvetica",
            8
        )
        for line in bullet_lines:
            if yy2 < (resumen_top - resumen_h + inner_pad + 10):
                break
            c.drawString(resumen_x + inner_pad + 5, yy2, line)
            yy2 -= 10
        yy2 -= 4

    # =====================================================
    # BLOQUE FINAL COMPROMISO / AJUSTE / NOTA (CAJAS)
    # =====================================================
    concl_x = margin_left
    concl_w = W - margin_right - margin_left
    concl_h = 170
    concl_top = resumen_top - resumen_h - 30

    c.setStrokeColor(colors.lightgrey)
    c.setFillColor(colors.white)
    c.rect(concl_x, concl_top - concl_h, concl_w, concl_h, stroke=1, fill=1)

    # subcaja 1
    sub_h = 50
    sub1_top = concl_top
    draw_wrapped_block(
        x=concl_x+6,
        y_top=sub1_top,
        w=concl_w-12,
        h=sub_h,
        title="Compromiso / Permanencia",
        body_lines=compromiso_text,
        title_font="Helvetica-Bold",
        title_size=8,
        body_font="Helvetica",
        body_size=7,
        leading=10,
        pad=8
    )

    # subcaja 2
    sub2_top = sub1_top - sub_h - 6
    draw_wrapped_block(
        x=concl_x+6,
        y_top=sub2_top,
        w=concl_w-12,
        h=sub_h,
        title="Ajuste al cargo evaluado",
        body_lines=ajuste_text,
        title_font="Helvetica-Bold",
        title_size=8,
        body_font="Helvetica",
        body_size=7,
        leading=10,
        pad=8
    )

    # subcaja 3
    sub3_top = sub2_top - sub_h - 6
    sub3_h = concl_h - (sub_h*2 + 12)
    draw_wrapped_block(
        x=concl_x+6,
        y_top=sub3_top,
        w=concl_w-12,
        h=sub3_h,
        title="Nota metodológica",
        body_lines=nota_text,
        title_font="Helvetica-Bold",
        title_size=8,
        body_font="Helvetica",
        body_size=6,
        leading=9,
        pad=8
    )

    # footer
    c.setFont("Helvetica",6)
    c.setFillColor(colors.grey)
    c.drawRightString(W-margin_right, 40,
        "Uso interno RR.HH. · EPQR-A Adaptado · No clínico"
    )

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()

# =========================================================
# UI VISTAS STREAMLIT
# =========================================================
def view_setup():
    st.markdown("### Evaluación Conductual EPQR-A (Selección Operativa)")
    st.write("Complete los datos iniciales para comenzar el test.")
    job_options = {k:v["name"] for k,v in JOB_PROFILES.items()}

    st.session_state.job_key = st.selectbox(
        "Cargo a evaluar",
        options=list(job_options.keys()),
        format_func=lambda k: job_options[k],
        index=0 if st.session_state.job_key == "" else list(job_options.keys()).index(st.session_state.job_key)
    )

    st.session_state.candidate_name = st.text_input(
        "Nombre del candidato",
        value=st.session_state.candidate_name
    )

    st.session_state.evaluator_email = st.text_input(
        "Correo del evaluador (se mostrará en el informe interno)",
        value=st.session_state.evaluator_email
    )

    if st.button("Iniciar test", type="primary", use_container_width=True):
        if st.session_state.candidate_name and st.session_state.evaluator_email and st.session_state.job_key:
            st.session_state.stage = "test"
            st.session_state.q_idx = 0
            st.session_state.answers = {}
            st.session_state.results = None
            st.experimental_rerun()

def on_answer_click(val):
    q_i = st.session_state.q_idx
    st.session_state.answers[q_i] = val

    if q_i < len(QUESTIONS)-1:
        st.session_state.q_idx = q_i + 1
    else:
        # terminamos
        finish_assessment()
    st.session_state._advance = True

def finish_assessment():
    # calcular resultados
    raw_scores, norm_scores, totals = compute_scores(st.session_state.answers)

    fortalezas, monitoreo = build_strengths_and_risks(norm_scores)
    table_desc = build_descriptions(norm_scores)
    compromiso_text = build_compromiso_text(norm_scores)
    ajuste_text = build_final_adjustment_text(norm_scores, st.session_state.job_key)
    nota_text = build_nota_text()

    fecha_eval = datetime.now().strftime("%d/%m/%Y %H:%M")
    cargo_name = JOB_PROFILES[st.session_state.job_key]["name"]

    # generar PDF
    pdf_bytes = generate_pdf(
        candidate_name=st.session_state.candidate_name,
        cargo_name=cargo_name,
        fecha_eval=fecha_eval,
        evaluator_email=st.session_state.evaluator_email,
        norm_scores=norm_scores,
        raw_scores=raw_scores,
        fortalezas=fortalezas,
        monitoreo=monitoreo,
        table_desc=table_desc,
        compromiso_text=compromiso_text,
        ajuste_text=ajuste_text,
        nota_text=nota_text
    )

    st.session_state.results = {
        "pdf": pdf_bytes,
        "fecha": fecha_eval,
    }
    st.session_state.stage = "done"

def view_test():
    idx = st.session_state.q_idx
    q = QUESTIONS[idx]
    total = len(QUESTIONS)
    progress = int(((idx+1)/total)*100)

    # barra de progreso simple estilo HTML inline
    st.markdown(f"""
    <div style='background:#f8fafc;padding:1rem 1.5rem;
                border-bottom:1px solid #e2e8f0;'>
        <div style='height:6px;border-radius:999px;
                    background:#e2e8f0;overflow:hidden;'>
            <div style='height:6px;background:#3b82f6;
                        width:{progress}%;'></div>
        </div>
        <div style="font-size:.8rem;color:#475569;
                    margin-top:.5rem;display:flex;
                    justify-content:space-between;">
            <span>Pregunta {idx+1} de {total}</span>
            <span>{progress}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style='background:#fff;padding:2rem 1.5rem;'>
        <p style='font-size:1.05rem;color:#1e293b;
                  line-height:1.4;margin:0 0 1.5rem 0;'>
            {q["text"]}
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Sí", key=f"yes_{idx}", use_container_width=True):
            on_answer_click(1)
    with col2:
        if st.button("❌ No", key=f"no_{idx}", use_container_width=True):
            on_answer_click(0)

    st.markdown("""
    <div style='background:#f8fafc;padding:1rem 1.5rem;
                border-top:1px solid #e2e8f0;font-size:.75rem;
                color:#475569;'>
        <b>Confidencialidad:</b> Uso interno RR.HH. / Selección operativa.
        El candidato no recibe copia directa del informe.
    </div>
    """, unsafe_allow_html=True)

    if st.session_state._advance:
        st.session_state._advance = False
        st.experimental_rerun()

def view_done():
    st.markdown("""
    <div style='background:#ecfdf5;border:1px solid #6ee7b7;
                color:#065f46;border-radius:.75rem;
                padding:2rem 1.5rem;text-align:center;
                max-width:480px;margin:2rem auto;
                font-family:system-ui, -apple-system, BlinkMacSystemFont;'>
        <div style='font-size:2.5rem;line-height:1;'>✅</div>
        <div style='font-size:1.25rem;font-weight:600;margin-top:.5rem;'>
            Test completado
        </div>
        <div style='font-size:.9rem;margin-top:.5rem;'>
            La evaluación ha sido registrada correctamente.
        </div>
        <div style='font-size:.8rem;color:#065f46;
                    margin-top:1rem;line-height:1.4;'>
            El informe interno para RR.HH. fue generado.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # entregar descarga del PDF al evaluador en pantalla
    if st.session_state.results and "pdf" in st.session_state.results:
        st.download_button(
            "⬇️ Descargar informe interno (PDF)",
            data=st.session_state.results["pdf"],
            file_name="Informe_EPQRA.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary"
        )

    st.markdown("---")
    if st.button("Realizar nueva evaluación", type="secondary", use_container_width=True):
        # reset parcial
        st.session_state.stage = "setup"
        st.session_state.answers = {}
        st.session_state.q_idx = 0
        st.session_state.results = None
        st.experimental_rerun()

# =========================================================
# MAIN FLOW
# =========================================================
init_state()

if st.session_state.stage == "setup":
    view_setup()
elif st.session_state.stage == "test":
    view_test()
else:
    view_done()
