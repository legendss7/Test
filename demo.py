# ============================================================
# EPQR-A Operativo con 5 dimensiones (E, EE, DC, C, M)
# 40 ítems totales (8 por dimensión)
# Visual tipo tarjeta limpia (sin HTML sin cerrar)
# Avance con 1 click (callback + rerun)
# Genera PDF ordenado con 5 barras y lo envía automáticamente
# ============================================================

import streamlit as st
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import smtplib
from email.message import EmailMessage

# -----------------------------
# CONFIG STREAMLIT
# -----------------------------
st.set_page_config(
    page_title="Evaluación EPQR-A Operativa",
    page_icon="🧪",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# -----------------------------
# PREGUNTAS (40 total)
# 8 por dimensión:
#   E  = Extraversión / iniciativa social
#   N  = Neuroticismo crudo (luego invertimos y reportamos EE = Estabilidad Emocional)
#   P  = Dureza Conductual / estilo directo
#   S  = Consistencia / Autopresentación
#   M  = Motivación / Compromiso / Permanencia
#
# Nota sobre categorías:
#  E:       "E"      Sí=1 / No=0
#  E_rev:   invertida (preferencia por retraerse) => Sí=0 / No=1
#
#  N:       "N"      Sí=1 / No=0  (reactividad emocional)
#  N_rev:   invertida (calma declarada) => Sí=0 / No=1
#  EE_raw = 8 - N_total   (0..8)
#
#  P_func:  Sí=1 / No=0   (firmeza funcional operativa)
#  P:       invertida     Sí=0 / No=1   (riesgo egoísta, saltarse norma)
#  DC = P_func + invertida
#
#  S_ok:    Sí=1 / No=0   (respeto normas, confiable)
#  S:       invertida     Sí=0 / No=1   (conducta poco ética declarada)
#  C  = S_ok + invertida
#
#  M_commit: Sí=1 / No=0  (quiero quedarme / estabilidad)
#  M_leaver:  Sí=0 / No=1 (me iría rápido si algo no me gusta)
#  M  = commit + leaver
# -----------------------------

QUESTIONS = [
    # Extraversión (E)
    {"text": "Me siento cómodo/a hablando con personas que recién conozco.", "cat": "E"},
    {"text": "Puedo tomar la palabra frente a un grupo sin mucho problema.", "cat": "E"},
    {"text": "Cuando hay que coordinar al equipo, suelo ofrecerme a explicar qué hacer.", "cat": "E"},
    {"text": "Me gusta interactuar con otras personas durante la jornada.", "cat": "E"},
    {"text": "Prefiero estar en silencio y que otros hablen por mí.", "cat": "E_rev"},
    {"text": "Evito situaciones donde deba hablar en voz alta frente a varios.", "cat": "E_rev"},
    {"text": "Me ha resultado fácil motivar a otros cuando se están quedando atrás.", "cat": "E"},
    {"text": "Disfruto estar rodeado/a de personas en el turno.", "cat": "E"},

    # Neuroticismo crudo (N) -> luego se convierte a EE = Estabilidad Emocional
    {"text": "Bajo presión me pongo muy ansioso/a.", "cat": "N"},
    {"text": "Me cuesta mantener la calma cuando todo se acelera.", "cat": "N"},
    {"text": "Cuando algo sale mal, me quedo dándole vueltas en la cabeza mucho rato.", "cat": "N"},
    {"text": "Me altero con facilidad frente a conflictos en el trabajo.", "cat": "N"},
    {"text": "Puedo seguir funcionando aun con estrés encima.", "cat": "N_rev"},
    {"text": "Siento que controlo mis reacciones incluso cuando hay urgencia.", "cat": "N_rev"},
    {"text": "Me desespero rápido si hay muchas órdenes distintas al mismo tiempo.", "cat": "N"},
    {"text": "Cuando las cosas se enredan, logro mantenerme estable.", "cat": "N_rev"},

    # Dureza Conductual / Estilo Directo (P / DC)
    {"text": "Si alguien no hace su parte, le digo directamente que se ponga al día.", "cat": "P_func"},
    {"text": "Para mí es más importante que el trabajo salga bien que quedar bien con todos.", "cat": "P_func"},
    {"text": "Me da lo mismo si mis palabras suenan duras mientras el turno se cumpla.", "cat": "P"},
    {"text": "Cuando hay una instrucción clara, espero que se cumpla sin discusión.", "cat": "P_func"},
    {"text": "He pasado por encima de otros para salir beneficiado/a.", "cat": "P"},
    {"text": "Puedo mantenerme firme incluso si otros se enojan un poco.", "cat": "P_func"},
    {"text": "Prefiero seguir mis propias reglas aunque choquen con las normas.", "cat": "P"},
    {"text": "Puedo marcar prioridades cuando hay muchas tareas al mismo tiempo.", "cat": "P_func"},

    # Consistencia / Autopresentación (S / C)
    {"text": "Trato de dar siempre una buena impresión a la jefatura.", "cat": "S_ok"},
    {"text": "He mentido para evitar asumir un error propio.", "cat": "S"},
    {"text": "Me preocupo de seguir los procedimientos tal como están definidos.", "cat": "S_ok"},
    {"text": "He culpado a otra persona sabiendo que el error fue mío.", "cat": "S"},
    {"text": "Me importa que me consideren alguien confiable.", "cat": "S_ok"},
    {"text": "He tomado algo que no era mío en el trabajo.", "cat": "S"},
    {"text": "Respeto las normas de seguridad aunque nadie esté mirando.", "cat": "S_ok"},
    {"text": "A veces hago trampa si sé que no me van a pillar.", "cat": "S"},

    # Motivación / Compromiso (M)
    {"text": "Si el turno está difícil, igual termino la tarea aunque implique un poco más de esfuerzo.", "cat": "M_commit"},
    {"text": "Para mí este trabajo es sólo algo temporal hasta encontrar algo mejor luego.", "cat": "M_leaver"},
    {"text": "Prefiero quedarme y hablar los problemas antes que irme al primer conflicto.", "cat": "M_commit"},
    {"text": "Si las reglas del lugar no me gustan en la primera semana, prefiero renunciar rápido.", "cat": "M_leaver"},
    {"text": "Me importa que me vean como una persona estable y que cumple.", "cat": "M_commit"},
    {"text": "Si siento que me exigen mucho, me voy sin pensarlo demasiado.", "cat": "M_leaver"},
    {"text": "Quiero que me consideren alguien en quien se puede confiar a largo plazo.", "cat": "M_commit"},
    {"text": "Me cambiaría rápido de puesto si algo no me acomoda de inmediato.", "cat": "M_leaver"},
]

TOTAL_QUESTIONS = len(QUESTIONS)  # 40

# -----------------------------
# Perfiles de cargo y rangos esperados en escala 0..6
# -----------------------------
JOB_PROFILES = {
    "operario": {
        "title": "Operario de Producción",
        "req": {
            "E":  (1.5, 4.5),
            "EE": (3.0, 6.0),
            "DC": (2.0, 5.0),
            "C":  (3.0, 6.0),
            "M":  (3.0, 6.0),
        },
    },
    "supervisor": {
        "title": "Supervisor Operativo",
        "req": {
            "E":  (3.0, 6.0),
            "EE": (3.0, 6.0),
            "DC": (3.0, 6.0),
            "C":  (3.0, 6.0),
            "M":  (4.0, 6.0),
        },
    },
    "tecnico": {
        "title": "Técnico de Mantenimiento",
        "req": {
            "E":  (1.0, 4.0),
            "EE": (3.0, 6.0),
            "DC": (2.0, 5.0),
            "C":  (3.5, 6.0),
            "M":  (4.0, 6.0),
        },
    },
    "logistica": {
        "title": "Personal de Logística",
        "req": {
            "E":  (2.0, 5.5),
            "EE": (3.0, 6.0),
            "DC": (2.0, 5.5),
            "C":  (3.0, 6.0),
            "M":  (3.0, 6.0),
        },
    },
}

# -----------------------------
# Estado Streamlit
# -----------------------------
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
    st.session_state.answers = {i: None for i in range(TOTAL_QUESTIONS)}

if "_need_rerun" not in st.session_state:
    st.session_state._need_rerun = False

if "already_sent" not in st.session_state:
    st.session_state.already_sent = False


# -----------------------------
# Funciones de cálculo de puntajes
# -----------------------------
def _norm_to_six(raw, max_raw=8):
    # normaliza 0..8 → 0..6
    return (raw / max_raw) * 6.0

def compute_scores(answers_dict):
    E_raw = 0
    N_raw = 0
    P_raw_func = 0
    P_raw_inv = 0
    S_raw_ok = 0
    S_raw_inv = 0
    M_raw_commit = 0
    M_raw_leaver = 0

    for idx, q in enumerate(QUESTIONS):
        ans = answers_dict.get(idx)
        if ans is None:
            continue
        cat = q["cat"]

        # E
        if cat == "E":
            if ans == 1: E_raw += 1
        elif cat == "E_rev":
            if ans == 0: E_raw += 1

        # N
        if cat == "N":
            if ans == 1: N_raw += 1
        elif cat == "N_rev":
            if ans == 0: N_raw += 1

        # P / DC
        if cat == "P_func":
            if ans == 1: P_raw_func += 1
        elif cat == "P":
            if ans == 0: P_raw_inv += 1

        # S / C
        if cat == "S_ok":
            if ans == 1: S_raw_ok += 1
        elif cat == "S":
            if ans == 0: S_raw_inv += 1

        # M
        if cat == "M_commit":
            if ans == 1: M_raw_commit += 1
        elif cat == "M_leaver":
            if ans == 0: M_raw_leaver += 1

    P_raw = P_raw_func + P_raw_inv
    S_raw = S_raw_ok + S_raw_inv
    M_raw = M_raw_commit + M_raw_leaver

    # EE_raw = 8 - N_raw
    EE_raw = 8 - N_raw
    if EE_raw < 0: EE_raw = 0
    if EE_raw > 8: EE_raw = 8

    # normalizados
    E_norm  = _norm_to_six(E_raw)
    EE_norm = _norm_to_six(EE_raw)
    DC_norm = _norm_to_six(P_raw)
    C_norm  = _norm_to_six(S_raw)
    M_norm  = _norm_to_six(M_raw)

    return {
        "raw": {
            "E":  E_raw,
            "EE": EE_raw,
            "DC": P_raw,
            "C":  S_raw,
            "M":  M_raw,
        },
        "norm": {
            "E":  E_norm,
            "EE": EE_norm,
            "DC": DC_norm,
            "C":  C_norm,
            "M":  M_norm,
        }
    }

def qualitative_level(norm_score):
    # 0..6 → Bajo / Medio / Alto
    if norm_score > 4.5:
        return "Alto"
    elif norm_score > 2.0:
        return "Medio"
    else:
        return "Bajo"

def build_short_desc(E, EE, DC, C, M):
    desc = {}
    # E
    if E > 4.5:
        desc["E"] = "Alta iniciativa social; comunica y coordina."
    elif E > 2.0:
        desc["E"] = "Interacción funcional cuando la tarea lo pide."
    else:
        desc["E"] = "Estilo más reservado; baja exposición."
    # EE
    if EE > 4.5:
        desc["EE"] = "Tolerancia a presión y foco estable."
    elif EE > 2.0:
        desc["EE"] = "Se sostiene con apoyo claro en tensión."
    else:
        desc["EE"] = "Puede requerir contención en alta urgencia."
    # DC
    if DC > 4.5:
        desc["DC"] = "Directo/a al marcar prioridades operativas."
    elif DC > 2.0:
        desc["DC"] = "Puede sostener criterios firmes de cumplimiento."
    else:
        desc["DC"] = "Evita confrontación directa; prefiere orden sin choque."
    # C
    if C > 4.5:
        desc["C"] = "Alta orientación a normas y confiabilidad."
    elif C > 2.0:
        desc["C"] = "Cuida imagen responsable y respeta procesos."
    else:
        desc["C"] = "Puede priorizar criterio propio sobre la norma."
    # M
    if M > 4.5:
        desc["M"] = "Alta motivación declarada para quedarse."
    elif M > 2.0:
        desc["M"] = "Compromiso condicionado a trato justo/claridad."
    else:
        desc["M"] = "Riesgo de rotación temprana si no se adapta."
    return desc

def build_strengths_risks(E, EE, DC, C, M):
    fortalezas = []
    monitoreo = []

    if E > 4.5:
        fortalezas.append("Disposición a comunicarse y coordinar con otros.")
    elif E > 2.0:
        fortalezas.append("Puede interactuar funcionalmente en equipo.")
    else:
        monitoreo.append("Puede requerir instrucciones claras en vez de exposición pública.")

    if EE > 4.5:
        fortalezas.append("Manejo de presión estable; foco en la tarea.")
    elif EE <= 2.0:
        monitoreo.append("Podría necesitar contención directa en escenarios de alta urgencia.")

    if DC > 4.5:
        fortalezas.append("Capacidad de marcar prioridades operativas bajo presión.")
        monitoreo.append("Su comunicación directa puede percibirse exigente; acordar estándares claros.")
    elif DC > 2.0:
        fortalezas.append("Sostiene criterios de cumplimiento sin evitar responsabilidad.")
    else:
        monitoreo.append("Tiende a evitar confrontación; riesgo de dejar pasar incumplimientos.")

    if C > 4.5:
        fortalezas.append("Alta adhesión declarada a normas/procedimientos.")
    elif C <= 2.0:
        monitoreo.append("Puede tensionar estándares si prima su propio criterio.")

    if M > 4.5:
        fortalezas.append("Declara intención de permanencia y compromiso con el puesto.")
    elif M <= 2.0:
        monitoreo.append("Manifiesta riesgo de rotación temprana si el entorno no calza rápido.")

    return fortalezas[:3], monitoreo[:3]

def build_commitment_line(M):
    if M > 4.5:
        return "Declara intención de permanencia estable en el rol."
    elif M > 2.0:
        return "Compromiso condicionado: se mantiene si percibe trato justo y claridad."
    else:
        return "Existe riesgo de rotación temprana si la adaptación inicial no calza."

def match_job_profile(job_key, E, EE, DC, C, M):
    req = JOB_PROFILES[job_key]["req"]
    scores = {"E":E,"EE":EE,"DC":DC,"C":C,"M":M}
    ok_all = True
    for dim,(mn,mx) in req.items():
        if not (scores[dim] >= mn and scores[dim] <= mx):
            ok_all = False
            break
    cargo_name = JOB_PROFILES[job_key]["title"]
    if ok_all:
        return (
            "Conclusión: El perfil evaluado se considera GLOBALMENTE CONSISTENTE "
            f"con las exigencias conductuales habituales del cargo {cargo_name}."
        )
    else:
        return (
            "Conclusión: El perfil evaluado REQUIERE REVISIÓN ADICIONAL antes de confirmar "
            f"idoneidad para el cargo {cargo_name}. Se sugiere profundizar en entrevista "
            "focalizada y verificación de referencias."
        )

# -----------------------------
# Helpers PDF
# -----------------------------
def make_wrapped_lines(c, text, max_width, font_name="Helvetica", font_size=8):
    words = text.split()
    if not words:
        return [""]
    lines=[]
    cur=words[0]
    for w in words[1:]:
        test = cur + " " + w
        if c.stringWidth(test, font_name, font_size) <= max_width:
            cur = test
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines

def draw_wrapped_paragraph(c, text, x, y, max_width, font_name="Helvetica", font_size=8, leading=10, color=colors.black, max_lines=None):
    c.setFont(font_name, font_size)
    c.setFillColor(color)
    lines = make_wrapped_lines(c, text, max_width, font_name, font_size)
    if max_lines is not None:
        lines = lines[:max_lines]
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y

def generate_pdf(candidate_name,
                 cargo_name,
                 fecha_eval,
                 evaluator_email,
                 norm_scores,
                 raw_scores,
                 fortalezas,
                 monitoreo,
                 table_desc,
                 cierre_text,
                 nota_text):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4

    # colores barras
    bar_colors = [
        colors.Color(0.20,0.40,0.80),  # E
        colors.Color(0.15,0.60,0.30),  # EE
        colors.Color(0.90,0.40,0.20),  # DC
        colors.Color(0.40,0.40,0.40),  # C
        colors.Color(0.25,0.50,0.60),  # M
    ]

    # Header
    c.setFont("Helvetica-Bold",10)
    c.drawString(30, H-30, "EMPRESA / LOGO")
    c.setFont("Helvetica",7)
    c.drawString(30, H-42, "Evaluación de personalidad ocupacional")

    c.setFont("Helvetica-Bold",11)
    c.drawRightString(W-30, H-30, "Perfil EPQR-A · Selección Operativa")
    c.setFont("Helvetica",7)
    c.drawRightString(W-30, H-42, "Uso interno RR.HH. / Procesos productivos")

    # Gráfico de barras (5 dims)
    chart_x = 30
    chart_y_bottom = H-235
    chart_h = 120
    chart_w = 250

    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.line(chart_x, chart_y_bottom, chart_x, chart_y_bottom+chart_h)

    for lvl in range(0,7):
        yv = chart_y_bottom + (lvl/6.0)*chart_h
        c.setFont("Helvetica",6)
        c.setFillColor(colors.black)
        c.drawString(chart_x-15, yv-2, str(lvl))
        c.setStrokeColor(colors.lightgrey)
        c.line(chart_x, yv, chart_x+chart_w, yv)

    dims_order = [("E","E"),("EE","EE"),("DC","DC"),("C","C"),("M","M")]
    gap = 12
    bar_w = (chart_w - gap*(len(dims_order)+1)) / len(dims_order)
    tops=[]

    for i,(key,label) in enumerate(dims_order):
        val_norm = norm_scores[key]
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
            chart_y_bottom-24,
            f"{raw_scores[key]}/8  {val_norm:.1f}/6  {lvl_txt}"
        )

    c.setStrokeColor(colors.black)
    c.setLineWidth(1.2)
    for j in range(len(tops)-1):
        (x1,y1)=tops[j]
        (x2,y2)=tops[j+1]
        c.line(x1,y1,x2,y2)
    for (px,py) in tops:
        c.setFillColor(colors.black)
        c.circle(px,py,2.5,stroke=0,fill=1)

    c.setFont("Helvetica-Bold",8)
    c.setFillColor(colors.black)
    c.drawString(chart_x, chart_y_bottom+chart_h+10, "Perfil conductual (0–6)")

    # Caja datos candidato (arriba derecha)
    box_x = 300
    box_y_top = H-130
    box_w = 250
    box_h = 70
    c.setStrokeColor(colors.lightgrey)
    c.setFillColor(colors.white)
    c.rect(box_x, box_y_top-box_h, box_w, box_h, stroke=1, fill=1)

    yy = box_y_top-12
    c.setFont("Helvetica-Bold",8)
    c.setFillColor(colors.black)
    c.drawString(box_x+8, yy, f"Nombre: {candidate_name}")
    yy -= 10
    c.setFont("Helvetica",8)
    c.drawString(box_x+8, yy, f"Cargo evaluado: {cargo_name}")
    yy -= 10
    c.drawString(box_x+8, yy, f"Fecha evaluación: {fecha_eval}")
    yy -= 10
    c.drawString(box_x+8, yy, f"Evaluador: {evaluator_email.upper()}")
    yy -= 10
    c.setFont("Helvetica",6)
    c.setFillColor(colors.grey)
    c.drawString(box_x+8, yy, "Documento de uso interno. No clínico.")

    # Guía dimensiones
    guide_x = 300
    guide_y_top = H-210
    guide_w = 250
    guide_h = 70
    c.setStrokeColor(colors.lightgrey)
    c.setFillColor(colors.white)
    c.rect(guide_x, guide_y_top-guide_h, guide_w, guide_h, stroke=1, fill=1)

    gy = guide_y_top-12
    c.setFont("Helvetica-Bold",8)
    c.setFillColor(colors.black)
    c.drawString(guide_x+8, gy, "Guía de lectura de dimensiones")
    gy -= 10
    c.setFont("Helvetica",7)
    guide_lines = [
        "E  = Extraversión / iniciativa social",
        "EE = Estabilidad Emocional (manejo presión)",
        "DC = Dureza Conductual / estilo directo",
        "C  = Consistencia / Autopresentación",
        "M  = Motivación / Compromiso con el Puesto",
    ]
    for gl in guide_lines:
        c.drawString(guide_x+8, gy, gl)
        gy -= 9

    # Resumen conductual (Fortalezas / Monitoreo)
    sum_x = 300
    sum_y_top = H-300
    sum_w = 250
    sum_h = 90
    c.setStrokeColor(colors.lightgrey)
    c.setFillColor(colors.white)
    c.rect(sum_x, sum_y_top-sum_h, sum_w, sum_h, stroke=1, fill=1)

    sy = sum_y_top-12
    c.setFont("Helvetica-Bold",8)
    c.setFillColor(colors.black)
    c.drawString(sum_x+8, sy, "Resumen conductual observado")
    sy -= 10

    c.setFont("Helvetica-Bold",7)
    c.drawString(sum_x+8, sy, "Fortalezas potenciales:")
    sy -= 9
    c.setFont("Helvetica",7)
    for f in fortalezas:
        lines = make_wrapped_lines(c, "• "+f, sum_w-16, "Helvetica",7)
        for line in lines:
            c.drawString(sum_x+10, sy, line)
            sy -= 9
            if sy < sum_y_top - sum_h + 15:
                break
        if sy < sum_y_top - sum_h + 15:
            break

    sy -= 4
    c.setFont("Helvetica-Bold",7)
    c.drawString(sum_x+8, sy, "Aspectos a monitorear / apoyo sugerido:")
    sy -= 9
    c.setFont("Helvetica",7)
    for m in monitoreo:
        lines = make_wrapped_lines(c, "• "+m, sum_w-16, "Helvetica",7)
        for line in lines:
            c.drawString(sum_x+10, sy, line)
            sy -= 9
            if sy < sum_y_top - sum_h + 10:
                break
        if sy < sum_y_top - sum_h + 10:
            break

    # Tabla resumen por dimensión
    table_x = 30
    table_y_top = H-330
    table_w = W-60
    table_h = 110
    c.setStrokeColor(colors.lightgrey)
    c.setFillColor(colors.white)
    c.rect(table_x, table_y_top-table_h, table_w, table_h, stroke=1, fill=1)

    c.setFont("Helvetica-Bold",9)
    c.setFillColor(colors.black)
    c.drawString(table_x, table_y_top+10, "Detalle por dimensión (resumen interpretativo)")

    c.setFont("Helvetica-Bold",8)
    c.drawString(table_x+8,   table_y_top-14, "Dimensión")
    c.drawString(table_x+100, table_y_top-14, "Puntaje (0–8 / 0–6)")
    c.drawString(table_x+200, table_y_top-14, "Nivel")
    c.drawString(table_x+250, table_y_top-14, "Descripción breve")

    row_y = table_y_top-26
    row_gap = 20
    dims_display = [
        ("E",  "Extraversión"),
        ("EE", "Estabilidad Emocional"),
        ("DC", "Dureza Conductual / Estilo Directo"),
        ("C",  "Consistencia / Autopresentación"),
        ("M",  "Motivación / Compromiso con el Puesto"),
    ]

    for key,label in dims_display:
        raw_v  = raw_scores[key]
        norm_v = norm_scores[key]
        lvl_v  = qualitative_level(norm_v)
        desc_v = table_desc[key]

        c.setFont("Helvetica-Bold",7)
        c.drawString(table_x+8, row_y, label)

        c.setFont("Helvetica",7)
        c.drawString(table_x+100, row_y, f"{raw_v}/8  {norm_v:.1f}/6")
        c.drawString(table_x+200, row_y, lvl_v)
        draw_wrapped_paragraph(
            c,
            desc_v,
            table_x+250,
            row_y,
            table_w-260,
            font_name="Helvetica",
            font_size=7,
            leading=9,
            color=colors.black,
            max_lines=2
        )

        row_y -= row_gap

    # Conclusión
    concl_x = 30
    concl_y_top = 160
    concl_w = W-60
    concl_h = 110
    c.setStrokeColor(colors.lightgrey)
    c.setFillColor(colors.white)
    c.rect(concl_x, concl_y_top-concl_h, concl_w, concl_h, stroke=1, fill=1)

    yy = concl_y_top-14
    c.setFont("Helvetica-Bold",8)
    c.setFillColor(colors.black)
    c.drawString(concl_x+8, yy, "Conclusión Operativa")
    yy -= 10
    yy = draw_wrapped_paragraph(
        c,
        cierre_text,
        concl_x+8,
        yy,
        concl_w-16,
        font_name="Helvetica",
        font_size=7,
        leading=9,
        color=colors.black,
        max_lines=6
    )
    yy -= 6
    c.setFont("Helvetica-Bold",8)
    c.drawString(concl_x+8, yy, "Nota metodológica")
    yy -= 10
    draw_wrapped_paragraph(
        c,
        nota_text,
        concl_x+8,
        yy,
        concl_w-16,
        font_name="Helvetica",
        font_size=6,
        leading=8,
        color=colors.grey,
        max_lines=6
    )

    c.setFont("Helvetica",6)
    c.setFillColor(colors.grey)
    c.drawRightString(W-30, 40, "Uso interno RR.HH. · EPQR-A Adaptado · No clínico")

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()

