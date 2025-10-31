# ============================================================
# EPQR-A Operativo con 5 dimensiones (E, EE, DC, C, M)
# 40 ítems totales (8 por dimensión)
# Genera PDF ordenado en grillas / cajas
# Incluye gráfico de barras con las 5 dimensiones
# Envía PDF automáticamente al evaluador al finalizar
#
# Requisitos:
#   pip install streamlit reportlab
#
# NOTA IMPORTANTE sobre correo:
#   - Usa SMTP Gmail con App Password.
#   - Si el entorno no deja salir a internet o bloquea SMTP, el envío falla.
# ============================================================

import streamlit as st
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import smtplib
from email.message import EmailMessage
import math

# ------------------------------------------------------------
# CONFIG STREAMLIT
# ------------------------------------------------------------
st.set_page_config(
    page_title="Evaluación EPQR-A Operativa",
    page_icon="🧪",
    layout="centered",
    initial_sidebar_state="collapsed"
)


# ------------------------------------------------------------
# DEFINICIÓN DE LAS DIMENSIONES
#
# E  = Extraversión / iniciativa social
# N  = Neuroticismo crudo (lo invertimos y reportamos como EE = Estabilidad Emocional)
# P  = Dureza Conductual / estilo directo (Psicoticismo históricamente)
# S  = Consistencia / Autopresentación (Sinceridad socialmente deseable)
# M  = Motivación / Compromiso con el Puesto (retención / permanencia)
#
# Vamos a usar 8 preguntas por dimensión => 5*8 = 40 preguntas.
#
# IMPORTANTE:
# - Para E y N:
#       respuesta "Sí" = 1, "No" = 0 (sumamos directo)
# - Para P y S:
#       se invierte: "Sí" = 0, "No" = 1
#   Esto refleja que, para selección, el puntaje alto es estilo directo funcional
#   y/o consistencia normativa declarada.
#
# - Para M:
#   Tipo commit:     Sí=1 No=0  (compromiso, quedarse)
#   Tipo leaver:     Sí=0 No=1  (prefiere irse rápido => resta compromiso)
#
# El rango de cada escala será 0..8 (porque son 8 ítems por dimensión).
# Luego normalizamos a escala 0..6 para dibujar y comparar.
# ------------------------------------------------------------

