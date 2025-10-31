# ============================================================ f
# EPQR-A Operativo (5 dimensiones) · 40 ítems
# Visual "card blanca + barra progreso" · Sin doble click
# PDF ordenado (5 barras + cajas) · Envío automático por correo
# Pantalla final: sólo mensaje "Evaluación finalizada"
# Requiere: pip install reportlab
# ============================================================

import streamlit as st
from datetime import datetime
from io import BytesIO
import smtplib
from email.message import EmailMessage

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors

# ---------- CONFIG STREAMLIT ----------
st.set_page_config(
    page_title="EPQR-A Operativo",
    page_icon="🧪",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ---------- CREDENCIALES DE CORREO ----------
FROM_ADDR = "jo.tajtaj@gmail.com"
APP_PASS  = "nlkt kujl ebdg cyts"

# ---------- PREGUNTAS (40 total, 5 dimensiones x 8 ítems) ----------
QUESTIONS = [
    # E — Extraversión / iniciativa social
    {"text": "Me siento cómodo/a hablando con personas que recién conozco.", "cat": "E"},
    {"text": "Puedo tomar la palabra frente a un grupo sin mucho problema.", "cat": "E"},
    {"text": "Cuando hay que coordinar al equipo, suelo ofrecerme a explicar qué hacer.", "cat": "E"},
    {"text": "Me gusta interactuar con otras personas durante la jornada.", "cat": "E"},
    {"text": "Prefiero estar en silencio y que otros hablen por mí.", "cat": "E_rev"},
    {"text": "Evito situaciones donde deba hablar en voz alta frente a varios.", "cat": "E_rev"},
    {"text": "Me ha resultado fácil motivar a otros cuando se están quedando atrás.", "cat": "E"},
    {"text": "Disfruto estar rodeado/a de personas en el turno.", "cat": "E"},

    # N — Neuroticismo crudo (luego se invierte a EE = Estabilidad Emocional)
    {"text": "Bajo presión me pongo muy ansioso/a.", "cat": "N"},
    {"text": "Me cuesta mantener la calma cuando todo se acelera.", "cat": "N"},
    {"text": "Cuando algo sale mal, le doy vueltas mucho rato.", "cat": "N"},
    {"text": "Me altero con facilidad frente a conflictos en el trabajo.", "cat": "N"},
    {"text": "Puedo seguir funcionando aun con estrés encima.", "cat": "N_rev"},
    {"text": "Controlo mis reacciones incluso cuando hay urgencia.", "cat": "N_rev"},
    {"text": "Me desespero rápido si hay muchas órdenes distintas.", "cat": "N"},
    {"text": "Cuando las cosas se enredan, logro mantenerme estable.", "cat": "N_rev"},

    # DC — Dureza Conductual / Estilo Directo
    {"text": "Si alguien no hace su parte, le digo directamente que se ponga al día.", "cat": "P_func"},
    {"text": "Es más importante que el trabajo salga bien que quedar bien con todos.", "cat": "P_func"},
    {"text": "Me da lo mismo si mis palabras suenan duras mientras el turno se cumpla.", "cat": "P"},
    {"text": "Cuando hay una instrucción clara, espero que se cumpla sin discusión.", "cat": "P_func"},
    {"text": "He pasado por encima de otros para salir beneficiado/a.", "cat": "P"},
    {"text": "Puedo mantenerme firme incluso si otros se enojan un poco.", "cat": "P_func"},
    {"text": "Prefiero mis propias reglas aunque choquen con las normas.", "cat": "P"},
    {"text": "Marco prioridades cuando hay muchas tareas al mismo tiempo.", "cat": "P_func"},

    # C — Consistencia / Autopresentación
    {"text": "Trato de dar siempre buena impresión a la jefatura.", "cat": "S_ok"},
    {"text": "He mentido para evitar asumir un error propio.", "cat": "S"},
    {"text": "Sigo los procedimientos tal como están definidos.", "cat": "S_ok"},
    {"text": "He culpado a otra persona sabiendo que el error fue mío.", "cat": "S"},
    {"text": "Me importa que me consideren confiable.", "cat": "S_ok"},
    {"text": "He tomado algo que no era mío en el trabajo.", "cat": "S"},
    {"text": "Respeto normas de seguridad aunque nadie mire.", "cat": "S_ok"},
    {"text": "A veces hago trampa si sé que no me pillarán.", "cat": "S"},

    # M — Motivación / Compromiso con el Puesto
    {"text": "Si el turno está difícil, igual termino la tarea haciendo un esfuerzo extra.", "cat": "M_commit"},
    {"text": "Este trabajo es sólo temporal hasta encontrar algo mejor luego.", "cat": "M_leaver"},
    {"text": "Prefiero quedarme y hablar los problemas antes que irme al primer conflicto.", "cat": "M_commit"},
    {"text": "Si las reglas no me gustan en la primera semana, prefiero renunciar rápido.", "cat": "M_leaver"},
    {"text": "Quiero que me vean como alguien estable y que cumple.", "cat": "M_commit"},
    {"text": "Si siento que me exigen mucho, me voy sin pensarlo demasiado.", "cat": "M_leaver"},
    {"text": "Quiero que me consideren confiable a largo plazo.", "cat": "M_commit"},
    {"text": "Me cambiaría rápido de puesto si algo no me acomoda de inmediato.", "cat": "M_leaver"},
]
TOTAL_QUESTIONS = len(QUESTIONS)  # 40

# ---------- PERFILES DE CARGO (rangos esperados por dimensión en escala 0-6) ----------
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

# ---------- ESTADO GLOBAL STREAMLIT ----------
if "stage" not in st.session_state:
    st.session_state.stage = "select_job"  # select_job → info → test → done

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


# ---------- SCORING ----------
def _norm_to_six(raw_value):
    # normaliza puntaje bruto 0..8 a escala 0..6
    return (raw_value / 8.0) * 6.0

def compute_scores(ans_dict):
    E_raw = 0
    N_raw = 0
    P_func_raw = 0
    P_inv_raw = 0
    S_ok_raw = 0
    S_inv_raw = 0
    M_commit_raw = 0
    M_leaver_raw = 0

    for idx, q in enumerate(QUESTIONS):
        a = ans_dict.get(idx)
        if a is None:
            continue
        cat = q["cat"]

        # Extraversión
        if cat == "E" and a == 1:
            E_raw += 1
        elif cat == "E_rev" and a == 0:
            E_raw += 1

        # Neuroticismo (para luego invertir)
        if cat == "N" and a == 1:
            N_raw += 1
        elif cat == "N_rev" and a == 0:
            N_raw += 1

        # Dureza Conductual / Estilo Directo
        if cat == "P_func" and a == 1:
            P_func_raw += 1
        elif cat == "P" and a == 0:
            P_inv_raw += 1

        # Consistencia / Autopresentación
        if cat == "S_ok" and a == 1:
            S_ok_raw += 1
        elif cat == "S" and a == 0:
            S_inv_raw += 1

        # Motivación / Compromiso
        if cat == "M_commit" and a == 1:
            M_commit_raw += 1
        elif cat == "M_leaver" and a == 0:
            M_leaver_raw += 1

    DC_raw = P_func_raw + P_inv_raw
    C_raw  = S_ok_raw + S_inv_raw
    M_raw  = M_commit_raw + M_leaver_raw

    # Estabilidad Emocional EE = 8 - Neuroticismo
    EE_raw = 8 - N_raw
    if EE_raw < 0: EE_raw = 0
    if EE_raw > 8: EE_raw = 8

    raw_scores = {
        "E":  E_raw,
        "EE": EE_raw,
        "DC": DC_raw,
        "C":  C_raw,
        "M":  M_raw,
    }
    norm_scores = {k: _norm_to_six(v) for k, v in raw_scores.items()}

    return {"raw": raw_scores, "norm": norm_scores}


# ---- NUEVA FUNCIÓN: NIVEL usando puntaje bruto (0-8)
def qualitative_level_raw(raw_score):
    # 0-2 bajo, 3-5 medio, 6-8 alto
    if raw_score >= 6:
        return "Alto"
    elif raw_score >= 3:
        return "Medio"
    else:
        return "Bajo"


def build_short_desc(E_norm, EE_norm, DC_norm, C_norm, M_norm):
    out = {}
    out["E"]  = (
        "Tendencia a interactuar y coordinar con otros cuando la tarea lo requiere."
        if E_norm > 2.0 else
        "Estilo más bien reservado, baja exposición pública."
    )
    out["EE"] = (
        "Manejo estable frente a presión y cambio."
        if EE_norm > 2.0 else
        "Puede requerir apoyo en escenarios de alta urgencia."
    )
    out["DC"] = (
        "Capacidad para marcar prioridades operativas y sostener criterios de cumplimiento."
        if DC_norm > 2.0 else
        "Prefiere evitar confrontación directa; espera orden sin choque."
    )
    out["C"]  = (
        "Orientación a normas, búsqueda de imagen responsable y cumplimiento declarado."
        if C_norm > 2.0 else
        "Puede tensionar estándares si prima su propio criterio sobre lo formal."
    )
    out["M"]  = (
        "Disposición declarada a cumplir y mantenerse en el puesto si las condiciones son claras."
        if M_norm > 2.0 else
        "Declara baja intención de permanencia si la adaptación inicial no es cómoda."
    )
    return out


def build_strengths_risks(E_norm, EE_norm, DC_norm, C_norm, M_norm):
    fortalezas = []
    monitoreo = []

    # Extraversión
    if E_norm >= 4.5:
        fortalezas.append("Comunicación activa y coordinación con el equipo.")
    elif E_norm <= 2.0:
        monitoreo.append("Puede requerir instrucciones claras más que exposición frente a grupos.")

    # Estabilidad Emocional
    if EE_norm >= 4.5:
        fortalezas.append("Manejo estable de presión y foco en la tarea.")
    elif EE_norm <= 2.0:
        monitoreo.append("Podría necesitar apoyo directo en escenarios de alta urgencia.")

    # Dureza Conductual
    if DC_norm >= 4.5:
        fortalezas.append("Capacidad para marcar prioridades operativas bajo presión.")
        monitoreo.append("Su comunicación directa podría percibirse exigente; acordar estándares claros.")
    elif DC_norm <= 2.0:
        monitoreo.append("Tiende a evitar confrontación; riesgo de omitir incumplimientos de otros.")

    # Consistencia
    if C_norm >= 4.5:
        fortalezas.append("Alta adhesión declarada a normas y procedimientos.")
    elif C_norm <= 2.0:
        monitoreo.append("Puede tensionar estándares si prioriza su propio criterio sobre el protocolo.")

    # Motivación / Permanencia
    if M_norm >= 4.5:
        fortalezas.append("Declara compromiso sostenido y disposición a permanecer en el puesto.")
    elif M_norm <= 2.0:
        monitoreo.append("Existe riesgo de rotación temprana si la adaptación inicial no calza.")

    # fallback para no dejar cajas vacías
    if not fortalezas:
        fortalezas.append("Mantiene un estilo de trabajo funcional al rol evaluado.")
    if not monitoreo:
        monitoreo.append("No se observan alertas conductuales críticas declaradas en esta medición inicial.")

    return fortalezas[:4], monitoreo[:4]


def build_commitment_line(M_raw):
    # ahora usamos puntaje bruto M_raw (0-8)
    if M_raw >= 6:
        return "Compromiso declarado: alta intención de permanencia y continuidad en el rol."
    elif M_raw >= 3:
        return "Compromiso declarado: se mantendría en el cargo si percibe trato justo y claridad operativa."
    else:
        return "Compromiso declarado: riesgo de salida temprana si la adaptación inicial no es satisfactoria."


def cargo_fit_text(job_key, E_norm, EE_norm, DC_norm, C_norm, M_norm):
    """
    Evalúa ajuste al cargo de forma más flexible.
    En lugar de exigir que TODAS las dimensiones estén dentro del rango,
    consideramos 'consistente' si el candidato calza en al menos 3 de 5 dimensiones.
    Eso evita que siempre salga NO SE CONSIDERA CONSISTENTE.
    """

    req = JOB_PROFILES[job_key]["req"]  # rangos esperados por dimensión
    got = {
        "E":  E_norm,
        "EE": EE_norm,
        "DC": DC_norm,
        "C":  C_norm,
        "M":  M_norm,
    }

    cargo_name = JOB_PROFILES[job_key]["title"]

    # contamos cuántas dimensiones quedan dentro del rango definido
    matches = 0
    total_dims = 0

    for dim, (mn, mx) in req.items():
        total_dims += 1
        val = got[dim]
        if mn <= val <= mx:
            matches += 1

    # regla de decisión:
    # si cumple al menos 3 de las 5 dimensiones (60%+), se considera consistente
    if matches >= 3:
        return (
            f"Ajuste al cargo: El perfil evaluado se considera "
            f"GLOBALMENTE CONSISTENTE con las exigencias habituales "
            f"del cargo {cargo_name}."
        )
    else:
        return (
            f"Ajuste al cargo: El perfil evaluado NO SE CONSIDERA "
            f"CONSISTENTE con las exigencias habituales del cargo "
            f"{cargo_name}."
        )



# ---------- TEXTO / WRAP HELPERS PARA PDF ----------
def _wrap(c, text, width, font="Helvetica", size=8):
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        test = (cur + " " + w).strip()
        if c.stringWidth(test, font, size) <= width:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def _draw_par(c, text, x, y, width, font="Helvetica", size=8, leading=11,
              color=colors.black, max_lines=None):
    c.setFont(font, size)
    c.setFillColor(color)
    lines = _wrap(c, text, width, font, size)
    if max_lines:
        lines = lines[:max_lines]
    for ln in lines:
        c.drawString(x, y, ln)
        y -= leading
    return y


def draw_table_dimensiones_fullwidth(c, x, y_top, w, rows):
    """
    Tabla "Detalle por dimensión" a ancho completo.
    rows = [
      { "dim":..., "puntaje":..., "nivel":..., "desc":... },
      ...
    ]
    Esta versión:
    - Usa puntaje bruto (X/8)
    - Nivel viene de qualitative_level_raw()
    """

    header_h   = 24
    row_h_base = 40
    pad_x      = 8
    leading    = 10
    font_hdr   = "Helvetica-Bold"
    font_txt_b = "Helvetica-Bold"
    font_txt   = "Helvetica"
    size_hdr   = 9
    size_cell  = 8

    col_dim_x   = x + pad_x
    col_punt_x  = x + 200
    col_nivel_x = x + 260
    col_desc_x  = x + 320
    table_right = x + w

    total_h = header_h
    wrapped_rows = []

    for r in rows:
        dim_lines = _wrap(
            c,
            r["dim"],
            col_punt_x - col_dim_x - 10,
            font_txt_b,
            size_cell
        )
        desc_lines = _wrap(
            c,
            r["desc"],
            table_right - col_desc_x - pad_x,
            font_txt,
            size_cell
        )

        lines_needed = max(len(dim_lines), len(desc_lines), 1)
        row_h = max(row_h_base, lines_needed * leading + 14)

        wrapped_rows.append({
            "dim_lines": dim_lines,
            "puntaje":   r["puntaje"],
            "nivel":     r["nivel"],
            "desc_lines":desc_lines,
            "row_h":     row_h
        })
        total_h += row_h

    # caja externa
    c.setStrokeColor(colors.lightgrey)
    c.setFillColor(colors.white)
    c.rect(x, y_top-total_h, w, total_h, stroke=1, fill=1)

    # título
    c.setFont(font_hdr, size_hdr)
    c.setFillColor(colors.black)
    c.drawString(x+pad_x, y_top-14, "Detalle por dimensión")

    # línea separadora título
    header_y_base = y_top - header_h
    c.setStrokeColor(colors.lightgrey)
    c.line(x, header_y_base, x+w, header_y_base)

    # encabezados columnas
    c.setFont(font_txt_b, size_cell)
    c.setFillColor(colors.black)
    c.drawString(col_dim_x,   header_y_base+leading-2, "Dimensión")
    c.drawString(col_punt_x,  header_y_base+leading-2, "Puntaje")
    c.drawString(col_nivel_x, header_y_base+leading-2, "Nivel")
    c.drawString(col_desc_x,  header_y_base+leading-2, "Descripción breve")

    # línea separadora encabezados
    c.line(x, header_y_base-4, x+w, header_y_base-4)

    # filas
    cursor_y = header_y_base-8
    for row in wrapped_rows:
        row_top_y    = cursor_y
        row_bottom_y = cursor_y - row["row_h"]

        # línea separadora fila
        c.setStrokeColor(colors.lightgrey)
        c.line(x, row_bottom_y, x+w, row_bottom_y)

        # Dimensión
        c.setFont(font_txt_b, size_cell)
        text_y = row_top_y - 12
        for dl in row["dim_lines"]:
            c.drawString(col_dim_x, text_y, dl)
            text_y -= leading

        # Puntaje (bruto X/8)
        c.setFont(font_txt, size_cell)
        c.drawString(col_punt_x, row_top_y - 12, row["puntaje"])

        # Nivel cualitativo (Bajo/Medio/Alto)
        c.drawString(col_nivel_x, row_top_y - 12, row["nivel"])

        # Descripción breve envuelta
        c.setFont(font_txt, size_cell)
        desc_y = row_top_y - 12
        for dl2 in row["desc_lines"]:
            c.drawString(col_desc_x, desc_y, dl2)
            desc_y -= leading

        cursor_y = row_bottom_y

    return y_top - total_h - 16


def draw_resumen_box_fullwidth(c, x, y_top, w, fortalezas, monitoreo):
    """
    Caja "Resumen conductual observado" ancho completo.
    Siempre muestra fortalezas y monitoreo (con fallback).
    """

    pad_x = 8
    pad_top = 12
    pad_bottom = 12
    line_height = 10
    font_tit  = "Helvetica-Bold"
    font_body = "Helvetica"
    size_tit  = 8
    size_txt  = 7

    # armamos contenido
    tmp_lines = []
    tmp_lines.append(("Resumen conductual observado", True))
    tmp_lines.append(("Fortalezas potenciales:", True))
    for f in fortalezas:
        tmp_lines.append(("• " + f, False))
    tmp_lines.append(("Aspectos a monitorear / apoyo sugerido:", True))
    for m in monitoreo:
        tmp_lines.append(("• " + m, False))

    # medir altura
    total_text_height = 0
    wrapped_content = []
    usable_w = w - 2*pad_x
    for text, is_header in tmp_lines:
        fnt = font_tit if is_header else font_body
        sz  = size_tit if is_header else size_txt
        wrapped = _wrap(c, text, usable_w, fnt, sz)
        wrapped_content.append((wrapped, fnt, sz))
        total_text_height += len(wrapped)*line_height + (4 if is_header else 0)

    box_h = pad_top + total_text_height + pad_bottom

    # caja
    c.setStrokeColor(colors.lightgrey)
    c.setFillColor(colors.white)
    c.rect(x, y_top - box_h, w, box_h, stroke=1, fill=1)

    # texto
    yy = y_top - pad_top
    for wrapped, fnt, sz in wrapped_content:
        c.setFont(fnt, sz)
        c.setFillColor(colors.black)
        for line in wrapped:
            c.drawString(x+pad_x, yy, line)
            yy -= line_height
        yy -= 2

    return y_top - box_h - 16


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
    W, H = A4  # retrato
    c = canvas.Canvas(buf, pagesize=A4)

    margin_left = 36
    margin_right = 36

    # ---------- HEADER SUPERIOR ----------
    c.setFont("Helvetica-Bold",10)
    c.setFillColor(colors.black)
    c.drawString(margin_left, H-40, "EMPRESA / LOGO")
    c.setFont("Helvetica",7)
    c.drawString(margin_left, H-55, "Evaluación de personalidad ocupacional")

    c.setFont("Helvetica-Bold",11)
    c.drawRightString(W-margin_right, H-40, "Perfil EPQR-A · Selección Operativa")
    c.setFont("Helvetica",7)
    c.drawRightString(W-margin_right, H-55, "Uso interno RR.HH. / Procesos productivos")

    # ---------- GRAFICO DE BARRAS IZQUIERDA ----------
    chart_x = margin_left
    chart_y_bottom = H-260
    chart_w = 250
    chart_h = 120

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
        val_norm = norm_scores[key]  # 0..6
        bx = chart_x + gap + i*(bar_w+gap)
        bh = (val_norm/6.0)*chart_h
        by = chart_y_bottom

        c.setStrokeColor(colors.black)
        c.setFillColor(bar_colors[i])
        c.rect(bx, by, bar_w, bh, stroke=1, fill=1)

        tops.append((bx+bar_w/2.0, by+bh))

        # nivel calculado con bruto
        lvl_txt = qualitative_level_raw(raw_scores[key])

        c.setFont("Helvetica-Bold",7)
        c.setFillColor(colors.black)
        c.drawCentredString(bx+bar_w/2.0, chart_y_bottom-14, label)

        c.setFont("Helvetica",6)
        c.drawCentredString(
            bx+bar_w/2.0,
            chart_y_bottom-26,
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
        c.circle(px,py,2.0,stroke=0,fill=1)

    c.setFont("Helvetica-Bold",8)
    c.setFillColor(colors.black)
    c.drawString(chart_x, chart_y_bottom+chart_h+12, "Perfil conductual (0–6)")

    # ---------- CAJAS DERECHA (DATOS + GUÍA) ----------
    box_x = margin_left + chart_w + 30
    box_w = W - margin_right - box_x

    # datos candidato
    box_y_top = H-140
    box_h = 70
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

    # guía
    guide_y_top = H-230
    guide_h = 75
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
        "EE = Estabilidad Emocional (manejo presión)",
        "DC = Dureza Conductual / Estilo directo",
        "C  = Consistencia / Autopresentación",
        "M  = Motivación / Compromiso con el Puesto",
    ]
    for gl in lines_dim:
        c.drawString(box_x+8, gy, gl)
        gy -= 10

    # ---------- TABLA DETALLE DIMENSIONES (ANCHO COMPLETO) ----------
    dims_display = [
        ("E",  "Extraversión"),
        ("EE", "Estabilidad Emocional"),
        ("DC", "Dureza Conductual / Estilo Directo"),
        ("C",  "Consistencia / Autopresentación"),
        ("M",  "Motivación / Compromiso con el Puesto"),
    ]

    table_rows = []
    for key,label in dims_display:
        raw_v  = raw_scores[key]            # bruto 0..8
        lvl_v  = qualitative_level_raw(raw_v)
        desc_v = table_desc[key]            # breve
        table_rows.append({
            "dim": label,
            "puntaje": f"{raw_v}/8",
            "nivel": lvl_v,
            "desc": desc_v,
        })

    table_x = margin_left
    table_y_top = H-360
    table_w = W - margin_right - margin_left

    after_table_y = draw_table_dimensiones_fullwidth(
        c,
        table_x,
        table_y_top,
        table_w,
        table_rows
    )

    # ---------- RESUMEN CONDUCTUAL OBSERVADO (ANCHO COMPLETO) ----------
    after_resumen_y = draw_resumen_box_fullwidth(
        c,
        margin_left,
        after_table_y,
        table_w,
        fortalezas,
        monitoreo
    )

    # ---------- BLOQUE FINAL: COMPROMISO / AJUSTE / NOTA ----------
    concl_x = margin_left
    concl_y_top = after_resumen_y
    concl_w = W - margin_right - margin_left

    pad_x = 8
    pad_top = 12
    pad_bottom = 12
    line_height = 10

    final_lines = [
        ("Compromiso / Permanencia", "Helvetica-Bold", 8, colors.black, compromiso_text),
        ("Ajuste al cargo evaluado", "Helvetica-Bold", 8, colors.black, ajuste_text),
        ("Nota metodológica", "Helvetica-Bold", 8, colors.black, nota_text),
    ]

    total_h_content = 0
    wrapped_blocks = []
    usable_w = concl_w - 2*pad_x

    for (section_title, fnt_t, sz_t, col_t, body_txt) in final_lines:
        title_wrapped = _wrap(c, section_title, usable_w, fnt_t, sz_t)
        body_wrapped  = _wrap(c, body_txt, usable_w, "Helvetica", 7)

        block_height = len(title_wrapped)*line_height + 4 \
                     + len(body_wrapped)*line_height + 10
        total_h_content += block_height
        wrapped_blocks.append((title_wrapped, fnt_t, sz_t, col_t, body_wrapped))

    concl_h = pad_top + total_h_content + pad_bottom

    c.setStrokeColor(colors.lightgrey)
    c.setFillColor(colors.white)
    c.rect(concl_x, concl_y_top - concl_h, concl_w, concl_h, stroke=1, fill=1)

    yy = concl_y_top - pad_top
    for (title_wrapped, fnt_t, sz_t, col_t, body_wrapped) in wrapped_blocks:
        c.setFont(fnt_t, sz_t)
        c.setFillColor(col_t)
        for line in title_wrapped:
            c.drawString(concl_x+pad_x, yy, line)
            yy -= line_height
        yy -= 2
        c.setFont("Helvetica",7)
        c.setFillColor(colors.black)
        for line in body_wrapped:
            c.drawString(concl_x+pad_x, yy, line)
            yy -= line_height
        yy -= 8

    # footer
    c.setFont("Helvetica",6)
    c.setFillColor(colors.white)
    c.drawRightString(W-margin_right, 40,
        "Uso interno RR.HH. · EPQR-A Adaptado · No clínico"
    )

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()


# ---------- EMAIL ----------
def send_email_with_pdf(to_email, pdf_bytes, filename, subject, body_text):
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


# ---------- GENERAR Y ENVIAR INFORME ----------
def finalize_and_send():
    scores = compute_scores(st.session_state.answers)
    raw_scores  = scores["raw"]   # dict con E,EE,DC,C,M en 0..8
    norm_scores = scores["norm"]  # dict con E,EE,DC,C,M en 0..6

    E_norm  = norm_scores["E"]
    EE_norm = norm_scores["EE"]
    DC_norm = norm_scores["DC"]
    C_norm  = norm_scores["C"]
    M_norm  = norm_scores["M"]

    M_raw = raw_scores["M"]

    # descripciones cortas para tabla
    table_desc = build_short_desc(E_norm, EE_norm, DC_norm, C_norm, M_norm)

    # fortalezas / monitoreo con fallback
    fortalezas, monitoreo = build_strengths_risks(E_norm, EE_norm, DC_norm, C_norm, M_norm)

    # compromiso con el puesto según puntaje bruto de motivación
    compromiso_text = build_commitment_line(M_raw)

    # ajuste cargo según rangos esperados por cargo
    ajuste_text = cargo_fit_text(
        st.session_state.selected_job,
        E_norm, EE_norm, DC_norm, C_norm, M_norm
    )

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
        compromiso_text  = compromiso_text,
        ajuste_text      = ajuste_text,
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


# ---------- CALLBACK RESPUESTA (sin doble click) ----------
def choose_answer(value_yes_or_no: int):
    q_idx = st.session_state.current_q
    st.session_state.answers[q_idx] = value_yes_or_no

    if q_idx < TOTAL_QUESTIONS - 1:
        st.session_state.current_q += 1
        st.session_state._need_rerun = True
    else:
        finalize_and_send()
        st.session_state.stage = "done"
        st.session_state._need_rerun = True


# ---------- VISTAS STREAMLIT ----------
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
    st.info("Estos datos se usan para generar el informe PDF interno y enviarlo automáticamente a RR.HH.")

    st.session_state.candidate_name = st.text_input(
        "Nombre del candidato",
        value=st.session_state.candidate_name,
        placeholder="Nombre completo"
    )
    st.session_state.evaluator_email = st.text_input(
        "Correo del evaluador (RR.HH. / Supervisor)",
        value=st.session_state.evaluator_email or FROM_ADDR,
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

    st.markdown(
        f"""
        <div style="
            background:linear-gradient(to right,#1e40af,#4338ca);
            color:white;
            border-radius:12px 12px 0 0;
            padding:16px 20px;
            display:flex;
            justify-content:space-between;
            align-items:center;
            flex-wrap:wrap;">
            <div style="font-weight:700;">
                Test EPQR-A Operativo (40 ítems)
            </div>
            <div style="
                background:rgba(255,255,255,0.25);
                padding:4px 10px;
                border-radius:999px;
                font-size:.85rem;">
                Pregunta {q_idx+1} de {TOTAL_QUESTIONS} · {int(round(progreso*100))}%
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.progress(progreso)

    st.markdown(
        f"""
        <div style="
            background:#ffffff;
            border:1px solid #e2e8f0;
            border-radius:12px;
            padding:24px;
            box-shadow:0 12px 24px rgba(0,0,0,0.06);
            margin-top:12px;">
            <p style="
                margin:0;
                font-size:1.05rem;
                color:#1e293b;
                line-height:1.45;">
                {q["text"]}
            </p>
        </div>
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

    st.markdown(
        """
        <div style="
            background:#f8fafc;
            border:1px solid #e2e8f0;
            border-radius:8px;
            padding:10px 14px;
            font-size:.8rem;
            color:#475569;
            margin-top:12px;">
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
            padding:28px;
            border-radius:14px;
            box-shadow:0 24px 48px rgba(0,0,0,0.08);
            text-align:center;">
            <div style="
                width:64px;
                height:64px;
                border-radius:999px;
                background:#10b981;
                color:#fff;
                display:flex;
                align-items:center;
                justify-content:center;
                font-size:2rem;
                font-weight:700;
                margin:0 auto 12px auto;">
                ✔
            </div>
            <div style="
                font-size:1.25rem;
                font-weight:800;
                color:#065f46;
                margin-bottom:6px;">
                Evaluación finalizada
            </div>
            <div style="color:#065f46;">
                Los resultados fueron procesados y enviados al correo del evaluador.
            </div>
            <div style="
                color:#065f46;
                font-size:.85rem;
                margin-top:6px;">
                Documento interno. No clínico.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ---------- FLUJO PRINCIPAL ----------
if st.session_state.stage == "select_job":
    view_select_job()

elif st.session_state.stage == "info":
    view_info_form()

elif st.session_state.stage == "test":
    if st.session_state.current_q >= TOTAL_QUESTIONS:
        st.session_state.stage = "done"
        st.session_state._need_rerun = True
    view_test()

elif st.session_state.stage == "done":
    finalize_and_send()
    view_done()

# ---------- RERUN CONTROLADO ----------
if st.session_state._need_rerun:
    st.session_state._need_rerun = False
    st.rerun()