def send_email_with_pdf(to_email, pdf_bytes, filename, subject, body_text):
    FROM_ADDR = "jo.tajtaj@gmail.com"
    APP_PASS  = "nlkt kujl ebdg cyts"
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = FROM_ADDR
    msg["To"] = to_email
    msg.set_content(body_text)
    msg.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename=filename
    )
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(FROM_ADDR, APP_PASS)
        smtp.send_message(msg)

def finalize_and_send():
    scores = compute_scores(st.session_state.answers)
    raw_scores  = scores["raw"]
    norm_scores = scores["norm"]

    E  = norm_scores["E"]
    EE = norm_scores["EE"]
    DC = norm_scores["DC"]
    C_ = norm_scores["C"]
    M  = norm_scores["M"]

    table_desc = build_short_desc(E,EE,DC,C_,M)
    fortalezas, monitoreo = build_strengths_risks(E,EE,DC,C_,M)
    compromiso_line = build_commitment_line(M)
    cierre_match    = match_job_profile(
        st.session_state.selected_job,
        E,EE,DC,C_,M
    )
    cierre_text = compromiso_line + " " + cierre_match

    nota_text = (
        "Este informe se basa en la auto-respuesta declarada por la persona evaluada "
        "en el Cuestionario EPQR-A. Los resultados describen tendencias y preferencias "
        "conductuales observadas en el momento de la evaluación. No constituyen un "
        "diagnóstico clínico ni, por sí solos, una determinación absoluta de idoneidad "
        "laboral. Se recomienda complementar esta información con entrevista estructurada, "
        "verificación de experiencia y evaluación técnica del cargo."
    )

    now_txt = datetime.now().strftime("%d/%m/%Y %H:%M")
    cargo_name = JOB_PROFILES[st.session_state.selected_job]["title"]

    pdf_bytes = generate_pdf(
        candidate_name   = st.session_state.candidate_name,
        cargo_name       = cargo_name,
        fecha_eval       = now_txt,
        evaluator_email  = st.session_state.evaluator_email,
        norm_scores      = norm_scores,
        raw_scores       = raw_scores,
        fortalezas       = fortalezas,
        monitoreo        = monitoreo,
        table_desc       = table_desc,
        cierre_text      = cierre_text,
        nota_text        = nota_text
    )

    if not st.session_state.already_sent:
        try:
            send_email_with_pdf(
                to_email   = st.session_state.evaluator_email,
                pdf_bytes  = pdf_bytes,
                filename   = "Informe_EPQR_Operativo.pdf",
                subject    = "Informe EPQR-A Operativo (Selección)",
                body_text  = (
                    "Adjunto informe interno EPQR-A Operativo "
                    f"({st.session_state.candidate_name} / {cargo_name}). "
                    "Uso interno RR.HH."
                ),
            )
        except Exception:
            pass
        st.session_state.already_sent = True


