# ================================================================
#  Test DISC — Evaluación Laboral PRO (auto-avance + PDF)
#  Inspirado en Big Five PRO, con medidores y análisis laboral
# ================================================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from io import BytesIO

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
    page_title="Test DISC PRO | Evaluación Laboral",
    page_icon="📊",
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
/* Paleta pastel por dimensión */
.pastel-D { background:#FFF2F0; border-color:#FFE5E0; }
.pastel-I { background:#FFF8E6; border-color:#FFF0CC; }
.pastel-S { background:#F0F9F4; border-color:#E0F2E8; }
.pastel-C { background:#F0F6FF; border-color:#E0ECFF; }
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
.badge{
  display:inline-flex; align-items:center; gap:6px; padding:.25rem .55rem; font-size:.82rem;
  border-radius:999px; border:1px solid #eaeaea; background:#fafafa;
}
.small{ font-size:0.95rem; opacity:.9; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------
# Definiciones DISC
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# Definiciones DISC — Versión de elección forzada (28 ítems, 4 frases por ítem)
# ---------------------------------------------------------------
DIMENSIONES = {
    "Dominancia": {
        "code": "D", "icon": "💪",
        "desc": "Decisión, control, resultados y acción directa.",
        "color": "#E74C3C",
        "fort_high": [
            "Toma decisiones rápidas bajo presión.",
            "Enfocado en resultados y metas claras.",
            "Liderazgo natural en crisis o desafíos."
        ],
        "risk_high": [
            "Puede ser percibido como autoritario o impaciente.",
            "Baja tolerancia a la burocracia o lentitud.",
            "Dificultad para delegar o escuchar en profundidad."
        ],
        "fort_low": [
            "Colaboración y evita imponer su voluntad.",
            "Estilo más reflexivo y menos confrontativo."
        ],
        "risk_low": [
            "Evita tomar decisiones difíciles.",
            "Puede ceder terreno en negociaciones."
        ],
        "recs_low": [
            "Practicar toma de decisiones diarias (aunque sean pequeñas).",
            "Entrenar comunicación asertiva sin agresividad."
        ],
        "roles_high": ["Liderazgo ejecutivo", "Ventas estratégicas", "Emprendimiento", "Gestión de crisis"],
        "roles_low": ["Soporte administrativo", "Roles altamente colaborativos sin autoridad"],
        "no_apt_high": ["Trabajo en equipo sin jerarquía", "Mediación de conflictos"],
        "no_apt_low": ["Dirección general", "Negociación de alto impacto"]
    },
    "Influencia": {
        "code": "I", "icon": "✨",
        "desc": "Entusiasmo, persuasión, optimismo y relaciones.",
        "color": "#F39C12",
        "fort_high": [
            "Motiva e inspira a otros con facilidad.",
            "Excelente en networking y comunicación verbal.",
            "Crea entusiasmo en torno a ideas o productos."
        ],
        "risk_high": [
            "Puede priorizar popularidad sobre resultados.",
            "Dificultad para seguir procesos detallados.",
            "Impulsividad en decisiones."
        ],
        "fort_low": [
            "Comunicación más reflexiva y precisa.",
            "Menor necesidad de validación externa."
        ],
        "risk_low": [
            "Baja visibilidad en equipos grandes.",
            "Dificultad para vender ideas o influir."
        ],
        "recs_low": [
            "Practicar storytelling breve (1 minuto).",
            "Participar en reuniones con 1 idea clara por sesión."
        ],
        "roles_high": ["Ventas", "Marketing", "Relaciones Públicas", "Capacitación"],
        "roles_low": ["Análisis de datos", "Auditoría interna"],
        "no_apt_high": ["Roles solitarios con mínima interacción"],
        "no_apt_low": ["Comunicación corporativa", "Liderazgo inspiracional"]
    },
    "Estabilidad": {
        "code": "S", "icon": "🕊️",
        "desc": "Paciencia, lealtad, cooperación y consistencia.",
        "color": "#27AE60",
        "fort_high": [
            "Construye relaciones de confianza duraderas.",
            "Excelente en entornos estables y predecibles.",
            "Apoyo emocional constante al equipo."
        ],
        "risk_high": [
            "Resistencia al cambio repentino.",
            "Evita conflictos incluso cuando son necesarios.",
            "Dificultad para decir 'no'."
        ],
        "fort_low": [
            "Adaptabilidad rápida a nuevos entornos.",
            "Capacidad de desapego emocional funcional."
        ],
        "risk_low": [
            "Puede generar inseguridad en equipos que buscan estabilidad.",
            "Menor compromiso a largo plazo."
        ],
        "recs_low": [
            "Crear rutinas de conexión breve con el equipo (ej. check-in semanal).",
            "Practicar feedback amable pero directo."
        ],
        "roles_high": ["RR.HH.", "Soporte al cliente", "Operaciones", "Mentoría"],
        "roles_low": ["Startups en fase caótica", "Proyectos de transformación radical"],
        "no_apt_high": ["Entornos hipercompetitivos sin cooperación"],
        "no_apt_low": ["Soporte emocional", "Gestión de equipos estables"]
    },
    "Cumplimiento": {
        "code": "C", "icon": "🔍",
        "desc": "Precisión, análisis, calidad y seguimiento de normas.",
        "color": "#3498DB",
        "fort_high": [
            "Alta calidad en entregables y procesos.",
            "Ojo para detectar errores o inconsistencias.",
            "Toma decisiones basadas en datos."
        ],
        "risk_high": [
            "Perfeccionismo que retrasa entregas.",
            "Dificultad para actuar con información incompleta.",
            "Puede ser percibido como crítico o frío."
        ],
        "fort_low": [
            "Agilidad en entornos ambiguos.",
            "Flexibilidad para ajustar estándares si es necesario."
        ],
        "risk_low": [
            "Errores por descuido o falta de revisión.",
            "Dificultad en roles que exigen rigor técnico."
        ],
        "recs_low": [
            "Usar checklist simple para tareas críticas.",
            "Revisión cruzada con un par antes de entregar."
        ],
        "roles_high": ["Calidad", "Finanzas", "Legal", "Ingeniería", "Data Science"],
        "roles_low": ["Ideación abierta", "Roles sin procesos definidos"],
        "no_apt_high": ["Entornos caóticos sin reglas"],
        "no_apt_low": ["Control de calidad", "Cumplimiento normativo"]
    }
}

DIM_LIST = list(DIMENSIONES.keys())
DIM_CODES = [DIMENSIONES[d]["code"] for d in DIM_LIST]  # ['D', 'I', 'S', 'C']

# Frases DISC clásicas (28 grupos de 4)
DISC_ITEMS = [
    ("Soy directo/a y decidido/a.", "Me gusta entusiasmar a otros.", "Soy paciente y constante.", "Soy preciso/a y meticuloso/a."),
    ("Me gusta asumir el control.", "Soy sociable y comunicativo/a.", "Prefiero un ambiente estable y armonioso.", "Me gusta seguir reglas y procedimientos."),
    ("Soy competitivo/a y orientado/a a resultados.", "Soy optimista y expresivo/a.", "Soy un/a buen/a oyente.", "Me preocupo por los detalles y la exactitud."),
    ("Me gusta tomar decisiones rápidas.", "Disfruto trabajando en equipo y motivando.", "Soy cooperativo/a y servicial.", "Soy analítico/a y lógico/a."),
    ("Soy audaz y me gusta asumir riesgos.", "Soy entusiasta y carismático/a.", "Soy leal y confiable.", "Soy perfeccionista y organizado/a."),
    ("Soy firme y me gusta resolver problemas.", "Soy animado/a y creativo/a.", "Soy tranquilo/a y evito conflictos.", "Soy reflexivo/a y me gusta planificar."),
    ("Soy independiente y autosuficiente.", "Soy persuasivo/a y me gusta influir.", "Soy empático/a y comprensivo/a.", "Soy riguroso/a y me gusta la calidad.")
]

# Convertir a lista plana de 28 preguntas
QUESTIONS = []
for i, (d, i_, s, c) in enumerate(DISC_ITEMS):
    QUESTIONS.append({
        "key": f"Q{i+1}",
        "options": [d, i_, s, c],  # orden: D, I, S, C
        "dim_order": ["Dominancia", "Influencia", "Estabilidad", "Cumplimiento"]
    })

KEY2IDX = {q["key"]: i for i, q in enumerate(QUESTIONS)}

# ---------------------------------------------------------------
# Función de cálculo corregida
# ---------------------------------------------------------------
def compute_scores(answers: dict) -> dict:
    # Inicializar contadores
    scores = {d: 0 for d in DIM_LIST}
    counts = {d: 0 for d in DIM_LIST}
    
    for q in QUESTIONS:
        selected_idx = answers.get(q["key"])
        if selected_idx is not None and 0 <= selected_idx < 4:
            dim = q["dim_order"][selected_idx]
            scores[dim] += 1
            counts[dim] += 1
    
    # Normalizar a 0–100
    result = {}
    for d in DIM_LIST:
        if counts[d] > 0:
            result[d] = round((scores[d] / counts[d]) * 100, 1)
        else:
            result[d] = 0.0
    return result

# ---------------------------------------------------------------
# Vista de test corregida
# ---------------------------------------------------------------
def view_test():
    i = st.session_state.q_idx
    q = QUESTIONS[i]
    p = (i + 1) / len(QUESTIONS)
    st.progress(p, text=f"Progreso: {i+1}/{len(QUESTIONS)}")
    
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown(f"### Pregunta {i+1} de {len(QUESTIONS)}")
    st.markdown("Selecciona la frase que **MEJOR** te describe:")
    
    # Mostrar las 4 opciones con etiquetas claras
    option_labels = []
    for j, frase in enumerate(q["options"]):
        dim_name = q["dim_order"][j]
        code = DIMENSIONES[dim_name]["code"]
        icon = DIMENSIONES[dim_name]["icon"]
        option_labels.append(f"{icon} **{code} — {frase}**")
    
    prev = st.session_state.answers.get(q["key"])
    st.radio(
        "Elige una opción",
        options=range(4),
        format_func=lambda x: option_labels[x],
        index=prev if prev is not None else 0,
        key=f"resp_{q['key']}",
        label_visibility="collapsed",
        on_change=on_answer_change,
        args=(q["key"],),
    )
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------
# Callback de respuesta (sin cambios, pero aseguramos el índice)
# ---------------------------------------------------------------
def on_answer_change(qkey: str):
    st.session_state.answers[qkey] = st.session_state.get(f"resp_{qkey}")
    idx = KEY2IDX[qkey]
    if idx < len(QUESTIONS) - 1:
        st.session_state.q_idx = idx + 1
    else:
        st.session_state.stage = "resultados"
        st.session_state.fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    st.session_state._needs_rerun = True

# ---------------------------------------------------------------
# Auto-avance
# ---------------------------------------------------------------
def on_answer_change(qkey: str):
    st.session_state.answers[qkey] = st.session_state.get(f"resp_{qkey}")
    idx = KEY2IDX[qkey]
    if idx < len(QUESTIONS) - 1:
        st.session_state.q_idx = idx + 1
    else:
        st.session_state.stage = "resultados"
        st.session_state.fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    st.session_state._needs_rerun = True

# ---------------------------------------------------------------
# Gráficos
# ---------------------------------------------------------------
def plot_bar(res: dict):
    palette = ["#E74C3C", "#F39C12", "#27AE60", "#3498DB"]
    df = pd.DataFrame({"Dimensión": list(res.keys()), "Puntuación": list(res.values())}).sort_values("Puntuación")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df["Dimensión"], x=df["Puntuación"], orientation='h',
        marker=dict(color=palette[:len(df)]),
        text=[f"{v:.1f}" for v in df["Puntuación"]], textposition="outside"
    ))
    fig.update_layout(height=400, template="plotly_white",
                      xaxis=dict(range=[0, 105], title="Puntuación (0–100)"),
                      yaxis=dict(title=""))
    return fig

def gauge_plotly(value: float, title: str = "", color="#3498DB"):
    v = max(0, min(100, float(value)))
    bounds = [0, 25, 40, 60, 75, 100]
    colors = ["#fde2e1", "#fff0c2", "#e9f2fb", "#e7f6e8", "#d9f2db"]
    vals = [bounds[i+1]-bounds[i] for i in range(len(bounds)-1)]
    fig = go.Figure()
    fig.add_trace(go.Pie(
        values=vals, hole=0.6, rotation=180, direction="clockwise",
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
# Exportar PDF / HTML
# ---------------------------------------------------------------
def pdf_semicircle(ax, value, cx=0.5, cy=0.5, r=0.45):
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

def build_pdf(res: dict, fecha: str) -> bytes:
    buf = BytesIO()
    with PdfPages(buf) as pdf:
        # Portada
        fig = plt.figure(figsize=(8.27, 11.69))
        ax = fig.add_axes([0,0,1,1]); ax.axis('off')
        ax.text(.5, .95, "Informe Test DISC — Contexto Laboral", ha='center', fontsize=20, fontweight='bold')
        ax.text(.5, .92, f"Fecha: {fecha}", ha='center', fontsize=11)
        # KPIs
        avg = np.mean(list(res.values()))
        top = max(res, key=res.get)
        def card(ax, x,y,w,h,title,val):
            from matplotlib.patches import FancyBboxPatch
            r = FancyBboxPatch((x,y), w,h, boxstyle="round,pad=0.012,rounding_size=0.018",
                               edgecolor="#dddddd", facecolor="#ffffff")
            ax.add_patch(r)
            ax.text(x+w*0.06, y+h*0.60, title, fontsize=10, color="#333")
            ax.text(x+w*0.06, y+h*0.25, f"{val}", fontsize=20, fontweight='bold')
        Y0 = .82; H = .10; W = .40; GAP = .02
        card(ax, .06, Y0, W, H, "Promedio (0–100)", f"{avg:.1f}")
        card(ax, .54, Y0, W, H, "Dimensión destacada", f"{top}")
        # Medidores
        dims = list(res.keys())
        for i, d in enumerate(dims):
            axg = fig.add_axes([.12 + i*.22, .65, .18, .14]); axg.axis("off")
            pdf_semicircle(axg, res[d], cx=0.5, cy=0.0, r=0.9)
            axg.text(.5,-.35,f"{d}\n({res[d]:.1f})",ha="center",fontsize=9)
        pdf.savefig(fig, bbox_inches='tight'); plt.close(fig)
        # Análisis por dimensión
        for d in dims:
            score = res[d]; lvl, tag = level_label(score)
            f, r, recs, roles, not_apt, expl = dimension_profile(d, score)
            fig3 = plt.figure(figsize=(8.27,11.69)); ax3 = fig3.add_axes([0,0,1,1]); ax3.axis('off')
            ax3.text(.5,.95, f"{DIMENSIONES[d]['code']} — {d}", ha='center', fontsize=16, fontweight='bold')
            ax3.text(.5,.92, f"Puntuación: {score:.1f} · Nivel: {lvl} ({tag})", ha='center', fontsize=11)
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

def build_html(res: dict, fecha: str) -> bytes:
    rows = ""
    for d in DIM_LIST:
        lvl, tag = level_label(res[d])
        rows += f"<tr><td>{DIMENSIONES[d]['code']}</td><td>{d}</td><td>{res[d]:.1f}</td><td>{lvl}</td><td>{tag}</td></tr>"
    blocks = ""
    for d in DIM_LIST:
        score = res[d]; lvl, tag = level_label(score)
        f, r, recs, roles, not_apt, expl = dimension_profile(d, score)
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
    html = f"""<!doctype html>
<html><head><meta charset="utf-8" />
<title>Informe Test DISC Laboral</title>
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
<h1>Informe Test DISC — Contexto Laboral</h1>
<p>Fecha: <b>{fecha}</b></p>
<div class="kpi-grid">
  <div class="kpi"><div class="label">Promedio general (0–100)</div><div class="value">{np.mean(list(res.values())):.1f}</div></div>
  <div class="kpi"><div class="label">Dimensión destacada</div><div class="value">{max(res, key=res.get)}</div></div>
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
            📊 Test DISC — Evaluación Laboral
          </h1>
          <p class="tag" style="margin:0;">Fondo blanco · Texto negro · Diseño profesional y responsivo</p>
        </div>
        """, unsafe_allow_html=True
    )
    c1, c2 = st.columns([1.35, 1])
    with c1:
        st.markdown(
            """
            <div class="card">
              <h3 style="margin-top:0">¿Qué mide?</h3>
              <ul style="line-height:1.6">
                <li><b>D</b> Dominancia</li>
                <li><b>I</b> Influencia</li>
                <li><b>S</b> Estabilidad</li>
                <li><b>C</b> Cumplimiento</li>
              </ul>
              <p class="small">28 ítems · Autoavance · Duración estimada: <b>5–8 min</b>.</p>
            </div>
            """, unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            """
            <div class="card">
              <h3 style="margin-top:0">Cómo funciona</h3>
              <ol style="line-height:1.6">
                <li>1 pregunta por pantalla.</li>
                <li>Al elegir una opción, avanzas automáticamente.</li>
                <li>Resultados con análisis laboral: fortalezas, riesgos, roles sugeridos y más.</li>
              </ol>
            </div>
            """, unsafe_allow_html=True
        )
        if st.button("🚀 Iniciar evaluación", type="primary", use_container_width=True):
            st.session_state.stage = "test"
            st.session_state.q_idx = 0
            st.session_state.answers = {q["key"]: None for q in QUESTIONS}
            st.session_state.fecha = None
            st.rerun()

def view_test():
    i = st.session_state.q_idx
    q = QUESTIONS[i]
    dim = q["dim"]
    code = DIMENSIONES[dim]["code"]
    icon = DIMENSIONES[dim]["icon"]
    p = (i + 1) / len(QUESTIONS)
    st.progress(p, text=f"Progreso: {i+1}/{len(QUESTIONS)}")
    st.markdown(f"<div class='dim-title'>{icon} {code} — {dim}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='dim-desc'>{DIMENSIONES[dim]['desc']}</div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown(f"### {i+1}. {q['text']}")
    prev = st.session_state.answers.get(q["key"])
    prev_idx = None if prev is None else LIK_KEYS.index(prev) if prev in LIK_KEYS else 0
    st.radio(
        "Selecciona la opción que mejor te describe",
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
    avg = round(float(np.mean(list(res.values()))), 1)
    top = max(res, key=res.get)
    st.markdown(
        f"""
        <div class="card">
          <h1 style="margin:0 0 6px 0; font-size:clamp(2.2rem,3.8vw,3rem); font-weight:900;">📊 Informe Test DISC — Resultados Laborales</h1>
          <p class="small" style="margin:0;">Fecha: <b>{st.session_state.fecha}</b></p>
        </div>
        """, unsafe_allow_html=True
    )
    st.markdown("<div class='kpi-grid'>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi'><div class='label'>Promedio general (0–100)</div><div class='value'>{avg:.1f}</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi'><div class='label'>Dimensión destacada</div><div class='value'>{top}</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("📊 Puntuaciones por dimensión")
    st.plotly_chart(plot_bar(res), use_container_width=True)
    st.markdown("---")
    st.subheader("📋 Resumen de resultados")
    tabla = pd.DataFrame({
        "Código": [DIMENSIONES[d]["code"] for d in DIM_LIST],
        "Dimensión": DIM_LIST,
        "Puntuación": [f"{res[d]:.1f}" for d in DIM_LIST],
        "Nivel": [level_label(res[d])[0] for d in DIM_LIST],
        "Etiqueta": [level_label(res[d])[1] for d in DIM_LIST],
    })
    st.dataframe(tabla, use_container_width=True, hide_index=True)
    st.markdown("---")
    st.subheader("🔍 Análisis por dimensión (laboral)")
    pastel_class = {
        "Dominancia": "pastel-D",
        "Influencia": "pastel-I",
        "Estabilidad": "pastel-S",
        "Cumplimiento": "pastel-C",
    }
    for d in DIM_LIST:
        score = res[d]
        lvl, tag = level_label(score)
        f, r, recs, roles, not_apt, expl = dimension_profile(d, score)
        icon = DIMENSIONES[d]["icon"]
        code = DIMENSIONES[d]["code"]
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
    st.subheader("📥 Exportar informe")
    if HAS_MPL:
        pdf_bytes = build_pdf(res, st.session_state.fecha)
        st.download_button(
            "⬇️ Descargar PDF (con medidores)",
            data=pdf_bytes,
            file_name="Informe_DISC_Laboral.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary"
        )
    else:
        html_bytes = build_html(res, st.session_state.fecha)
        st.download_button(
            "⬇️ Descargar Reporte (HTML) — Imprime como PDF",
            data=html_bytes,
            file_name="Informe_DISC_Laboral.html",
            mime="text/html",
            use_container_width=True,
            type="primary"
        )
        st.caption("Instala matplotlib para obtener el PDF directo con medidores.")
    st.markdown("---")
    if st.button("🔄 Nueva evaluación", type="primary", use_container_width=True):
        st.session_state.stage = "inicio"
        st.session_state.q_idx = 0
        st.session_state.answers = {q["key"]: None for q in QUESTIONS}
        st.session_state.fecha = None
        st.rerun()

# ---------------------------------------------------------------
# FLUJO PRINCIPAL
# ---------------------------------------------------------------
if st.session_state.stage == "inicio":
    view_inicio()
elif st.session_state.stage == "test":
    view_test()
else:
    if st.session_state.fecha is None:
        st.session_state.fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    view_resultados()

if st.session_state._needs_rerun:
    st.session_state._needs_rerun = False
    st.rerun()

