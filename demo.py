import streamlit as st
from typing import Dict, List

# ============================================================
# Configuración general de la app
# ============================================================
st.set_page_config(
    page_title="EPQR-A | Evaluación Operativa",
    page_icon="🧪",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ============================================================
# Estilos visuales (tailwind-like feeling, tarjetas suaves)
# ============================================================
st.markdown("""
<style>
/* Ocultar sidebar */
[data-testid="stSidebar"] { display:none !important; }

/* Base */
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

/* Tarjeta principal */
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

/* Mini KPI box */
.kpi-box{
  background:#fff;
  border:1px solid #e5e7eb;
  border-radius:.75rem;
  padding:.75rem .9rem;
  box-shadow:0 10px 20px -6px rgba(0,0,0,.08);
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

/* Botones principales */
.btn-main{
  background:linear-gradient(90deg,#2563eb 0%,#4f46e5 100%);
  color:#fff;
  font-weight:600;
  text-align:center;
  width:100%;
  border-radius:.75rem;
  padding:.8rem 1rem;
  border:0;
  box-shadow:0 20px 24px -8px rgba(37,99,235,.4);
}
.btn-main[disabled]{
  filter:grayscale(1);
  opacity:.5;
  box-shadow:none;
}
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

/* Etiquetas de aptitud */
.tag-fit{
  font-size:.8rem;
  font-weight:600;
  display:inline-block;
  padding:.4rem .6rem;
  border-radius:.5rem;
  line-height:1.1;
}
.tag-fit-ok{
  background:#d1fae5;
  color:#065f46;
  border:1px solid #10b98140;
}
.tag-fit-mid{
  background:#fef3c7;
  color:#92400e;
  border:1px solid #facc1540;
}
.tag-fit-bad{
  background:#fee2e2;
  color:#991b1b;
  border:1px solid #ef444440;
}

/* Texto pequeño gris */
.muted{
  font-size:.8rem;
  color:#6b7280;
  line-height:1.4;
}

/* Bloque alternativo */
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
</style>
""", unsafe_allow_html=True)

# ============================================================
# --- Definición de preguntas y lógica psicométrica ----------
# ============================================================

# Preguntas EPQR-A (24 ítems). 1 = Sí, 0 = No
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
]

# A qué escala puntúa cada ítem según la versión que me diste:
# E = Extraversión (sociabilidad/asertividad)
# N = Neuroticismo / inestabilidad emocional (queremos bajo en planta)
# P = Psicoticismo / dureza / impulsividad (muy alto puede ser riesgo disciplina)
# S = Sinceridad / conformidad social / deseabilidad social
CATEGORIES = [
    "N", "E", "P", "E", "S", "P", "S", "P", "N", "S",
    "N", "P", "E", "N", "E", "P", "S", "N", "S", "E",
    "N", "P", "E", "S"
]

# Rangos esperados por cargo en planta productiva
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
# --- Inicialización de estado en session_state --------------
# ============================================================
def init_state():
    if "phase" not in st.session_state:
        # phase: 'role' | 'candidate' | 'test' | 'result'
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
        # guardamos respuesta binaria 0/1 por índice de pregunta
        st.session_state.answers = {i: None for i in range(len(QUESTIONS))}

    if "scores" not in st.session_state:
        st.session_state.scores = {"E": 0, "N": 0, "P": 0, "S": 0}

    if "final_report" not in st.session_state:
        st.session_state.final_report = None

    # para auto-rerun después de seleccionar Sí/No
    if "_needs_rerun" not in st.session_state:
        st.session_state._needs_rerun = False


init_state()


# ============================================================
# --- Utilidades de cálculo ---------------------------------
# ============================================================
def compute_scores(answers: Dict[int, int]) -> Dict[str, int]:
    """
    Calcula puntajes E, N, P, S:
      - Para E y N sumamos 'Sí' (1) directo.
      - Para P y S aplicamos inversión que venías usando:
        value = 1 si respuesta fue "No" (0), value = 0 si respuesta fue "Sí" (1).
        (Interpretación: control de impulsividad / adherencia normativa).
    """
    scores = {"E": 0, "N": 0, "P": 0, "S": 0}
    for idx, cat in enumerate(CATEGORIES):
        ans = answers.get(idx)
        if ans is None:
            continue
        if cat in ["P", "S"]:
            # invertido
            val = 1 if ans == 0 else 0
            scores[cat] += val
        else:
            # directo
            scores[cat] += ans
    return scores