QUESTIONS = [
    # === EXTRAVERSIÓN (E) === 8 ítems
    {"text": "Me siento cómodo/a hablando con personas que recién conozco.", "cat": "E"},
    {"text": "Puedo tomar la palabra frente a un grupo sin mucho problema.", "cat": "E"},
    {"text": "Cuando hay que coordinar al equipo, suelo ofrecerme a explicar qué hacer.", "cat": "E"},
    {"text": "Me gusta interactuar con otras personas durante la jornada.", "cat": "E"},
    {"text": "Prefiero estar en silencio y que otros hablen por mí.", "cat": "E_rev"},  # invertida en el sentido social
    {"text": "Evito situaciones donde deba hablar en voz alta frente a varios.", "cat": "E_rev"},
    {"text": "Me ha resultado fácil motivar a otros cuando se están quedando atrás.", "cat": "E"},
    {"text": "Disfruto estar rodeado/a de personas en el turno.", "cat": "E"},

    # === NEUROTICISMO crudo (N) => luego hacemos EE=Estabilidad Emocional=8 - N_raw === 8 ítems
    {"text": "Bajo presión me pongo muy ansioso/a.", "cat": "N"},
    {"text": "Me cuesta mantener la calma cuando todo se acelera.", "cat": "N"},
    {"text": "Cuando algo sale mal, me quedo dándole vueltas en la cabeza mucho rato.", "cat": "N"},
    {"text": "Me altero con facilidad frente a conflictos en el trabajo.", "cat": "N"},
    {"text": "Puedo seguir funcionando aun con estrés encima.", "cat": "N_rev"},  # rev: Sí = calma => menos neuroticismo
    {"text": "Siento que controlo mis reacciones incluso cuando hay urgencia.", "cat": "N_rev"},
    {"text": "Me desespero rápido si hay muchas órdenes distintas al mismo tiempo.", "cat": "N"},
    {"text": "Cuando las cosas se enredan, logro mantenerme estable.", "cat": "N_rev"},

    # === DUREZA CONDUCTUAL / ESTILO DIRECTO (P) === 8 ítems
    # Aquí queremos medir estilo directo / foco en tarea:
    # Para puntaje alto 'bueno operativo', interpretamos respuestas con inversión tipo EPQR.
    # cat 'P' => invertido (Sí=0, No=1) cuando refleja conducta riesgosa/egoísta
    # cat 'P_func' => directa/funcional (Sí=1, No=0) cuando refleja asertividad laboral aceptable
    {"text": "Si alguien no hace su parte, le digo directamente que se ponga al día.", "cat": "P_func"},
    {"text": "Para mí es más importante que el trabajo salga bien que quedar bien con todos.", "cat": "P_func"},
    {"text": "Me da lo mismo si mis palabras suenan duras mientras el turno se cumpla.", "cat": "P"},
    {"text": "Cuando hay una instrucción clara, espero que se cumpla sin discusión.", "cat": "P_func"},
    {"text": "He pasado por encima de otros para salir beneficiado/a.", "cat": "P"},
    {"text": "Puedo mantenerme firme incluso si otros se enojan un poco.", "cat": "P_func"},
    {"text": "Prefiero seguir mis propias reglas aunque choquen con las normas.", "cat": "P"},
    {"text": "Puedo marcar prioridades cuando hay muchas tareas al mismo tiempo.", "cat": "P_func"},

    # === CONSISTENCIA / AUTOPRESENTACIÓN (S) === 8 ítems
    # Aquí queremos medir 'cumplo norma / muestro imagen responsable'
    # cat 'S' => invertido EPQR clásico (Sí=0, No=1) en conductas poco éticas
    # cat 'S_ok' => Sí=1, No=0 en afirmaciones de cumplimiento/norma
    {"text": "Trato de dar siempre una buena impresión a la jefatura.", "cat": "S_ok"},
    {"text": "He mentido para evitar asumir un error propio.", "cat": "S"},
    {"text": "Me preocupo de seguir los procedimientos tal como están definidos.", "cat": "S_ok"},
    {"text": "He culpado a otra persona sabiendo que el error fue mío.", "cat": "S"},
    {"text": "Me importa que me consideren alguien confiable.", "cat": "S_ok"},
    {"text": "He tomado algo que no era mío en el trabajo.", "cat": "S"},
    {"text": "Respeto las normas de seguridad aunque nadie esté mirando.", "cat": "S_ok"},
    {"text": "A veces hago trampa si sé que no me van a pillar.", "cat": "S"},

    # === MOTIVACIÓN / COMPROMISO CON EL PUESTO (M) === 8 ítems
    # commit-style: Sí=1 No=0
    # leaver-style: Sí=0 No=1
    {"text": "Si el turno está difícil, igual termino la tarea aunque implique un poco más de esfuerzo.", "cat": "M_commit"},
    {"text": "Para mí este trabajo es sólo algo temporal hasta encontrar algo mejor luego.", "cat": "M_leaver"},
    {"text": "Prefiero quedarme y hablar los problemas antes que irme al primer conflicto.", "cat": "M_commit"},
    {"text": "Si las reglas del lugar no me gustan en la primera semana, prefiero renunciar rápido.", "cat": "M_leaver"},
    {"text": "Me importa que me vean como una persona estable y que cumple.", "cat": "M_commit"},
    {"text": "Si siento que me exigen mucho, me voy sin pensarlo demasiado.", "cat": "M_leaver"},
    {"text": "Quiero que me consideren alguien en quien se puede confiar a largo plazo.", "cat": "M_commit"},
    {"text": "Me cambiaría rápido de puesto si algo no me acomoda de inmediato.", "cat": "M_leaver"},
]

TOTAL_QUESTIONS = len(QUESTIONS)  # debe ser 40


# ------------------------------------------------------------
# PERFILES DE CARGO Y RANGOS ESPERADOS
#
# Puntajes se normalizan a escala 0..6 aprox para comparar.
# ------------------------------------------------------------
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


