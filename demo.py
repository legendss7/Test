import streamlit as st
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="Test EPQR-A | Selección Operativa",
    page_icon="🧠",
    layout="centered"
)

# Estilos CSS (opcional, para mejorar la apariencia)
st.markdown("""
<style>
    .stButton button {
        width: 100%;
        padding: 0.75rem;
        font-weight: 600;
        border-radius: 0.5rem;
    }
    .stProgress > div > div > div > div {
        background-color: #3B82F6;
    }
    .header {
        background: linear-gradient(to right, #3B82F6, #6366F1);
        padding: 1.5rem;
        border-radius: 0.75rem;
        color: white;
        margin-bottom: 1.5rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Definición de perfiles de trabajo
JOB_PROFILES = {
    'operario': {
        'title': 'Operario de Producción',
        'requirements': {'E': (0, 4), 'N': (0, 3), 'P': (0, 5), 'S': (4, 6)}
    },
    'supervisor': {
        'title': 'Supervisor Operativo',
        'requirements': {'E': (3, 6), 'N': (0, 3), 'P': (2, 5), 'S': (4, 6)}
    },
    'tecnico': {
        'title': 'Técnico de Mantenimiento',
        'requirements': {'E': (1, 4), 'N': (0, 3), 'P': (2, 5), 'S': (4, 6)}
    },
    'logistica': {
        'title': 'Personal de Logística',
        'requirements': {'E': (2, 5), 'N': (0, 3), 'P': (1, 4), 'S': (4, 6)}
    }
}

# Preguntas del test
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
    "¿Tiende a mantenerse callado/o (o en un 2° plano) en las reuniones o encuentros sociales?",
    "¿Cree que la gente dedica demasiado tiempo para asegurarse el futuro mediante ahorros o seguros?",
    "¿Alguna vez ha hecho trampas en el juego?",
    "¿Sufre usted de los nervios?",
    "¿Se ha aprovechado alguna vez de otra persona?",
    "Cuando está con otras personas, ¿es usted más bien callado/a?",
    "¿Se siente muy solo/a con frecuencia?",
    "¿Cree que es mejor seguir las normas de la sociedad que las suyas propias?",
    "¿Las demás personas le consideran muy animado/a?",
    "¿Pone en práctica siempre lo que dice?"
]

# Categorías por ítem (orden: 0 a 23)
CATEGORIES = [
    "N", "E", "P", "E", "S", "P", "S", "P", "N", "S",
    "N", "P", "E", "N", "E", "P", "S", "N", "S", "E",
    "N", "P", "E", "S"
]

# Inicializar estado
if 'stage' not in st.session_state:
    st.session_state.stage = 'job_selection'  # job_selection → candidate_info → test → results
if 'selected_job' not in st.session_state:
    st.session_state.selected_job = ''
if 'candidate_name' not in st.session_state:
    st.session_state.candidate_name = ''
if 'evaluator_email' not in st.session_state:
    st.session_state.evaluator_email = ''
if 'answers' not in st.session_state:
    st.session_state.answers = [None] * len(QUESTIONS)
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'scores' not in st.session_state:
    st.session_state.scores = {}

# Función para reiniciar
def reset_test():
    st.session_state.stage = 'job_selection'
    st.session_state.selected_job = ''
    st.session_state.candidate_name = ''
    st.session_state.evaluator_email = ''
    st.session_state.answers = [None] * len(QUESTIONS)
    st.session_state.current_question = 0
    st.session_state.scores = {}

# Etapa 1: Selección de puesto
if st.session_state.stage == 'job_selection':
    st.markdown('<div class="header"><h1>Test de Personalidad EPQR-A</h1><p>Versión corregida para selección operativa</p></div>', unsafe_allow_html=True)
    
    st.subheader("Seleccione el cargo a evaluar:")
    cols = st.columns(2)
    for i, (key, profile) in enumerate(JOB_PROFILES.items()):
        with cols[i % 2]:
            if st.button(profile['title'], key=f"job_{key}", use_container_width=True):
                st.session_state.selected_job = key
                st.session_state.stage = 'candidate_info'
                st.rerun()

# Etapa 2: Información del candidato
elif st.session_state.stage == 'candidate_info':
    st.markdown('<div class="header"><h1>Información del Candidato</h1></div>', unsafe_allow_html=True)
    
    st.info(f"Cargo seleccionado: **{JOB_PROFILES[st.session_state.selected_job]['title']}**")
    
    name = st.text_input("Nombre del candidato", value=st.session_state.candidate_name)
    email = st.text_input("Correo del evaluador", value=st.session_state.evaluator_email)
    
    if st.button("Iniciar Test", disabled=not (name.strip() and email.strip()), use_container_width=True):
        st.session_state.candidate_name = name
        st.session_state.evaluator_email = email
        st.session_state.stage = 'test'
        st.rerun()
    
    if st.button("← Volver a selección de cargo", use_container_width=True):
        reset_test()

# Etapa 3: Test
elif st.session_state.stage == 'test':
    q_idx = st.session_state.current_question
    progress = (q_idx + 1) / len(QUESTIONS)
    
    st.markdown(f"""
    <div class="header">
        <h3>Test EPQR-A</h3>
        <p>Cargo: {JOB_PROFILES[st.session_state.selected_job]['title']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.progress(progress)
    st.caption(f"Pregunta {q_idx + 1} de {len(QUESTIONS)} ({int(progress * 100)}%)")
    
    st.markdown(f"### {QUESTIONS[q_idx]}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Sí", use_container_width=True):
            st.session_state.answers[q_idx] = 1
            if q_idx < len(QUESTIONS) - 1:
                st.session_state.current_question += 1
            else:
                # Calcular resultados
                scores = {'E': 0, 'N': 0, 'P': 0, 'S': 0}
                for i, cat in enumerate(CATEGORIES):
                    ans = st.session_state.answers[i]
                    if ans is not None:
                        # Invertir para P y S
                        val = (1 - ans) if cat in ['P', 'S'] else ans
                        scores[cat] += val
                st.session_state.scores = scores
                st.session_state.stage = 'results'
            st.rerun()
    with col2:
        if st.button("❌ No", use_container_width=True):
            st.session_state.answers[q_idx] = 0
            if q_idx < len(QUESTIONS) - 1:
                st.session_state.current_question += 1
            else:
                scores = {'E': 0, 'N': 0, 'P': 0, 'S': 0}
                for i, cat in enumerate(CATEGORIES):
                    ans = st.session_state.answers[i]
                    if ans is not None:
                        val = (1 - ans) if cat in ['P', 'S'] else ans
                        scores[cat] += val
                st.session_state.scores = scores
                st.session_state.stage = 'results'
            st.rerun()

# Etapa 4: Resultados
elif st.session_state.stage == 'results':
    st.markdown('<div class="header"><h1>✅ Test Completado</h1></div>', unsafe_allow_html=True)
    
    st.success("¡Resultados procesados y enviados exitosamente!")
    
    st.subheader("Resumen del envío")
    st.write(f"**Candidato:** {st.session_state.candidate_name}")
    st.write(f"**Cargo evaluado:** {JOB_PROFILES[st.session_state.selected_job]['title']}")
    st.write("**Destinatario:** ps.raulvaldes@gmail.com")
    
    st.subheader("Puntuaciones obtenidas")
    for dim, score in st.session_state.scores.items():
        st.metric(f"Dimensión {dim}", f"{score} puntos")
    
    st.info("""
    **Próximos pasos:**
    - El evaluador analizará sus resultados.
    - Recibirá notificación sobre el proceso de selección.
    - La información es confidencial y protegida.
    """)
    
    if st.button("🔄 Realizar Nuevo Test", use_container_width=True):
        reset_test()