# -----------------------------
# Navegación de preguntas SIN doble click
# -----------------------------
def choose_answer(value_yes_or_no: int):
    q_idx = st.session_state.current_q
    st.session_state.answers[q_idx] = value_yes_or_no

    # ¿última pregunta?
    if q_idx < TOTAL_QUESTIONS - 1:
        st.session_state.current_q += 1
        # Forzamos rerun suave al final del script
        st.session_state._need_rerun = True
    else:
        finalize_and_send()
        st.session_state.stage = "done"
        st.session_state._need_rerun = True


# -----------------------------
# Vistas
# -----------------------------
def view_select_job():
    st.markdown("### Evaluación EPQR-A Operativa")
    st.write("Seleccione el cargo a evaluar:")

    cols = st.columns(2)
    for idx, job_key in enumerate(JOB_PROFILES.keys()):
        col = cols[idx % 2]
        if col.button(JOB_PROFILES[job_key]["title"], key=f"job_{job_key}", use_container_width=True):
            st.session_state.selected_job = job_key
            st.session_state.stage = "info"
            st.session_state._need_rerun = True

def view_info_form():
    cargo_titulo = JOB_PROFILES[st.session_state.selected_job]["title"]
    st.markdown(f"#### Datos del candidato\n**Cargo evaluado:** {cargo_titulo}")
    st.info("Esta información se usará para generar el informe PDF interno y enviarlo al correo del evaluador.")
    st.session_state.candidate_name = st.text_input(
        "Nombre del candidato",
        value=st.session_state.candidate_name,
        placeholder="Nombre completo"
    )
    st.session_state.evaluator_email = st.text_input(
        "Correo del evaluador (RR.HH. / Supervisor)",
        value=st.session_state.evaluator_email,
        placeholder="nombre@empresa.com"
    )

    ok = (
        len(st.session_state.candidate_name.strip()) > 0 and
        len(st.session_state.evaluator_email.strip()) > 0
    )

    if st.button("Comenzar test", type="primary", disabled=not ok, use_container_width=True):
        st.session_state.current_q = 0
        st.session_state.answers = {i: None for i in range(TOTAL_QUESTIONS)}
        st.session_state.already_sent = False
        st.session_state.stage = "test"
        st.session_state._need_rerun = True

