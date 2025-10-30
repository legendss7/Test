# ================================================================
#  Big Five (OCEAN) — Evaluación Laboral PRO (auto-avance + PDF)
#  Con medidores semicirculares en pantalla y en el PDF
# ================================================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from io import BytesIO
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Configuración de correo
EMAIL_REMITENTE = "jo.tajtaj@gmail.com"
CONTRASEÑA_APP = "nlkt kujl ebdg cyts"  # Contraseña de aplicación de 16 dígitos
EMAIL_DESTINO = "jo.tajtaj@gmail.com"

# Intento usar matplotlib (para PDF). Si no está, fallback a HTML.
HAS_MPL = False
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    from matplotlib.patches import FancyBboxPatch, Wedge, Circle
    HAS_MPL = True
except Exception:
    HAS_MPL = False

# ---------------------------------------------------------------
# Config general
# ---------------------------------------------------------------
st.set_page_config(
    page_title="Big Five PRO | Evaluación Laboral",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------
# Estilos: fondo blanco, tipografías y UI suave + tarjetas color pastel
# ---------------------------------------------------------------
st.markdown("""
<style>
/* Ocultar sidebar */
[data-testid="stSidebar"] { display:none !important; }
/* Base */
html, body, [data-testid="stAppViewContainer"]{
  background:#ffffff !important; color:#111 !important;
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
}
.block-container{ max-width:1200px; padding-top:0.8rem; padding-bottom:2rem; }
/* Títulos grandes y animados para dimensión */
.dim-title{
  font-size:clamp(2.2rem, 5vw, 3.2rem);
  font-weight:900; letter-spacing:.2px; line-height:1.12;
  margin:.2rem 0 .6rem 0;
  animation: slideIn .3s ease-out both;
}
@keyframes slideIn{
  from{ transform: translateY(6px); opacity:0; }
  to{ transform: translateY(0); opacity:1; }
}
.dim-desc{ margin:.1rem 0 1rem 0; opacity:.9; }
/* Tarjeta */
.card{
  border:1px solid #eee; border-radius:14px; background:#fff;
  box-shadow: 0 2px 0 rgba(0,0,0,0.03); padding:18px;
}
/* KPIs */
.kpi-grid{
  display:grid; grid-template-columns: repeat(auto-fit, minmax(200px,1fr));
  gap:12px; margin:10px 0 6px 0;
}
.kpi{
  border:1px solid #eee; border-radius:14px; background:#fff; padding:16px;
  position:relative; overflow:hidden;
}
.kpi::after{
  content:""; position:absolute; inset:0;
  background: linear-gradient(120deg, rgba(255,255,255,0) 0%,
    rgba(240,240,240,0.7) 45%, rgba(255,255,255,0) 90%);
  transform: translateX(-100%);
  animation: shimmer 2s ease-in-out 1;
}
@keyframes shimmer { to{ transform: translateX(100%);} }
.kpi .label{ font-size:.95rem; opacity:.85; }
.kpi .value{ font-size:2.2rem; font-weight:900; line-height:1; }
/* “count-up” visual declarativo */
.countup[data-target]::after{ content: attr(data-target); }
/* Expander */
details, [data-testid="stExpander"]{
  background:#fff; border:1px solid #eee; border-radius:12px;
}
/* Tabla */
[data-testid="stDataFrame"] div[role="grid"]{ font-size:0.95rem; }
/* Botones */
button[kind="primary"], button[kind="secondary"]{ width:100%; }
/* Chips */
.tag{ display:inline-block; padding:.2rem .6rem; border:1px solid #eee; border-radius:999px; font-size:.82rem; }
hr{ border:none; border-top:1px solid #eee; margin:16px 0; }
/* Paleta pastel por dimensión (encabezados y badges) */
.pastel-O { background:#F0F7FF; border-color:#E0EEFF; }
.pastel-C { background:#F7FFF2; border-color:#E9FBE0; }
.pastel-E { background:#FFF6F2; border-color:#FFE7DE; }
.pastel-A { background:#F9F6FF; border-color:#ECE6FF; }
.pastel-N { background:#F2FBFF; border-color:#E5F7FF; }
/* Encabezado de la tarjeta de análisis por dimensión */
.dim-card{
  border:1px solid #eee; border-radius:14px; overflow:hidden; background:#fff;
}
.dim-card-header{
  padding:14px 16px; display:flex; align-items:center; gap:10px; border-bottom:1px solid #eee;
}
.dim-chip {
  font-weight:800; padding:.2rem .6rem; border-radius:999px; border:1px solid rgba(0,0,0,.06);
  background:#fff;
}
.dim-title-row{ display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap; }
.dim-title-name{ font-size:1.2rem; font-weight:800; margin:0; }
.dim-score{ font-size:1.1rem; font-weight:800; }
.dim-body{ padding:16px; }
.dim-grid{
  display:grid; grid-template-columns: repeat(auto-fit, minmax(260px,1fr)); gap:12px;
}
.dim-section{ border:1px solid #eee; border-radius:12px; padding:12px; background:#fff; }
.dim-section h4{ margin:.2rem 0 .4rem 0; font-size:1rem; }
.dim-list{ margin:.2rem 0; padding-left:18px; }
.dim-list li{ margin:.15rem 0; }
/* Badges nivel */
.badge{
  display:inline-flex; align-items:center; gap:6px; padding:.25rem .55rem; font-size:.82rem;
  border-radius:999px; border:1px solid #eaeaea; background:#fafafa;
}
/* Pequeño tip de accesibilidad visual */
.small{ font-size:0.95rem; opacity:.9; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------
# Definiciones Big Five
# ---------------------------------------------------------------
def reverse_score(v:int)->int: return 6 - v
# Paleta por dimensión
DIMENSIONES = {
    "Apertura a la Experiencia": {
        "code":"O", "icon":"💡",
        "desc":"Curiosidad intelectual, creatividad y apertura al cambio.",
        "color":"#8FB996",
        "fort_high":[
            "Genera ideas originales y puentes entre conceptos.",
            "Explora nuevas metodologías con aprendizaje rápido.",
            "Promueve mejora continua y experimentación controlada.",
        ],
        "risk_high":[
            "Puede dispersarse en demasiadas líneas de trabajo.",
            "Riesgo de sobre-innovar sin consolidar procesos.",
            "Tendencia a aburrirse con tareas repetitivas.",
        ],
        "fort_low":[
            "Constancia y apego a estándares probados.",
            "Ejecución confiable en entornos estables.",
        ],
        "risk_low":[
            "Resistencia al cambio y menor exploración conceptual.",
            "Más dificultad para innovar en ambigüedad.",
        ],
        "recs_low":[
            "Implementar micro-experimentos quincenales de 1h.",
            "Exposición breve a nuevas herramientas (demo/POC).",
        ],
        "roles_high":["Innovación","I+D","Diseño","Estrategia","Consultoría"],
        "roles_low":["Operaciones estandarizadas","Control de calidad"],
        "no_apt_high":["Cargos ultra-rutinarios sin espacio creativo"],
        "no_apt_low":["Laboratorios de innovación, estrategia corporativa"]
    },
    "Responsabilidad": {
        "code":"C", "icon":"🎯",
        "desc":"Orden, planificación, disciplina y cumplimiento de objetivos.",
        "color":"#A1C3D1",
        "fort_high":[
            "Fiabilidad en plazos y calidad del entregable.",
            "Excelente gestión del tiempo y priorización.",
            "Documentación y control de procesos destacables.",
        ],
        "risk_high":[
            "Perfeccionismo que retrasa entregas.",
            "Rigidez ante cambios de última hora.",
        ],
        "fort_low":[
            "Flexibilidad y adaptación rápida a imprevistos.",
            "Espacio para creatividad sin autoexigencia excesiva.",
        ],
        "risk_low":[
            "Procrastinación y baja tasa de finalización.",
            "Desorden operativo si no hay supervisión.",
        ],
        "recs_low":[
            "Timeboxing diario y checklist de 3 prioridades.",
            "Revisión semanal con métricas de finalización.",
        ],
        "roles_high":["Gestión de Proyectos","Finanzas","Auditoría","Operaciones"],
        "roles_low":["Ideación temprana abierta"],
        "no_apt_high":["Entornos caóticos sin procesos definidos"],
        "no_apt_low":["PMO, compliance, control interno"]
    },
    "Extraversión": {
        "code":"E", "icon":"🗣️",
        "desc":"Asertividad, sociabilidad y energía en interacción.",
        "color":"#F2C6B4",
        "fort_high":[
            "Networking sostenido y visibilidad del equipo.",
            "Comunicación clara ante grupos y stakeholders.",
            "Motivación del equipo en contextos colaborativos.",
        ],
        "risk_high":[
            "Riesgo de monopolizar conversaciones.",
            "Puede subvalorar la escucha profunda/activa.",
        ],
        "fort_low":[
            "Profundidad de análisis y foco individual.",
            "Comunicación escrita sólida y estructurada.",
        ],
        "risk_low":[
            "Evita exposición y grandes audiencias.",
            "Menor presencia en foros de decisión.",
        ],
        "recs_low":[
            "Exposición gradual a presentaciones (micro-stands).",
            "Reuniones 1:1 para construir confianza.",
        ],
        "roles_high":["Ventas","Relaciones Públicas","Liderazgo Comercial","BD"],
        "roles_low":["Análisis","Investigación","Programación","Datos"],
        "no_apt_high":["Roles de aislamiento con mínima interacción"],
        "no_apt_low":["Puestos comerciales de alto contacto inmediato"]
    },
    "Amabilidad": {
        "code":"A", "icon":"🤝",
        "desc":"Colaboración, empatía y confianza.",
        "color":"#E8D6CB",
        "fort_high":[
            "Clima de confianza y cohesión en el equipo.",
            "Gestión empática de conflictos.",
            "Excelente experiencia de cliente/usuario.",
        ],
        "risk_high":[
            "Evitar conversaciones difíciles o decir 'no'.",
            "Difícil establecer límites en alta presión.",
        ],
        "fort_low":[
            "Objetividad y firmeza en decisiones.",
            "Negociación más dura con foco en métricas.",
        ],
        "risk_low":[
            "Relaciones sensibles pueden deteriorarse.",
            "Riesgo de fricción intraequipo si no hay tacto.",
        ],
        "recs_low":[
            "Entrenar feedback con método SBI.",
            "Establecer límites claros por escrito.",
        ],
        "roles_high":["RR.HH.","Customer Success","Mediación","Atención a clientes"],
        "roles_low":["Negociación dura","Trading"],
        "no_apt_high":["Roles donde se requiere confrontación permanente"],
        "no_apt_low":["Facilitación, mediación, soporte sensible"]
    },
    "Estabilidad Emocional": {
        "code":"N", "icon":"🧘",
        "desc":"Gestión del estrés, resiliencia y calma bajo presión.",
        "color":"#D6EADF",
        "fort_high":[
            "Serenidad en incidentes y crisis.",
            "Recuperación rápida y foco en soluciones.",
            "Juicio estable en incertidumbre.",
        ],
        "risk_high":[
            "Subestimar señales de estrés ajeno.",
            "Puede comunicar calma como frialdad.",
        ],
        "fort_low":[
            "Sensibilidad que potencia empatía y creatividad.",
        ],
        "risk_low":[
            "Rumiación, estrés elevado y fluctuaciones de ánimo.",
            "Toma de decisiones afectada por presión.",
        ],
        "recs_low":[
            "Técnicas 4-7-8 y pausas de respiración.",
            "Rutina de sueño + journaling breve diario.",
        ],
        "roles_high":["Operaciones críticas","Dirección","Soporte incidentes","Compliance"],
        "roles_low":["Ambientes caóticos sin soporte"],
        "no_apt_high":["Roles donde se requiera hiper-empatía constante"],
        "no_apt_low":["Puestos de alta presión sin acompañamiento"]
    },
}
DIM_LIST = list(DIMENSIONES.keys())
LIKERT = {1:"Totalmente en desacuerdo", 2:"En desacuerdo", 3:"Neutral", 4:"De acuerdo", 5:"Totalmente de acuerdo"}
LIK_KEYS = list(LIKERT.keys())
# 50 ítems (10 por dimensión; 5 directos, 5 invertidos)
QUESTIONS = [
    # O
    {"text":"Tengo una imaginación muy activa.","dim":"Apertura a la Experiencia","key":"O1","rev":False},
    {"text":"Me atraen ideas nuevas y complejas.","dim":"Apertura a la Experiencia","key":"O2","rev":False},
    {"text":"Disfruto del arte y la cultura.","dim":"Apertura a la Experiencia","key":"O3","rev":False},
    {"text":"Busco experiencias poco convencionales.","dim":"Apertura a la Experiencia","key":"O4","rev":False},
    {"text":"Valoro la creatividad sobre la rutina.","dim":"Apertura a la Experiencia","key":"O5","rev":False},
    {"text":"Prefiero mantener hábitos que probar cosas nuevas.","dim":"Apertura a la Experiencia","key":"O6","rev":True},
    {"text":"Las discusiones filosóficas me parecen poco útiles.","dim":"Apertura a la Experiencia","key":"O7","rev":True},
    {"text":"Rara vez reflexiono sobre conceptos abstractos.","dim":"Apertura a la Experiencia","key":"O8","rev":True},
    {"text":"Me inclino por lo tradicional más que por lo original.","dim":"Apertura a la Experiencia","key":"O9","rev":True},
    {"text":"Evito cambiar mis hábitos establecidos.","dim":"Apertura a la Experiencia","key":"O10","rev":True},
    # C
    {"text":"Estoy bien preparado/a para mis tareas.","dim":"Responsabilidad","key":"C1","rev":False},
    {"text":"Cuido los detalles al trabajar.","dim":"Responsabilidad","key":"C2","rev":False},
    {"text":"Cumplo mis compromisos y plazos.","dim":"Responsabilidad","key":"C3","rev":False},
    {"text":"Sigo un plan y un horario definidos.","dim":"Responsabilidad","key":"C4","rev":False},
    {"text":"Me exijo altos estándares de calidad.","dim":"Responsabilidad","key":"C5","rev":False},
    {"text":"Dejo mis cosas desordenadas.","dim":"Responsabilidad","key":"C6","rev":True},
    {"text":"Evito responsabilidades cuando puedo.","dim":"Responsabilidad","key":"C7","rev":True},
    {"text":"Me distraigo con facilidad.","dim":"Responsabilidad","key":"C8","rev":True},
    {"text":"Olvido colocar las cosas en su lugar.","dim":"Responsabilidad","key":"C9","rev":True},
    {"text":"Aplazo tareas importantes.","dim":"Responsabilidad","key":"C10","rev":True},
    # E
    {"text":"Disfruto ser visible en reuniones.","dim":"Extraversión","key":"E1","rev":False},
    {"text":"Me siento a gusto con personas nuevas.","dim":"Extraversión","key":"E2","rev":False},
    {"text":"Busco la compañía de otras personas.","dim":"Extraversión","key":"E3","rev":False},
    {"text":"Participo activamente en conversaciones.","dim":"Extraversión","key":"E4","rev":False},
    {"text":"Me energiza compartir con otros.","dim":"Extraversión","key":"E5","rev":False},
    {"text":"Prefiero estar solo/a que rodeado/a de gente.","dim":"Extraversión","key":"E6","rev":True},
    {"text":"Soy más bien reservado/a y callado/a.","dim":"Extraversión","key":"E7","rev":True},
    {"text":"Me cuesta expresarme ante grupos grandes.","dim":"Extraversión","key":"E8","rev":True},
    {"text":"Prefiero actuar en segundo plano.","dim":"Extraversión","key":"E9","rev":True},
    {"text":"Me agotan las interacciones sociales prolongadas.","dim":"Extraversión","key":"E10","rev":True},
    # A
    {"text":"Empatizo con las emociones de los demás.","dim":"Amabilidad","key":"A1","rev":False},
    {"text":"Me preocupo por el bienestar ajeno.","dim":"Amabilidad","key":"A2","rev":False},
    {"text":"Trato a otros con respeto y consideración.","dim":"Amabilidad","key":"A3","rev":False},
    {"text":"Ayudo sin esperar nada a cambio.","dim":"Amabilidad","key":"A4","rev":False},
    {"text":"Confío en las buenas intenciones de la gente.","dim":"Amabilidad","key":"A5","rev":False},
    {"text":"No me interesa demasiado la gente.","dim":"Amabilidad","key":"A6","rev":True},
    {"text":"Sospecho de las intenciones ajenas.","dim":"Amabilidad","key":"A7","rev":True},
    {"text":"A veces soy poco considerado/a.","dim":"Amabilidad","key":"A8","rev":True},
    {"text":"Pienso primero en mí antes que en otros.","dim":"Amabilidad","key":"A9","rev":True},
    {"text":"Los problemas de otros no me afectan mucho.","dim":"Amabilidad","key":"A10","rev":True},
    # N
    {"text":"Me mantengo calmado/a bajo presión.","dim":"Estabilidad Emocional","key":"N1","rev":False},
    {"text":"Rara vez me siento ansioso/a o estresado/a.","dim":"Estabilidad Emocional","key":"N2","rev":False},
    {"text":"Soy emocionalmente estable.","dim":"Estabilidad Emocional","key":"N3","rev":False},
    {"text":"Me recupero rápido de contratiempos.","dim":"Estabilidad Emocional","key":"N4","rev":False},
    {"text":"Me siento seguro/a de mí mismo/a.","dim":"Estabilidad Emocional","key":"N5","rev":False},
    {"text":"Me preocupo demasiado por las cosas.","dim":"Estabilidad Emocional","key":"N6","rev":True},
    {"text":"Me irrito con facilidad.","dim":"Estabilidad Emocional","key":"N7","rev":True},
    {"text":"Con frecuencia me siento triste.","dim":"Estabilidad Emocional","key":"N8","rev":True},
    {"text":"Tengo cambios de ánimo frecuentes.","dim":"Estabilidad Emocional","key":"N9","rev":True},
    {"text":"El estrés me sobrepasa.","dim":"Estabilidad Emocional","key":"N10","rev":True},
]
KEY2IDX = {q["key"]:i for i,q in enumerate(QUESTIONS)}

# ---------------------------------------------------------------
# Estado
# ---------------------------------------------------------------
if "stage" not in st.session_state: st.session_state.stage = "inicio"  # inicio | test | resultados
if "q_idx" not in st.session_state: st.session_state.q_idx = 0
if "answers" not in st.session_state: st.session_state.answers = {q["key"]:None for q in QUESTIONS}
if "fecha" not in st.session_state: st.session_state.fecha = None
if "_needs_rerun" not in st.session_state: st.session_state._needs_rerun = False
if "pdf_bytes_cache" not in st.session_state: st.session_state.pdf_bytes_cache = None

# ---------------------------------------------------------------
# Utilidades de cálculo
# ---------------------------------------------------------------
def compute_scores(answers:dict)->dict:
    buckets = {d:[] for d in DIM_LIST}
    for q in QUESTIONS:
        raw = answers.get(q["key"])
        v = 3 if raw is None else (reverse_score(raw) if q["rev"] else raw)
        buckets[q["dim"]].append(v)
    out = {}
    for d, vals in buckets.items():
        avg = np.mean(vals)
        perc = ((avg - 1) / 4.0) * 100
        out[d] = round(float(perc), 1)
    return out

def level_label(score:float):
    if score>=75: return "Muy Alto","Dominante"
    if score>=60: return "Alto","Marcado"
    if score>=40: return "Promedio","Moderado"
    if score>=25: return "Bajo","Suave"
    return "Muy Bajo","Mínimo"

def dimension_profile(d:str, score:float):
    ds = DIMENSIONES[d]
    if score>=60:
        f = ds["fort_high"] + [
            "Capacidad de modelar buenas prácticas para pares.",
            "Eleva el estándar del equipo en esa dimensión."
        ]
        r = ds["risk_high"] + ["Si no se regula, impacta foco/tiempos de otros."]
        rec = [
            "Definir OKRs y criterios de cierre por sprint.",
            "Hitos intermedios con aceptación por pares.",
            "Revisión quincenal para calibrar foco/impacto."
        ]
        roles = ds["roles_high"]; not_apt = ds.get("no_apt_high", [])
        expl = "KPI alto: tu conducta típica favorece el desempeño cuando el rol exige este rasgo como palanca principal."
    elif score<40:
        f = ds["fort_low"] + ["Estabilidad de ejecución en límites conocidos."]
        r = ds["risk_low"] + ["Puede requerir soporte explícito en entornos de presión/ambigüedad."]
        rec = ds["recs_low"] + [
            "Rutina breve semanal de reflexión de aprendizajes.",
            "Definir 1 hábito palanca (2 min/día) durante 21 días."
        ]
        roles = ds["roles_low"]; not_apt = ds.get("no_apt_low", [])
        expl = "KPI bajo: tu estilo se sitúa en el extremo opuesto; útil en ciertos contextos, con riesgos en otros si no hay compensaciones."
    else:
        f = ["Balance situacional entre ambos extremos", "Capacidad de lectura del contexto antes de actuar"]
        r = ["Variabilidad entre equipos/líderes; alinear expectativas", "Riesgo de ambivalencia si faltan métricas claras"]
        rec = ["Definir escenarios de cuándo 'subir' o 'bajar' este rasgo", "Feedback mensual de 360° enfocado en esta dimensión"]
        roles = ds["roles_high"][:2] + ds["roles_low"][:1]; not_apt = []
        expl = "KPI medio: perfil flexible; puede optimizarse con reglas simples de activación según el entorno."
    return f, r, rec, roles, not_apt, expl

# ---------------------------------------------------------------
# Auto-avance: callback SIN doble click (bandera + rerun al final)
# ---------------------------------------------------------------
def on_answer_change(qkey:str):
    st.session_state.answers[qkey] = st.session_state.get(f"resp_{qkey}")
    idx = KEY2IDX[qkey]
    if idx < len(QUESTIONS)-1:
        st.session_state.q_idx = idx + 1
    else:
        st.session_state.stage = "resultados"
        st.session_state.fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    st.session_state._needs_rerun = True  # rerun único al final

# ---------------------------------------------------------------
# Función para enviar correo con PDF adjunto
# ---------------------------------------------------------------
def enviar_correo(pdf_bytes: bytes, fecha: str):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_REMITENTE
        msg['To'] = EMAIL_DESTINO
        msg['Subject'] = f"📄 Resultado Big Five — {fecha}"

        cuerpo = "Hola,\n\nAdjunto encontrarás el resultado del Test Big Five (OCEAN).\n\nSaludos."
        msg.attach(MIMEText(cuerpo, 'plain'))

        parte = MIMEBase('application', 'octet-stream')
        parte.set_payload(pdf_bytes)
        encoders.encode_base64(parte)
        parte.add_header('Content-Disposition', 'attachment; filename=Resultado_BigFive.pdf')
        msg.attach(parte)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_REMITENTE, CONTRASEÑA_APP.replace(" ", ""))
        server.sendmail(EMAIL_REMITENTE, EMAIL_DESTINO, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error al enviar correo: {e}")
        return False

# ---------------------------------------------------------------
# Gráficos (Radar, Barras, Gauge semicircular Plotly)
# ---------------------------------------------------------------
def plot_radar(res:dict):
    order = list(res.keys())
    vals = [res[d] for d in order]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals, theta=[f"{DIMENSIONES[d]['code']} {d}" for d in order],
        fill='toself', name='Perfil',
        line=dict(width=2, color="#6D597A"),
        fillcolor='rgba(109, 89, 122, .12)',
        marker=dict(size=7, color="#6D597A")
    ))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,100])),
                      showlegend=False, height=520, template="plotly_white")
    return fig

def plot_bar(res:dict):
    palette = ["#81B29A","#F2CC8F","#E07A5F","#9C6644","#6D597A"]
    df = pd.DataFrame({"Dimensión":list(res.keys()),"Puntuación":list(res.values())}).sort_values("Puntuación")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df["Dimensión"], x=df["Puntuación"], orientation='h',
        marker=dict(color=[palette[i%len(palette)] for i in range(len(df))]),
        text=[f"{v:.1f}" for v in df["Puntuación"]], textposition="outside"
    ))
    fig.update_layout(height=520, template="plotly_white",
                      xaxis=dict(range=[0,105], title="Puntuación (0–100)"),
                      yaxis=dict(title=""))
    return fig, df

def gauge_plotly(value: float, title: str = "", color="#6D597A"):
    """Medidor semicircular (0–100) con aguja."""
    v = max(0, min(100, float(value)))
    bounds = [0, 25, 40, 60, 75, 100]
    colors = ["#fde2e1", "#fff0c2", "#e9f2fb", "#e7f6e8", "#d9f2db"]
    vals = [bounds[i+1]-bounds[i] for i in range(len(bounds)-1)]
    fig = go.Figure()
    fig.add_trace(go.Pie(
        values=vals, hole=0.6, rotation=180, direction="clockwise",
        text=[f"{bounds[i]}–{bounds[i+1]}" for i in range(5)],
        textinfo="none", marker=dict(colors=colors, line=dict(color="#ffffff", width=1)),
        hoverinfo="skip", showlegend=False, sort=False
    ))
    import math
    theta = (180 * (v/100.0))
    r = 0.95; x0, y0 = 0.5, 0.5
    xe = x0 + r*math.cos(math.radians(180 - theta))
    ye = y0 + r*math.sin(math.radians(180 - theta))
    fig.add_shape(type="line", x0=x0, y0=y0, x1=xe, y1=ye, line=dict(color=color, width=4))
    fig.add_shape(type="circle", x0=x0-0.02, y0=y0-0.02, x1=x0+0.02, y1=y0+0.02,
                  line=dict(color=color), fillcolor=color)
    fig.update_layout(
        annotations=[
            dict(text=f"<b>{v:.1f}</b>", x=0.5, y=0.32, showarrow=False, font=dict(size=24, color="#111")),
            dict(text=title, x=0.5, y=0.16, showarrow=False, font=dict(size=13, color="#333")),
        ],
        margin=dict(l=10, r=10, t=10, b=10), showlegend=False, height=220
    )
    return fig

# ---------------------------------------------------------------
# Exportar (PDF con medidores; HTML si no hay MPL)
# ---------------------------------------------------------------
def pdf_semicircle(ax, value, cx=0.5, cy=0.5, r=0.45):
    """Dibuja un medidor semicircular matplotlib (0–100)."""
    v = max(0, min(100, float(value)))
    bands = [(0,25,"#fde2e1"), (25,40,"#fff0c2"), (40,60,"#e9f2fb"),
             (60,75,"#e7f6e8"), (75,100,"#d9f2db")]
    for a,b,c in bands:
        ang1 = 180*(a/100.0); ang2 = 180*(b/100.0)
        w = Wedge((cx,cy), r, 180-ang2, 180-ang1, facecolor=c, edgecolor="#fff", lw=1)
        ax.add_patch(w)
    import math
    theta = math.radians(180*(v/100.0))
    x2 = cx + r*0.95*math.cos(np.pi - theta)
    y2 = cy + r*0.95*math.sin(np.pi - theta)
    ax.plot([cx, x2], [cy, y2], color="#6D597A", lw=3)
    ax.add_patch(Circle((cx,cy), 0.02, color="#6D597A"))
    ax.text(cx, cy-0.12, f"{v:.1f}", ha="center", va="center", fontsize=16, color="#111")

def build_pdf(res:dict, fecha:str)->bytes:
    order = list(res.keys()); vals=[res[d] for d in order]
    avg = np.mean(vals); std = np.std(vals, ddof=1) if len(vals)>1 else 0.0
    rng = np.max(vals)-np.min(vals); top = max(res, key=res.get); low = min(res, key=res.get)
    buf = BytesIO()
    with PdfPages(buf) as pdf:
        # Portada + KPIs con 3 medidores semicirculares
        fig = plt.figure(figsize=(8.27,11.69))  # A4
        ax = fig.add_axes([0,0,1,1]); ax.axis('off')
        ax.text(.5,.95,"Informe Big Five — Contexto Laboral", ha='center', fontsize=20, fontweight='bold')
        ax.text(.5,.92,f"Fecha: {fecha}", ha='center', fontsize=11)
        # Tarjetas KPI
        def card(ax, x,y,w,h,title,val):
            r = FancyBboxPatch((x,y), w,h, boxstyle="round,pad=0.012,rounding_size=0.018",
                               edgecolor="#dddddd", facecolor="#ffffff")
            ax.add_patch(r)
            ax.text(x+w*0.06, y+h*0.60, title, fontsize=10, color="#333")
            ax.text(x+w*0.06, y+h*0.25, f"{val}", fontsize=20, fontweight='bold')
        Y0 = .82; H = .10; W = .40; GAP = .02
        card(ax, .06, Y0, W, H, "Promedio (0–100)", f"{avg:.1f}")
        card(ax, .54, Y0, W, H, "Desviación estándar", f"{std:.2f}")
        card(ax, .06, Y0-(H+GAP), W, H, "Rango entre dimensiones", f"{rng:.2f}")
        card(ax, .54, Y0-(H+GAP), W, H, "Dimensión destacada", f"{top}")
        # Tres medidores (promedio, mejor, menor)
        axg1 = fig.add_axes([.12, .54, .22, .16]); axg1.axis('off'); pdf_semicircle(axg1, avg, 0.5, 0.0, 0.9); axg1.text(.5,-.35,"Promedio",ha="center",fontsize=10)
        axg2 = fig.add_axes([.39, .54, .22, .16]); axg2.axis('off'); pdf_semicircle(axg2, res[top], 0.5, 0.0, 0.9); axg2.text(.5,-.35,f"Mayor: {top}",ha="center",fontsize=10)
        axg3 = fig.add_axes([.66, .54, .22, .16]); axg3.axis('off'); pdf_semicircle(axg3, res[low], 0.5, 0.0, 0.9); axg3.text(.5,-.35,f"Menor: {low}",ha="center",fontsize=10)
        # Lista breve
        ylist = .46
        ax.text(.08,ylist,"Resumen ejecutivo", fontsize=14, fontweight='bold'); ylist -= .04
        bullets = [
            f"Fortaleza clave: {top} ({res[top]:.1f})",
            f"Área a potenciar: {low} ({res[low]:.1f})",
            "Perfil global equilibrado" if 40<=avg<=60 else ("Tendencia alta para ambientes exigentes" if avg>60 else "Perfil conservador, ideal para entornos estables"),
            f"Variabilidad: DE={std:.2f} · Rango={rng:.2f}",
        ]
        for b in bullets:
            ax.text(.10, ylist, f"• {b}", fontsize=11); ylist -= .03
        pdf.savefig(fig, bbox_inches='tight'); plt.close(fig)
        # Barras
        fig2 = plt.figure(figsize=(8.27,11.69))
        a2 = fig2.add_subplot(111)
        y = np.arange(len(order))
        a2.barh(y, [res[d] for d in order], color="#81B29A")
        a2.set_yticks(y); a2.set_yticklabels(order)
        a2.set_xlim(0,100); a2.set_xlabel("Puntuación (0–100)")
        a2.set_title("Puntuaciones por dimensión")
        for i, v in enumerate([res[d] for d in order]):
            a2.text(v+1, i, f"{v:.1f}", va='center', fontsize=9)
        pdf.savefig(fig2, bbox_inches='tight'); plt.close(fig2)
        # Análisis por dimensión con medidor
        for d in order:
            score = res[d]; lvl, tag = level_label(score)
            f, r, recs, roles, not_apt, expl = dimension_profile(d, score)
            fig3 = plt.figure(figsize=(8.27,11.69)); ax3 = fig3.add_axes([0,0,1,1]); ax3.axis('off')
            ax3.text(.5,.95, f"{DIMENSIONES[d]['code']} — {d}", ha='center', fontsize=16, fontweight='bold')
            ax3.text(.5,.92, f"Puntuación: {score:.1f} · Nivel: {lvl} ({tag})", ha='center', fontsize=11)
            # Gauge de dimensión
            axg = fig3.add_axes([.18, .80, .64, .14]); axg.axis("off")
            pdf_semicircle(axg, score, cx=0.5, cy=0.0, r=0.9)
            def draw_list(y, title, items):
                ax3.text(.08,y,title, fontsize=13, fontweight='bold')
                yy = y - .03
                for it in items:
                    ax3.text(.10, yy, f"• {it}", fontsize=11)
                    yy -= .03
                return yy -.02
            ax3.text(.08,.78,"Descripción", fontsize=13, fontweight='bold')
            ax3.text(.08,.75, DIMENSIONES[d]["desc"], fontsize=11)
            ax3.text(.08,.71,"Explicativo del KPI", fontsize=13, fontweight='bold')
            ax3.text(.08,.68, expl, fontsize=11)
            yy = .63
            yy = draw_list(yy, "Fortalezas (laborales)", f)
            yy = draw_list(yy, "Riesgos / Cosas a cuidar", r)
            yy = draw_list(yy, "Recomendaciones", recs)
            yy = draw_list(yy, "Roles sugeridos", roles)
            draw_list(yy, "No recomendado para", not_apt if not_apt else ["—"])
            pdf.savefig(fig3, bbox_inches='tight'); plt.close(fig3)
    buf.seek(0)
    return buf.read()

def build_html(res:dict, fecha:str)->bytes:
    order = list(res.keys()); vals=[res[d] for d in order]
    avg=np.mean(vals); std=np.std(vals, ddof=1) if len(vals)>1 else 0.0; rng=np.max(vals)-np.min(vals); top=max(res,key=res.get)
    rows = ""
    for d in order:
        lvl,tag = level_label(res[d])
        rows += f"<tr><td>{DIMENSIONES[d]['code']}</td><td>{d}</td><td>{res[d]:.1f}</td><td>{lvl}</td><td>{tag}</td></tr>"
    blocks=""
    for d in order:
        score=res[d]; lvl,tag = level_label(score)
        f,r,recs,roles,not_apt, expl = dimension_profile(d, score)
        blocks += f"""
<section style="border:1px solid #eee; border-radius:12px; padding:14px; margin:14px 0;">
  <h3 style="margin:.2rem 0;">{DIMENSIONES[d]['code']} — {d} <span class='tag'>{score:.1f} · {lvl} ({tag})</span></h3>
  <p style="margin:.25rem 0; color:#333;">{DIMENSIONES[d]["desc"]}</p>
  <h4>Explicativo del KPI</h4>
  <p>{expl}</p>
  <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(220px,1fr)); gap:12px;">
    <div><h4>Fortalezas</h4><ul>{''.join([f'<li>{x}</li>' for x in f])}</ul></div>
    <div><h4>Riesgos</h4><ul>{''.join([f'<li>{x}</li>' for x in r])}</ul></div>
    <div><h4>Recomendaciones</h4><ul>{''.join([f'<li>{x}</li>' for x in recs])}</ul></div>
  </div>
  <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(220px,1fr)); gap:12px; margin-top:10px;">
    <div><h4>Roles sugeridos</h4><ul>{''.join([f'<li>{x}</li>' for x in roles])}</ul></div>
    <div><h4>No recomendado para</h4><ul>{''.join([f'<li>{x}</li>' for x in (not_apt if not_apt else ['—'])])}</ul></div>
  </div>