def evaluate_fit_for_job(scores: Dict[str, int], profile: dict):
    """
    Compara puntajes del candidato contra rangos exigidos por un cargo.
    Retorna nivel de ajuste y observaciones.
    Niveles:
      APTO = cumple todos los rangos
      RIESGO PARCIAL = sólo 1 desajuste
      NO APTO DIRECTO = 2 o más desajustes
    """
    req = profile["requirements"]
    issues = []
    for scale in ["E", "N", "P", "S"]:
        val = scores[scale]
        mn = req[scale]["min"]
        mx = req[scale]["max"]
        if val < mn:
            issues.append(f"{scale} bajo (requiere ≥{mn}, obtuvo {val})")
        elif val > mx:
            issues.append(f"{scale} alto (requiere ≤{mx}, obtuvo {val})")

    if len(issues) == 0:
        level = "APTO"
    elif len(issues) == 1:
        level = "RIESGO PARCIAL"
    else:
        level = "NO APTO DIRECTO"

    return {"matchLevel": level, "issues": issues}


def build_final_report():
    """
    Calcula puntajes totales, evalúa cargo objetivo
    y además evalúa el ajuste a todos los cargos disponibles.
    Guarda todo en session_state.final_report.
    """
    scores = compute_scores(st.session_state.answers)
    st.session_state.scores = scores

    sel_job_key = st.session_state.selected_job
    sel_profile = JOB_PROFILES[sel_job_key]

    # ajuste al cargo elegido
    fit_selected = evaluate_fit_for_job(scores, sel_profile)

    # evaluación de TODOS los cargos (para movilidad interna)
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
# --- Callbacks de navegación / acciones ---------------------
# ============================================================
def select_job(job_key: str):
    st.session_state.selected_job = job_key
    st.session_state.phase = "candidate"


def start_test_if_ready():
    if st.session_state.candidate_name and st.session_state.evaluator_email:
        st.session_state.phase = "test"
        st.session_state.q_idx = 0
        # reset respuestas por si venían de antes
        st.session_state.answers = {i: None for i in range(len(QUESTIONS))}


def answer_question(answer_val: int):
    """
    answer_val: 1 = Sí, 0 = No
    Guarda respuesta, avanza de pregunta o finaliza cálculo.
    """
    idx = st.session_state.q_idx
    st.session_state.answers[idx] = answer_val

    # última pregunta?
    if idx < len(QUESTIONS) - 1:
        st.session_state.q_idx = idx + 1
        st.session_state._needs_rerun = True
    else:
        # calcular resultados finales y pasar a 'result'
        build_final_report()
        st.session_state.phase = "result"
        st.session_state._needs_rerun = True


def reset_all():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_state()