# ------------------------------------------------------------
# ESTADO STREAMLIT
# ------------------------------------------------------------
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
    st.session_state.answers = {i: None for i in range(TOTAL_QUESTIONS)}

if "already_sent" not in st.session_state:
    st.session_state.already_sent = False


# ------------------------------------------------------------
# FUNCIONES DE CÁLCULO DE PUNTAJE
# ------------------------------------------------------------

def _norm_to_six(raw, max_raw=8):
    # normaliza puntaje crudo 0..8 -> 0..6
    return (raw / max_raw) * 6.0


def compute_scores(answers_dict):
    """
    Calcula puntajes crudos (0..8) y normalizados (0..6) por cada dimensión:
    E, EE (6-N), DC (P), C (S), M
    """
    # crudos
    E_raw = 0
    N_raw = 0
    P_raw_func = 0
    P_raw_inv  = 0
    S_raw_ok   = 0
    S_raw_inv  = 0
    M_raw_commit = 0
    M_raw_leaver = 0

    # Recorremos las 40 preguntas
    for idx, q in enumerate(QUESTIONS):
        ans = answers_dict.get(idx)
        if ans is None:
            continue

        cat = q["cat"]

        # Extraversión:
        #   cat "E": Sí=1 No=0
        #   cat "E_rev": invertida (Sí=0 No=1) porque es actitud más retraída
        if cat == "E":
            if ans == 1:
                E_raw += 1
        elif cat == "E_rev":
            if ans == 0:
                E_raw += 1

        # Neuroticismo:
        #   "N": Sí=1 (ansioso), "N_rev": Sí=0 No=1 (calma)
        if cat == "N":
            if ans == 1:
                N_raw += 1
        elif cat == "N_rev":
            if ans == 0:
                N_raw += 1

        # Dureza Conductual / Estilo Directo (P):
        #   "P_func": Sí=1 No=0 (directo funcional)
        #   "P":      Sí=0 No=1 (conductas más duras/egoístas; invertimos)
        if cat == "P_func":
            if ans == 1:
                P_raw_func += 1
        elif cat == "P":
            if ans == 0:
                P_raw_inv += 1

        # Consistencia / Autopresentación (S):
        #   "S_ok": Sí=1 No=0 (cumplo norma)
        #   "S":    Sí=0 No=1 (conducta poco ética -> invertida)
        if cat == "S_ok":
            if ans == 1:
                S_raw_ok += 1
        elif cat == "S":
            if ans == 0:
                S_raw_inv += 1

        # Motivación / Compromiso (M):
        #   "M_commit": Sí=1 No=0
        #   "M_leaver": Sí=0 No=1 (si NO se iría de inmediato)
        if cat == "M_commit":
            if ans == 1:
                M_raw_commit += 1
        elif cat == "M_leaver":
            if ans == 0:
                M_raw_leaver += 1

    # combinar parciales
    P_raw = P_raw_func + P_raw_inv    # 0..8
    S_raw = S_raw_ok + S_raw_inv      # 0..8
    M_raw = M_raw_commit + M_raw_leaver

    # Estabilidad Emocional (EE) = 8 - N_raw (más alto = más estable)
    EE_raw = 8 - N_raw
    if EE_raw < 0:
        EE_raw = 0
    if EE_raw > 8:
        EE_raw = 8

    # normalizamos a 0..6
    E_norm  = _norm_to_six(E_raw)
    EE_norm = _norm_to_six(EE_raw)
    DC_norm = _norm_to_six(P_raw)
    C_norm  = _norm_to_six(S_raw)
    M_norm  = _norm_to_six(M_raw)

    return {
        "raw": {
            "E":  E_raw,   # 0..8
            "EE": EE_raw,  # 0..8
            "DC": P_raw,   # 0..8
            "C":  S_raw,   # 0..8
            "M":  M_raw,   # 0..8
        },
        "norm": {
            "E":  E_norm,   # 0..6
            "EE": EE_norm,  # 0..6
            "DC": DC_norm,  # 0..6
            "C":  C_norm,   # 0..6
            "M":  M_norm,   # 0..6
        }
    }