def view_test():
    q_idx = st.session_state.current_q
    q = QUESTIONS[q_idx]
    progreso = (q_idx+1)/TOTAL_QUESTIONS

    # Header tarjeta arriba
    with st.container():
        st.markdown(
            f"""
            <div style="
                background:linear-gradient(to right,#1e40af,#4338ca);
                color:white;
                border-radius:0.75rem 0.75rem 0 0;
                padding:1rem 1.25rem;">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;">
                    <div style="font-size:1rem;font-weight:600;">
                        Test EPQR-A Operativo (40 ítems)
                    </div>
                    <div style="background:rgba(255,255,255,0.2);
                                border-radius:999px;
                                padding:0.25rem 0.75rem;
                                font-size:.8rem;">
                        Pregunta {q_idx+1} de {TOTAL_QUESTIONS} · {int(round(progreso*100))}%
                    </div>
                </div>
                <div style="font-size:.7rem;color:#c7d2fe;margin-top:.25rem;">
                    Cargo: {JOB_PROFILES[st.session_state.selected_job]["title"]}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Barra de progreso nativa streamlit (visualmente más estable)
    st.progress(progreso)

    # Bloque de pregunta en tarjeta blanca
    with st.container():
        st.markdown(
            f"""
            <div style="
                background:#ffffff;
                border:1px solid #e2e8f0;
                border-radius:0.75rem;
                padding:1.5rem;
                box-shadow:0 12px 24px rgba(0,0,0,0.05);
                margin-top:1rem;">
                <p style="
                    font-size:1.05rem;
                    color:#1e293b;
                    line-height:1.4;
                    margin:0 0 1.5rem 0;">
                    {q["text"]}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Botones Sí / No en dos columnas grandes
    col_yes, col_no = st.columns(2)
    with col_yes:
        st.button(
            "Sí",
            key=f"yes_{q_idx}",
            type="primary",
            use_container_width=True,
            on_click=choose_answer,
            args=(1,)
        )
    with col_no:
        st.button(
            "No",
            key=f"no_{q_idx}",
            use_container_width=True,
            on_click=choose_answer,
            args=(0,)
        )

    # Mensaje legal abajo
    st.markdown(
        """
        <div style="
            background:#f8fafc;
            border:1px solid #e2e8f0;
            border-radius:0.5rem;
            padding:0.75rem 1rem;
            font-size:.75rem;
            color:#475569;
            margin-top:1rem;">
            <b>Confidencialidad:</b> Uso interno RR.HH. / Selección operativa.
            El candidato no recibe copia directa del informe.
        </div>
        """,
        unsafe_allow_html=True
    )

def view_done():
    st.markdown(
        """
        <div style="
            background:linear-gradient(to bottom right,#ecfdf5,#d1fae5);
            padding:2rem;
            border-radius:1rem;
            box-shadow:0 24px 48px rgba(0,0,0,0.08);
            text-align:center;">
            <div style="
                width:64px;
                height:64px;
                border-radius:999px;
                background:#10b981;
                color:white;
                display:flex;
                align-items:center;
                justify-content:center;
                font-size:2rem;
                font-weight:700;
                margin:0 auto 1rem auto;">
                ✔
            </div>
            <h2 style="
                font-size:1.3rem;
                font-weight:700;
                color:#065f46;
                margin:0 0 .5rem 0;">
                Evaluación finalizada
            </h2>
            <p style="color:#065f46;margin:0;">
                Los resultados han sido procesados y enviados al correo del evaluador.
            </p>
            <p style="color:#065f46;margin:.5rem 0 0 0;font-size:.8rem;">
                Documento interno. No clínico.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

# -----------------------------
# Flujo finalización y envío
# -----------------------------
def end_test_and_send_if_needed():
    # Llamado al terminar la última pregunta
    scores = compute_scores(st.session_state.answers)
    raw_scores  = scores["raw"]
    norm_scores = scores["norm"]

    E  = norm_scores["E"]
    EE = norm_scores["EE"]
    DC = norm_scores["DC"]
    C_ = norm_scores["C"]
    M  = norm_scores["M"]

    table_desc = build_short_desc(E,EE,DC,C_,M)
    fortalezas, monitoreo = build_strengths_risks(E,EE,DC,C_,M)
    compromiso_line = build_commitment_line(M)
    cierre_match    = match_job_profile(
        st.session_state.selected_job,
        E,EE,DC,C_,M
    )
    cierre_text = compromiso_line + " " + cierre_match

    nota_text = (
        "Este informe se basa en la auto-respuesta declarada por la persona evaluada "
        "en el Cuestionario EPQR-A. Los resultados describen tendencias y preferencias "
        "conductuales observadas en el momento de la evaluación. No constituyen un "
        "diagnóstico clínico ni, por sí solos, una determinación absoluta de idoneidad "
        "laboral. Se recomienda complementar esta información con entrevista estructurada, "
        "verificación de experiencia y evaluación técnica del cargo."
    )

    now_txt = datetime.now().strftime("%d/%m/%Y %H:%M")
    cargo_name = JOB_PROFILES[st.session_state.selected_job]["title"]

    pdf_bytes = generate_pdf(
        candidate_name   = st.session_state.candidate_name,
        cargo_name       = cargo_name,
        fecha_eval       = now_txt,
        evaluator_email  = st.session_state.evaluator_email,
        norm_scores      = norm_scores,
        raw_scores       = raw_scores,
        fortalezas       = fortalezas,
        monitoreo        = monitoreo,
        table_desc       = table_desc,
        cierre_text      = cierre_text,
        nota_text        = nota_text
    )

    if not st.session_state.already_sent:
        try:
            send_email_with_pdf(
                to_email   = st.session_state.evaluator_email,
                pdf_bytes  = pdf_bytes,
                filename   = "Informe_EPQR_Operativo.pdf",
                subject    = "Informe EPQR-A Operativo (Selección)",
                body_text  = (
                    "Adjunto informe interno EPQR-A Operativo "
                    f"({st.session_state.candidate_name} / {cargo_name}). "
                    "Uso interno RR.HH."
                ),
            )
        except Exception:
            pass
        st.session_state.already_sent = True


# -----------------------------
# Render principal según stage
# -----------------------------
if st.session_state.stage == "select_job":
    view_select_job()

elif st.session_state.stage == "info":
    view_info_form()

elif st.session_state.stage == "test":
    # si ya contestó la última antes de render
    if st.session_state.current_q >= TOTAL_QUESTIONS:
        # forzamos fin
        st.session_state.stage = "done"
        st.session_state._need_rerun = True
    view_test()

elif st.session_state.stage == "done":
    # aseguro que el pdf ya está enviado/generado
    end_test_and_send_if_needed()
    view_done()

# -----------------------------
# Rerun único al final si se marcó la bandera
# Esto elimina la necesidad de doble click
# -----------------------------
if st.session_state._need_rerun:
    st.session_state._need_rerun = False
    st.rerun()