# ============================================================
# --- Render de cada fase -----------------------------------
# ============================================================
def render_phase_role():
    st.markdown(
        """
        <div class="card-header" style="margin-bottom:1rem;">
            <div style="display:flex;flex-direction:column;gap:.25rem;">
                <h1 style="font-size:1.25rem;">Test EPQR-A · Selección Operativa</h1>
                <div class="badge-pill">Foco en cargos productivos</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="card">
            <p style="margin-top:0;color:#374151;font-size:.9rem;line-height:1.4;">
            El objetivo es estimar ajuste conductual y emocional del candidato para
            un cargo específico de planta productiva. El resultado final clasifica
            en <b>APTO</b>, <b>RIESGO PARCIAL</b> o <b>NO APTO DIRECTO</b>.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="card" style="margin-top:1rem;">
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
                "Evaluar este cargo",
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
        <div class="card-header" style="margin-bottom:1rem;">
            <div style="display:flex;flex-direction:column;gap:.25rem;">
                <h2 style="font-size:1.1rem;">Datos del Candidato</h2>
                <div class="badge-pill">{profile["title"]}</div>
            </div>
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
            Esta información es confidencial y será utilizada sólo para fines
            de selección y/o reubicación interna.
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
        st.experimental_rerun()


def render_phase_test():
    idx = st.session_state.q_idx
    total = len(QUESTIONS)
    pct = round(((idx + 1) / total) * 100)

    # Encabezado progreso
    st.markdown(
        f"""
        <div class="card-header">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:.5rem;">
                <div style="color:#fff;">
                    <h3 style="font-size:1rem;margin:0 0 .25rem 0;font-weight:600;">
                        EPQR-A · {JOB_PROFILES[st.session_state.selected_job]["title"]}
                    </h3>
                    <div style="font-size:.8rem;opacity:.9;">
                        Pregunta {idx+1} de {total}
                    </div>
                </div>
                <div class="badge-pill" style="font-size:.7rem;">
                    {pct}%
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Barra de progreso visual
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

    # Pregunta actual
    st.markdown(
        f"""
        <div class="card" style="margin-top:1rem;">
            <div style="font-size:1rem;color:#111827;line-height:1.4;margin-bottom:1rem;font-weight:500;">
                {QUESTIONS[idx]}
            </div>
        """,
        unsafe_allow_html=True
    )

    c_yes, c_no = st.columns(2)
    with c_yes:
        st.button(
            "Sí",
            key=f"yes_{idx}",
            help="Marcar 'Sí' y avanzar",
            on_click=answer_question,
            args=(1,),
            use_container_width=True
        )
    with c_no:
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
                    Responda con honestidad. Sus respuestas ayudan a evaluar
                    estabilidad emocional bajo presión, apego a normas y
                    ajuste conductual al rol.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_phase_result():
    rep = st.session_state.final_report
    if rep is None:
        st.write("No hay resultados calculados.")
        return

    scores = rep["scores"]
    fit_selected = rep["fit_selected"]
    all_fits = rep["all_fits"]

    # header éxito
    st.markdown(
        """
        <div class="card-header" style="text-align:center;">
            <div style="margin:0 auto;">
                <div style="
                    width:3.5rem;height:3.5rem;
                    background:#10b981;
                    border-radius:999px;
                    display:flex;align-items:center;justify-content:center;
                    margin:0 auto .75rem auto;
                    box-shadow:0 20px 24px -8px rgba(16,185,129,.4);
                ">
                    <svg xmlns="http://www.w3.org/2000/svg" style="color:white;width:1.5rem;height:1.5rem;" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                    </svg>
                </div>
                <h2 style="font-size:1.25rem;font-weight:600;line-height:1.2;margin:0;">
                    Test Completado
                </h2>
                <div style="font-size:.8rem;opacity:.9;">
                    Informe de ajuste conductual y emocional
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # resumen candidato
    st.markdown(
        f"""
        <div class="card">
            <h3 style="font-size:1rem;margin:0 0 .75rem 0;font-weight:600;color:#111827;">
                Datos generales
            </h3>
            <div class="kpi-box" style="margin-bottom:1rem;">
                <div class="kpi-label">Candidato</div>
                <div class="kpi-value" style="font-size:1rem;">{rep["candidate_name"]}</div>
            </div>
            <div class="kpi-box" style="margin-bottom:1rem;">
                <div class="kpi-label">Evaluador</div>
                <div class="kpi-value" style="font-size:1rem;">{rep["evaluator_email"]}</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-label">Cargo evaluado</div>
                <div class="kpi-value" style="font-size:1rem;">{rep["selected_job_title"]}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # resultado ajuste al cargo elegido
    matchLevel = fit_selected["matchLevel"]
    if matchLevel == "APTO":
        tag_class = "tag-fit tag-fit-ok"
    elif matchLevel == "RIESGO PARCIAL":
        tag_class = "tag-fit tag-fit-mid"
    else:
        tag_class = "tag-fit tag-fit-bad"

    issues_list = ""
    if fit_selected["issues"]:
        issues_list += "<ul style='margin:.5rem 0 0 1rem;padding:0;font-size:.8rem;color:#4b5563;line-height:1.4;'>"
        for it in fit_selected["issues"]:
            issues_list += f"<li>{it}</li>"
        issues_list += "</ul>"
    else:
        issues_list += "<div class='muted' style='margin-top:.5rem;'>Sin observaciones críticas.</div>"

    st.markdown(
        f"""
        <div class="card">
            <h3 style="font-size:1rem;margin:0 0 .75rem 0;font-weight:600;color:#111827;">
                Ajuste al cargo objetivo
            </h3>
            <div style="display:flex;align-items:center;gap:.5rem;flex-wrap:wrap;">
                <div class="{tag_class}">{matchLevel}</div>
                <div class="muted" style="font-size:.8rem;">
                    Clasificación basada en rangos conductuales esperados para el rol.
                </div>
            </div>
            {issues_list}
        </div>
        """,
        unsafe_allow_html=True
    )

    # puntajes EPQR-A
    st.markdown(
        f"""
        <div class="card">
            <h3 style="font-size:1rem;margin:0 0 .75rem 0;font-weight:600;color:#111827;">
                Perfil conductual medido
            </h3>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;">
                <div class="kpi-box">
                    <div class="kpi-label">E (Sociabilidad / Asertividad)</div>
                    <div class="kpi-value">{scores["E"]}</div>
                </div>
                <div class="kpi-box">
                    <div class="kpi-label">N (Inestabilidad emocional)</div>
                    <div class="kpi-value">{scores["N"]}</div>
                </div>
                <div class="kpi-box">
                    <div class="kpi-label">P (Impulsividad / Dureza)</div>
                    <div class="kpi-value">{scores["P"]}</div>
                </div>
                <div class="kpi-box">
                    <div class="kpi-label">S (Apego a normas / Honestidad percibida)</div>
                    <div class="kpi-value">{scores["S"]}</div>
                </div>
            </div>
            <div class="muted" style="margin-top:1rem;">
                • N alto = más tensión emocional; idealmente buscamos N bajo (0-3).<br/>
                • S alto = mayor adherencia percibida a normas y sinceridad en contextos laborales.<br/>
                • P muy alto puede indicar riesgo de impulsividad o conductas límite, pero P demasiado bajo puede implicar excesiva docilidad (no confronta desviaciones).<br/>
                • E orienta sociabilidad y comunicación (útil p.ej. en supervisión o logística).
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Otros cargos donde calza
    st.markdown(
        """
        <div class="card">
            <h3 style="font-size:1rem;margin:0 0 .75rem 0;font-weight:600;color:#111827;">
                Ajuste potencial en otros cargos productivos
            </h3>
        """,
        unsafe_allow_html=True
    )

    # sugerencias: mostramos APTO y RIESGO PARCIAL
    suggested = [
        f for f in all_fits
        if f["matchLevel"] in ["APTO", "RIESGO PARCIAL"]
    ]

    if len(suggested) == 0:
        st.markdown(
            """
            <div class="alt-block">
                <h4>Sin alternativa inmediata clara</h4>
                <p>Se sugiere entrevista directa y observación en terreno.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        for fit in suggested:
            if fit["matchLevel"] == "APTO":
                small_tag = "tag-fit tag-fit-ok"
            elif fit["matchLevel"] == "RIESGO PARCIAL":
                small_tag = "tag-fit tag-fit-mid"
            else:
                small_tag = "tag-fit tag-fit-bad"

            issues_html = ""
            if fit["issues"]:
                issues_html += "<ul style='margin:.5rem 0 0 1rem;padding:0;font-size:.75rem;color:#4b5563;line-height:1.4;'>"
                for it in fit["issues"]:
                    issues_html += f"<li>{it}</li>"
                issues_html += "</ul>"

            st.markdown(
                f"""
                <div class="alt-block">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:.5rem;">
                        <div>
                            <h4 style="margin-bottom:.25rem;">{fit["title"]}</h4>
                            <p style="margin:0;">{fit["desc"]}</p>
                        </div>
                        <div class="{small_tag}" style="font-size:.7rem;">{fit["matchLevel"]}</div>
                    </div>
                    {issues_html}
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("</div>", unsafe_allow_html=True)

    # Próximos pasos + botón reinicio
    st.markdown(
        """
        <div class="card">
            <h3 style="font-size:1rem;margin:0 0 .75rem 0;font-weight:600;color:#111827;">
                Próximos pasos sugeridos
            </h3>
            <div class="muted">
                • RR.HH. y jefatura directa revisan el ajuste y las observaciones.<br/>
                • En caso de "RIESGO PARCIAL", profundizar en entrevista conductual.<br/>
                • Validar referencias laborales previas y asistencia / disciplina.<br/>
                • Este test NO reemplaza prueba técnica ni evaluación médica.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.button(
        "Realizar nuevo test",
        on_click=reset_all,
        use_container_width=True,
        key="btn_reset_all",
    )


# ============================================================
# --- Render principal según fase ----------------------------
# ============================================================
if st.session_state.phase == "role":
    render_phase_role()
elif st.session_state.phase == "candidate":
    render_phase_candidate()
elif st.session_state.phase == "test":
    render_phase_test()
elif st.session_state.phase == "result":
    render_phase_result()
else:
    st.write("Estado inválido. Reiniciando…")
    reset_all()

# Rerun si se marcó respuesta (para que cambie de pregunta sin 2 clics)
if st.session_state._needs_rerun:
    st.session_state._needs_rerun = False
    st.experimental_rerun()