def qualitative_level(norm_score):
    # 0..6 → Bajo / Medio / Alto
    # <=2 -> Bajo | 2<..4.5 -> Medio | >4.5 -> Alto
    if norm_score > 4.5:
        return "Alto"
    elif norm_score > 2.0:
        return "Medio"
    else:
        return "Bajo"


def build_short_desc(E, EE, DC, C, M):
    """
    Texto corto por dimensión (una línea o dos máximo) para "tabla" en el PDF.
    Debe ser brevísimo para no desbordar.
    """
    desc = {}

    # E
    if E > 4.5:
        desc["E"] = "Alta iniciativa social; tiende a comunicarse y tomar visibilidad."
    elif E > 2.0:
        desc["E"] = "Interacción funcional; habla cuando la tarea lo requiere."
    else:
        desc["E"] = "Prefiere bajo nivel de exposición; estilo más reservado."

    # EE
    if EE > 4.5:
        desc["EE"] = "Tolera presión, se mantiene enfocado/a en la tarea en alta demanda."
    elif EE > 2.0:
        desc["EE"] = "Puede sostenerse con apoyo claro en escenarios tensos."
    else:
        desc["EE"] = "Puede requerir contención directa en urgencia/conflicto."

    # DC
    if DC > 4.5:
        desc["DC"] = "Estilo directo y firme en priorizar tareas bajo presión."
    elif DC > 2.0:
        desc["DC"] = "Capaz de marcar instrucciones y sostener criterios operativos."
    else:
        desc["DC"] = "Prefiere evitar confrontación abierta; busca orden sin choque."

    # C
    if C > 4.5:
        desc["C"] = "Alta orientación a cumplir normas y mostrarse confiable."
    elif C > 2.0:
        desc["C"] = "Cuida imagen responsable y apego a procedimientos."
    else:
        desc["C"] = "Puede priorizar criterio propio frente a reglas formales."

    # M
    if M > 4.5:
        desc["M"] = "Alta motivación declarada para permanecer y cumplir."
    elif M > 2.0:
        desc["M"] = "Compromiso condicionado: permanece si percibe trato justo y claridad."
    else:
        desc["M"] = "Riesgo de rotación temprana si el entorno no calza de inmediato."

    return desc


def build_strengths_risks(E, EE, DC, C, M):
    fortalezas = []
    monitoreo = []

    if E > 4.5:
        fortalezas.append("Disposición a comunicarse y coordinar tareas con otros.")
    elif E > 2.0:
        fortalezas.append("Puede interactuar de manera funcional en equipo cuando es necesario.")
    else:
        monitoreo.append("Puede requerir instrucciones claras en lugar de exposición pública.")

    if EE > 4.5:
        fortalezas.append("Manejo de presión estable; mantiene foco en la tarea.")
    elif EE <= 2.0:
        monitoreo.append("Podría necesitar contención directa en escenarios de alta urgencia.")

    if DC > 4.5:
        fortalezas.append("Capacidad de marcar prioridades operativas aun con presión.")
        monitoreo.append("Su comunicación directa puede percibirse como exigente; acordar estándares claros.")
    elif DC > 2.0:
        fortalezas.append("Puede sostener criterios de cumplimiento sin evitar la responsabilidad.")
    else:
        monitoreo.append("Tiende a evitar confrontaciones; podría dejar pasar incumplimientos de otros.")

    if C > 4.5:
        fortalezas.append("Se declara consistente con normas y procedimientos establecidos.")
    elif C <= 2.0:
        monitoreo.append("Puede tensionar estándares si prioriza su propio criterio sobre la norma.")

    if M > 4.5:
        fortalezas.append("Declara alta permanencia y compromiso con el puesto.")
    elif M <= 2.0:
        monitoreo.append("Manifiesta riesgo de rotación temprana si el entorno no calza rápido.")

    # límite máximo 3 de cada uno para que el PDF no se desborde visualmente
    return fortalezas[:3], monitoreo[:3]


def build_commitment_line(M):
    if M > 4.5:
        return "Declara intención de permanencia estable y continuidad en el rol."
    elif M > 2.0:
        return "Compromiso condicionado: se mantiene si percibe trato justo, reglas claras y coherencia."
    else:
        return "Existe riesgo de rotación temprana si la adaptación inicial no cumple sus expectativas."