</section>
"""
    html=f"""<!doctype html>
<html><head><meta charset="utf-8" />
<title>Informe Big Five Laboral</title>
<style>
body{{font-family:Inter,Arial; margin:24px; color:#111;}}
h1{{font-size:24px; margin:0 0 8px 0;}}
h3{{font-size:18px; margin:.2rem 0;}}
h4{{font-size:15px; margin:.2rem 0;}}
table{{border-collapse:collapse; width:100%; margin-top:8px}}
th,td{{border:1px solid #eee; padding:8px; text-align:left;}}
.tag{{display:inline-block; padding:.2rem .6rem; border:1px solid #eee; border-radius:999px; font-size:.82rem;}}
.kpi-grid{{display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:12px; margin:10px 0 6px 0;}}
.kpi{{border:1px solid #eee; border-radius:12px; padding:12px; background:#fff;}}
.kpi .label{{font-size:13px; opacity:.85}}
.kpi .value{{font-size:22px; font-weight:800}}
@media print{{ .no-print{{display:none}} }}
</style>
</head>
<body>
<h1>Informe Big Five — Contexto Laboral</h1>
<p>Fecha: <b>{fecha}</b></p>
<div class="kpi-grid">
  <div class="kpi"><div class="label">Promedio general (0–100)</div><div class="value">{avg:.1f}</div></div>
  <div class="kpi"><div class="label">Desviación estándar</div><div class="value">{std:.2f}</div></div>
  <div class="kpi"><div class="label">Rango</div><div class="value">{rng:.2f}</div></div>
  <div class="kpi"><div class="label">Dimensión destacada</div><div class="value">{top}</div></div>
</div>
<h3>Tabla resumen</h3>
<table>
  <thead><tr><th>Código</th><th>Dimensión</th><th>Puntuación</th><th>Nivel</th><th>Etiqueta</th></tr></thead>
  <tbody>{rows}</tbody>
</table>
<h3>Análisis por dimensión (laboral)</h3>
{blocks}
<div class="no-print" style="margin-top:16px;">
  <button onclick="window.print()" style="padding:10px 14px; border:1px solid #ddd; background:#f9f9f9; border-radius:8px; cursor:pointer;">
    Imprimir / Guardar como PDF
  </button>
</div>
</body></html>"""
    return html.encode("utf-8")

# ---------------------------------------------------------------
# Vistas
# ---------------------------------------------------------------
def view_inicio():
    st.markdown(
        """
        <div class="card">
          <h1 style="margin:0 0 6px 0; font-size:clamp(2.2rem,3.8vw,3rem); font-weight:900;">
            🧠 Test Big Five (OCEAN) — Evaluación Laboral
          </h1>
          <p class="tag" style="margin:0;">Fondo blanco · Texto negro · Diseño profesional y responsivo</p>
        </div>
        """, unsafe_allow_html=True
    )
    c1, c2 = st.columns([1.35,1])
    with c1:
        st.markdown(
            """
            <div class="card">
              <h3 style="margin-top:0">¿Qué mide?</h3>
              <ul style="line-height:1.6">
                <li><b>O</b> Apertura a la Experiencia</li>
                <li><b>C</b> Responsabilidad</li>
                <li><b>E</b> Extraversión</li>
                <li><b>A</b> Amabilidad</li>
                <li><b>N</b> Estabilidad Emocional</li>
              </ul>
              <p class="small">50 ítems Likert (1–5) · Autoavance · Duración estimada: <b>8–12 min</b>.</p>
            </div>
            """, unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            """
            <div class="card">
              <h3 style="margin-top:0">Cómo funciona</h3>
              <ol style="line-height:1.6">
                <li>Ves 1 pregunta por pantalla y eliges una opción.</li>
                <li>Al elegir, avanzas automáticamente a la siguiente.</li>
                <li>Resultados con KPIs, medidores, gráficos y análisis laboral (pros, riesgos, recomendaciones, <i>roles sugeridos</i> y <i>no recomendado para</i>).</li>
              </ol>
            </div>
            """, unsafe_allow_html=True
        )
        if st.button("🚀 Iniciar evaluación", type="primary", use_container_width=True):
            st.session_state.stage = "test"
            st.session_state.q_idx = 0
            st.session_state.answers = {q["key"]:None for q in QUESTIONS}
            st.session_state.fecha = None
            st.rerun()

def view_test():
    i = st.session_state.q_idx
    q = QUESTIONS[i]
    dim = q["dim"]; code = DIMENSIONES[dim]["code"]; icon = DIMENSIONES[dim]["icon"]
    p = (i+1)/len(QUESTIONS)
    st.progress(p, text=f"Progreso: {i+1}/{len(QUESTIONS)}")
    st.markdown(f"<div class='dim-title'>{icon} {code} — {dim}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='dim-desc'>{DIMENSIONES[dim]['desc']}</div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown(f"### {i+1}. {q['text']}")
    prev = st.session_state.answers.get(q["key"])
    prev_idx = None if prev is None else LIK_KEYS.index(prev)
    st.radio(
        "Selecciona una opción",
        options=LIK_KEYS,
        index=prev_idx,
        format_func=lambda x: LIKERT[x],
        key=f"resp_{q['key']}",
        horizontal=True,
        label_visibility="collapsed",
        on_change=on_answer_change,
        args=(q["key"],),
    )
    st.markdown("</div>", unsafe_allow_html=True)

def view_resultados():
    res = compute_scores(st.session_state.answers)
    order = list(res.keys()); vals=[res[d] for d in order]
    avg = round(float(np.mean(vals)),1)
    std = round(float(np.std(vals, ddof=1)),2) if len(vals)>1 else 0.0
    rng = round(float(np.max(vals)-np.min(vals)),2)
    top = max(res, key=res.get)

    # Encabezado
    st.markdown(
        f"""
        <div class="card">
          <h1 style="margin:0 0 6px 0; font-size:clamp(2.2rem,3.8vw,3rem); font-weight:900;">📊 Informe Big Five — Resultados Laborales</h1>
          <p class="small" style="margin:0;">Fecha: <b>{st.session_state.fecha}</b></p>
        </div>
        """, unsafe_allow_html=True
    )

    # KPIs
    st.markdown("<div class='kpi-grid'>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi'><div class='label'>Promedio general (0–100)</div><div class='value countup' data-target='{avg:.1f}'>{avg:.1f}</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi'><div class='label'>Desviación estándar</div><div class='value countup' data-target='{std:.2f}'>{std:.2f}</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi'><div class='label'>Rango</div><div class='value countup' data-target='{rng:.2f}'>{rng:.2f}</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi'><div class='label'>Dimensión destacada</div><div class='value'>{top}</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🎯 Radar del perfil")
        st.plotly_chart(plot_radar(res), use_container_width=True)
    with c2:
        st.subheader("📊 Puntuaciones por dimensión")
        fig_bar, df_sorted = plot_bar(res)
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 Resumen de resultados")
    tabla = pd.DataFrame({
        "Código":[DIMENSIONES[d]["code"] for d in order],
        "Dimensión":order,
        "Puntuación":[f"{res[d]:.1f}" for d in order],
        "Nivel":[level_label(res[d])[0] for d in order],
        "Etiqueta":[level_label(res[d])[1] for d in order],
    })
    st.dataframe(tabla, use_container_width=True, hide_index=True)

    # ---------- Análisis por dimensión + Gauge ----------
    st.markdown("---")
    st.subheader("🔍 Análisis por dimensión (laboral)")
    pastel_class = {
        "Apertura a la Experiencia":"pastel-O",
        "Responsabilidad":"pastel-C",
        "Extraversión":"pastel-E",
        "Amabilidad":"pastel-A",
        "Estabilidad Emocional":"pastel-N",
    }
    for d in DIM_LIST:
        score = res[d]; lvl, tag = level_label(score)
        f, r, recs, roles, not_apt, expl = dimension_profile(d, score)
        icon = DIMENSIONES[d]["icon"]; code = DIMENSIONES[d]["code"]
        with st.container():
            st.markdown(f"""
            <div class="dim-card">
              <div class="dim-card-header {pastel_class[d]}">
                <div class="dim-chip">{icon} {code}</div>
                <div class="dim-title-row" style="flex:1;">
                  <h3 class="dim-title-name" style="margin:0;">{d}</h3>
                  <div class="badge">{score:.1f} · {lvl} · {tag}</div>
                </div>
              </div>
              <div class="dim-body">
            """, unsafe_allow_html=True)
            # Medidor semicircular (Plotly)
            st.plotly_chart(gauge_plotly(score, title=f"{lvl} · {tag}", color=DIMENSIONES[d]["color"]),
                            use_container_width=True)
            st.markdown("""
                <div class="dim-grid">
                  <div class="dim-section">
                    <h4>Descripción</h4>
                    <p class="small">""" + DIMENSIONES[d]["desc"] + """</p>
                    <h4>Explicativo del KPI</h4>
                    <p class="small">""" + expl + """</p>
                  </div>
            """, unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("**✅ Fortalezas (laborales)**")
                for x in f: st.markdown(f"- {x}")
            with c2:
                st.markdown("**⚠️ Riesgos / Cosas a cuidar**")
                for x in r: st.markdown(f"- {x}")
            with c3:
                st.markdown("**🛠️ Recomendaciones**")
                for x in recs: st.markdown(f"- {x}")
            c4, c5 = st.columns(2)
            with c4:
                st.markdown("**🎯 Roles sugeridos**")
                for x in roles: st.markdown(f"- {x}")
            with c5:
                st.markdown("**⛔ No recomendado para**")
                if not_apt:
                    for x in not_apt: st.markdown(f"- {x}")
                else:
                    st.markdown("- —")
            st.markdown("</div></div></div>", unsafe_allow_html=True)
            st.markdown("")

    st.markdown("---")
    st.subheader("📤 Enviar resultados a jo.tajtaj@gmail.com")

    # Generar PDF si no está en caché
    if st.session_state.pdf_bytes_cache is None and HAS_MPL:
        st.session_state.pdf_bytes_cache = build_pdf(res, st.session_state.fecha)

    if st.button("📧 Enviar por correo", type="primary", use_container_width=True):
        if not HAS_MPL:
            st.error("No se puede generar el PDF. Instala matplotlib.")
        else:
            with st.spinner("Enviando informe por correo..."):
                exito = enviar_correo(st.session_state.pdf_bytes_cache, st.session_state.fecha)
                if exito:
                    st.success("✅ ¡Resultado enviado correctamente a jo.tajtaj@gmail.com!")
                else:
                    st.error("❌ Error al enviar. Revisa la configuración.")

    st.markdown("---")
    st.subheader("📥 Exportar informe")
    if HAS_MPL:
        if st.session_state.pdf_bytes_cache is None:
            st.session_state.pdf_bytes_cache = build_pdf(res, st.session_state.fecha)
        st.download_button(
            "⬇️ Descargar PDF (con medidores)",
            data=st.session_state.pdf_bytes_cache,
            file_name="Informe_BigFive_Laboral.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary"
        )
    else:
        html_bytes = build_html(res, st.session_state.fecha)
        st.download_button(
            "⬇️ Descargar Reporte (HTML) — Imprime como PDF",
            data=html_bytes,
            file_name="Informe_BigFive_Laboral.html",
            mime="text/html",
            use_container_width=True,
            type="primary"
        )
        st.caption("Instala matplotlib para obtener el PDF directo con medidores.")

    st.markdown("---")
    if st.button("🔄 Nueva evaluación", type="primary", use_container_width=True):
        st.session_state.stage = "inicio"
        st.session_state.q_idx = 0
        st.session_state.answers = {q["key"]:None for q in QUESTIONS}
        st.session_state.fecha = None
        st.session_state.pdf_bytes_cache = None
        st.rerun()

# ---------------------------------------------------------------
# FLUJO PRINCIPAL
# ---------------------------------------------------------------
if st.session_state.stage == "inicio":
    view_inicio()
elif st.session_state.stage == "test":
    view_test()
else:
    # Entramos aquí si se completó o si el usuario recargó tras finalizar
    if st.session_state.fecha is None:
        st.session_state.fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    view_resultados()

# Rerun único si el callback de la radio lo marcó
if st.session_state._needs_rerun:
    st.session_state._needs_rerun = False
    st.rerun()