def match_job_profile(job_key, E, EE, DC, C_, M):
    req = JOB_PROFILES[job_key]["req"]
    checks = {
        "E":  E,
        "EE": EE,
        "DC": DC,
        "C":  C_,
        "M":  M
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


# ------------------------------------------------------------
# GENERACIÓN DEL PDF (1 página A4, diseño en bloques)
# Bloques:
#   A) Encabezado empresa + Perfil EPQR-A
#   B) Gráfico barras 5 dimensiones
#   C) Caja datos candidato
#   D) Caja guía/leyenda + caja resumen fortalezas/monitoreo
#   E) Tabla tipo grilla Dimensión / Puntaje / Nivel / Descripción breve
#   F) Conclusión operativa + Nota metodológica
#
# Para evitar traslapes:
# - posicionamos cada bloque con coordenadas fijas en la página
# - usamos texto corto y envolvemos líneas
# ------------------------------------------------------------

def make_wrapped_lines(c, text, max_width, font_name="Helvetica", font_size=8):
    words = text.split()
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
    """
    norm_scores: dict {E,EE,DC,C,M} escala 0..6
    raw_scores:  dict {E,EE,DC,C,M} escala 0..8
    table_desc:  dict {E,EE,DC,C,M} texto corto
    """

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4  # aprox 595 x 842

    # Paleta de barras (5 barras)
    bar_colors = [
        colors.Color(0.20,0.40,0.80),  # E
        colors.Color(0.15,0.60,0.30),  # EE
        colors.Color(0.90,0.40,0.20),  # DC
        colors.Color(0.40,0.40,0.40),  # C
        colors.Color(0.25,0.50,0.60),  # M (azul verdoso)
    ]

    # ------------------------
    # A) Encabezado
    # ------------------------
    c.setFont("Helvetica-Bold", 10)
    c.drawString(30, H-30, "EMPRESA / LOGO")
    c.setFont("Helvetica", 7)
    c.drawString(30, H-42, "Evaluación de personalidad ocupacional")

    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(W-30, H-30, "Perfil EPQR-A · Selección Operativa")
    c.setFont("Helvetica", 7)
    c.drawRightString(W-30, H-42, "Uso interno RR.HH. / Procesos productivos")

    # ------------------------
    # B) Gráfico de barras con 5 dimensiones
    # ------------------------
    chart_x = 30
    chart_y_bottom = H-235
    chart_h = 120
    chart_w = 250
    # eje y / grid
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.line(chart_x, chart_y_bottom, chart_x, chart_y_bottom+chart_h)

    # grid horizontal 0..6
    for lvl in range(0,7):
        yv = chart_y_bottom + (lvl/6.0)*chart_h
        c.setFont("Helvetica",6)
        c.setFillColor(colors.black)
        c.drawString(chart_x-15, yv-2, str(lvl))
        c.setStrokeColor(colors.lightgrey)
        c.line(chart_x, yv, chart_x+chart_w, yv)

    # dibujar barras
    dims_order = [("E","E"),("EE","EE"),("DC","DC"),("C","C"),("M","M")]
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

        # etiqueta debajo
        c.setFont("Helvetica-Bold",7)
        c.setFillColor(colors.black)
        c.drawCentredString(bx+bar_w/2.0, chart_y_bottom-14, label)

        # puntaje y nivel corto
        lvl_txt = qualitative_level(val_norm)
        c.setFont("Helvetica",6)
        c.drawCentredString(
            bx+bar_w/2.0,
            chart_y_bottom-24,
            f"{raw_scores[key]}/8  {val_norm:.1f}/6  {lvl_txt}"
        )

    # línea negra conectando puntos
    c.setStrokeColor(colors.black)
    c.setLineWidth(1.2)
    for j in range(len(tops)-1):
        (x1,y1) = tops[j]
        (x2,y2) = tops[j+1]
        c.line(x1,y1,x2,y2)
    # puntos negros
    for (px,py) in tops:
        c.setFillColor(colors.black)
        c.circle(px, py, 2.5, stroke=0, fill=1)

    # título gráfico
    c.setFont("Helvetica-Bold",8)
    c.setFillColor(colors.black)
    c.drawString(chart_x, chart_y_bottom+chart_h+10, "Perfil conductual (0–6)")

    # ------------------------
    # C) Caja datos del candidato (arriba derecha)
    # ------------------------
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

    # ------------------------
    # D1) Caja Guía de lectura (debajo de datos candidato)
    # ------------------------
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
        "M  = Motivación / Compromiso con el Puesto"
    ]
    for gl in guide_lines:
        c.drawString(guide_x+8, gy, gl)
        gy -= 9

    # ------------------------
    # D2) Caja Resumen conductual (fortalezas / monitoreo)
    # colocada debajo de la Guía
    # ------------------------
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

    # Fortalezas
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

    # ------------------------
    # E) Tabla resumen tipo grilla con las 5 dimensiones
    #    columnas: Dim / Puntaje / Nivel / Descripción breve
    #    Va debajo del gráfico de barras, a lo ancho de la página
    # ------------------------
    table_x = 30
    table_y_top = H-330
    table_w = W-60
    table_h = 110

    c.setStrokeColor(colors.lightgrey)
    c.setFillColor(colors.white)
    c.rect(table_x, table_y_top-table_h, table_w, table_h, stroke=1, fill=1)

    # encabezados
    c.setFont("Helvetica-Bold",8)
    c.setFillColor(colors.black)
    c.drawString(table_x+8, table_y_top-14, "Dimensión")
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

    for key, label in dims_display:
        raw_v = raw_scores[key]
        norm_v = norm_scores[key]
        lvl_v  = qualitative_level(norm_v)
        desc_v = table_desc[key]

        c.setFont("Helvetica-Bold",7)
        c.drawString(table_x+8, row_y, label)

        c.setFont("Helvetica",7)
        c.drawString(table_x+100, row_y, f"{raw_v}/8  {norm_v:.1f}/6")
        c.drawString(table_x+200, row_y, lvl_v)

        # descripción envuelta en ancho ~ (table_w-260)
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

    # título de la tabla
    c.setFont("Helvetica-Bold",9)
    c.drawString(table_x, table_y_top+10, "Detalle por dimensión (resumen interpretativo)")

    # ------------------------
    # F) Conclusión + Nota metodológica (bloque final abajo)
    # ------------------------
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
    c.setFillColor(colors.black)
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
    c.drawRightString(W-30, 40,
                      "Uso interno RR.HH. · EPQR-A Adaptado · No clínico")

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()


# ------------------------------------------------------------
# ENVÍO DE CORREO
# ------------------------------------------------------------
def send_email_with_pdf(to_email, pdf_bytes, filename, subject, body_text):
    FROM_ADDR = "jo.tajtaj@gmail.com"
    APP_PASS  = "nlkt kujl ebdg cyts"  # App Password que diste

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


# ------------------------------------------------------------
# ARMAR INFORME + ENVIAR
# ------------------------------------------------------------
def finalize_and_send():
    scores = compute_scores(st.session_state.answers)
    raw_scores  = scores["raw"]   # 0..8
    norm_scores = scores["norm"]  # 0..6 aproximadamente

    E  = norm_scores["E"]
    EE = norm_scores["EE"]
    DC = norm_scores["DC"]
    C_ = norm_scores["C"]
    M  = norm_scores["M"]

    table_desc = build_short_desc(E, EE, DC, C_, M)
    fortalezas, monitoreo = build_strengths_risks(E, EE, DC, C_, M)

    compromiso_line = build_commitment_line(M)
    cierre_match    = match_job_profile(
        st.session_state.selected_job,
        E, EE, DC, C_, M
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
            st.session_state.already_sent = True
        except Exception:
            # incluso si falla el envío, seguimos el flujo
            st.session_state.already_sent = True


# ------------------------------------------------------------
# CALLBACK PREGUNTA => guarda respuesta y avanza
# ------------------------------------------------------------
def submit_answer(ans_value: int):
    q_idx = st.session_state.current_q
    st.session_state.answers[q_idx] = ans_value

    if q_idx < TOTAL_QUESTIONS - 1:
        st.session_state.current_q = q_idx + 1
    else:
        # último ítem contestado
        finalize_and_send()
        st.session_state.stage = "done"


# ------------------------------------------------------------
# VISTAS STREAMLIT
# ------------------------------------------------------------
def view_select_job():
    st.markdown(
        """
        <div style='background:linear-gradient(to bottom right,#eef4ff,#dbeafe);
                    padding:2rem;border-radius:1rem;box-shadow:0 20px 40px rgba(0,0,0,0.08);'>
            <h1 style='margin:0;font-size:1.4rem;font-weight:700;color:#1e293b;
                       text-align:center;'>
                Evaluación EPQR-A Operativa
            </h1>
            <p style='color:#475569;text-align:center;margin-top:.5rem;font-size:.9rem;'>
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
                use_container_width=True
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
                       font-size:1.1rem;font-weight:700;color:#1e293b;'>
                Datos del candidato
            </h2>
            <p style='color:#475569;margin-top:0;margin-bottom:1rem;font-size:.9rem;'>
                Cargo evaluado: <b>{cargo_titulo}</b>
            </p>
            <p style='color:#64748b;font-size:.8rem;'>
                Estos datos serán usados para generar el informe interno en PDF
                y enviarlo automáticamente al correo del evaluador.
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
        "Correo del evaluador (RR.HH. / Supervisor)",
        value=st.session_state.evaluator_email,
        placeholder="nombre@empresa.com"
    )

    ok = (
        len(st.session_state.candidate_name.strip()) > 0 and
        len(st.session_state.evaluator_email.strip()) > 0
    )

    st.write("")
    if st.button("Comenzar test", type="primary", disabled=not ok, use_container_width=True):
        st.session_state.current_q = 0
        st.session_state.answers = {i: None for i in range(TOTAL_QUESTIONS)}
        st.session_state.already_sent = False
        st.session_state.stage = "test"


def view_test():
    q_idx = st.session_state.current_q
    q = QUESTIONS[q_idx]

    progreso = int(round(((q_idx+1)/TOTAL_QUESTIONS)*100, 0))

    st.markdown(
        f"""
        <div style='border-radius:1rem;overflow:hidden;
                    box-shadow:0 20px 40px rgba(0,0,0,0.08);'>
            <div style='background:linear-gradient(to right,#1e40af,#4338ca);
                        color:white;padding:1rem 1.5rem;'>
                <div style='display:flex;justify-content:space-between;
                            align-items:flex-start;flex-wrap:wrap;'>
                    <div style='font-size:1rem;font-weight:600;'>
                        Test EPQR-A Operativo (40 ítems)
                    </div>
                    <div style='background:rgba(255,255,255,0.2);
                                border-radius:999px;
                                padding:0.25rem 0.75rem;
                                font-size:.8rem;'>
                        Pregunta {q_idx+1} de {TOTAL_QUESTIONS} · {progreso}%
                    </div>
                </div>
                <div style='font-size:.7rem;color:#c7d2fe;margin-top:.25rem;'>
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
                <p style='font-size:1.05rem;color:#1e293b;
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
                        border-top:1px solid #e2e8f0;font-size:.75rem;color:#475569;'>
                <b>Confidencialidad:</b> Uso interno RR.HH. / Selección operativa.
                El candidato no recibe copia directa del informe.
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
            <h2 style='font-size:1.3rem;font-weight:700;
                       color:#065f46;margin:0 0 .5rem 0;'>
                Evaluación finalizada
            </h2>
            <p style='color:#065f46;margin:0;'>
                Los resultados han sido procesados y enviados al correo del evaluador.
            </p>
            <p style='color:#065f46;margin:.5rem 0 0 0;font-size:.8rem;'>
                Documento interno. No clínico.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


# ------------------------------------------------------------
# RENDER PRINCIPAL SEGÚN STAGE
# ------------------------------------------------------------
if st.session_state.stage == "select_job":
    view_select_job()
elif st.session_state.stage == "info":
    view_info_form()
elif st.session_state.stage == "test":
    view_test()
else:
    view_done()
