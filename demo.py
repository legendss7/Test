import streamlit as st
import uuid
from dataclasses import dataclass, field
from typing import Dict, List


# =========================================================
# 1. MODELO DE DATOS
# =========================================================

@dataclass
class ItemDISC:
    traits: List[str]                 # las 4 frases/opciones del bloque
    map_mas: Dict[int, str]           # índice -> dimensión (+1)
    map_menos: Dict[int, str]         # índice -> dimensión (-1)
    dimension_group: str              # "D","I","S","C" o mixto, para ordenar secciones
    key: str = field(default_factory=lambda: str(uuid.uuid4()))


# =========================================================
# 2. BANCO DE ITEMS
# =========================================================
# IMPORTANTE:
# - Debes reemplazar/ajustar las frases y el mapeo según tu PDF real.
# - dimension_group: te permite agrupar/ordenar las preguntas por bloques de dimensión
#   para análisis posterior. Ej: todas las de Dominancia primero, luego Influencia, etc.
#
# Ejemplo basado en la estructura DISC descrita en tu material:
# D = Dominancia (directo/a, decidido/a)
# I = Influencia (entusiasta, sociable)
# S = Estabilidad (tranquilo/a, paciente)
# C = Cumplimiento / Perfeccionista (preciso/a, cuidadoso/a, control de calidad) :contentReference[oaicite:1]{index=1}
#
# Nota: vamos a generar una lista larga (28 ítems, placeholder). Tú puedes ampliar
# hasta 100 ítems repitiendo el patrón, o reemplazar con todos tus ítems reales.

BASE_ITEMS = [
    ItemDISC(
        traits=[
            "Entusiasta / Extrovertido(a)",
            "Rápido(a) / Impulsivo(a)",
            "Lógico(a) / Cuida los detalles",
            "Apacible / Tranquilo(a)"
        ],
        map_mas={0: "I", 1: "D", 2: "C", 3: "S"},
        map_menos={0: "S", 1: "C", 2: "I", 3: "D"},
        dimension_group="I"  # este bloque lo dejamos en grupo I (Influencia) a modo ejemplo
    ),
    ItemDISC(
        traits=[
            "Decidido(a) / Audaz",
            "Cauteloso(a) / Analítico(a)",
            "Receptivo(a) / Encantador(a)",
            "Bondadoso(a) / Complaciente"
        ],
        map_mas={0: "D", 1: "C", 2: "I", 3: "S"},
        map_menos={0: "S", 1: "I", 2: "C", 3: "D"},
        dimension_group="D"
    ),
    ItemDISC(
        traits=[
            "Amigable / Preciso(a)",
            "Franco(a)",
            "Tranquilo(a)",
            "Paciente / Pacificador(a)"
        ],
        map_mas={0: "C", 1: "D", 2: "S", 3: "I"},
        map_menos={0: "D", 1: "S", 2: "I", 3: "C"},
        dimension_group="C"
    ),
    ItemDISC(
        traits=[
            "Elocuente",
            "Controlado(a) / Tolerante",
            "Decisivo(a)",
            "Reservado(a) / Resuelto(a)"
        ],
        map_mas={0: "I", 1: "S", 2: "D", 3: "C"},
        map_menos={0: "C", 1: "D", 2: "S", 3: "I"},
        dimension_group="D"
    ),
    ItemDISC(
        traits=[
            "Atrevido(a) / Firme",
            "Concienzudo(a) / Metódico(a)",
            "Comunicativo(a)",
            "Moderado(a) / Independiente"
        ],
        map_mas={0: "D", 1: "C", 2: "I", 3: "S"},
        map_menos={0: "S", 1: "I", 2: "C", 3: "D"},
        dimension_group="C"
    ),
    ItemDISC(
        traits=[
            "Ameno(a) / Ingenioso(a)",
            "Investigador(a) / Acepta riesgos",
            "De trato fácil / Compasivo(a)",
            "Inquieto(a) / Habla directo"
        ],
        map_mas={0: "I", 1: "D", 2: "S", 3: "C"},
        map_menos={0: "C", 1: "S", 2: "D", 3: "I"},
        dimension_group="I"
    ),
    ItemDISC(
        traits=[
            "Expresivo(a)",
            "Cuidadoso(a) / Obediente",
            "Dominante / Ideas firmes",
            "Sensible / Generoso(a)"
        ],
        map_mas={0: "I", 1: "C", 2: "D", 3: "S"},
        map_menos={0: "C", 1: "D", 2: "S", 3: "I"},
        dimension_group="S"
    ),
]

# Para efectos prácticos vamos a construir una lista más larga
# copiando este set hasta llegar a ~28 items.
ITEMS_RAW = []
while len(ITEMS_RAW) < 28:
    template = BASE_ITEMS[len(ITEMS_RAW) % len(BASE_ITEMS)]
    # duplicamos con nueva key
    ITEMS_RAW.append(
        ItemDISC(
            traits=template.traits.copy(),
            map_mas=template.map_mas.copy(),
            map_menos=template.map_menos.copy(),
            dimension_group=template.dimension_group,
        )
    )

# Ahora ordenamos todas las preguntas por dimension_group,
# para que primero salgan todas las D, luego I, luego S, luego C (o el orden que tú quieras).
DIM_ORDER = ["D", "I", "S", "C"]
ITEMS_SORTED = sorted(
    ITEMS_RAW,
    key=lambda it: (DIM_ORDER.index(it.dimension_group), it.key)
)


# =========================================================
# 3. ESTADO GLOBAL
# =========================================================

def init_state():
    if "stage" not in st.session_state:
        st.session_state.stage = "intro"  # intro -> test -> results
    if "current_idx" not in st.session_state:
        st.session_state.current_idx = 0   # índice de pregunta actual
    if "answers_mas" not in st.session_state:
        st.session_state.answers_mas = {}  # item_key -> idx opción MÁS
    if "answers_menos" not in st.session_state:
        st.session_state.answers_menos = {}  # item_key -> idx opción MENOS
    if "scores" not in st.session_state:
        st.session_state.scores = {"D": 0, "I": 0, "S": 0, "C": 0}
    if "profile" not in st.session_state:
        st.session_state.profile = {}
    if "nombre_participante" not in st.session_state:
        st.session_state.nombre_participante = ""


# =========================================================
# 4. CÁLCULO DISC
# =========================================================

def compute_scores():
    scores = {"D": 0, "I": 0, "S": 0, "C": 0}
    for item in ITEMS_SORTED:
        # MAS = suma +1 a la dimensión asociada
        if item.key in st.session_state.answers_mas:
            idx_mas = st.session_state.answers_mas[item.key]
            if idx_mas in item.map_mas:
                dim = item.map_mas[idx_mas]
                scores[dim] += 1
        # MENOS = resta 1 a la dimensión asociada
        if item.key in st.session_state.answers_menos:
            idx_menos = st.session_state.answers_menos[item.key]
            if idx_menos in item.map_menos:
                dim2 = item.map_menos[idx_menos]
                scores[dim2] -= 1
    return scores


def describe_high_dimension(dim: str) -> str:
    # Perfil "Perfeccionista" = C alto:
    # Persona metódica, precisa, orientada a calidad.
    # Busca estabilidad, normas claras, control de calidad
    # Puede tardar en decidir porque analiza todo
    # Valor para la organización: consistencia, rigor, control de errores. :contentReference[oaicite:2]{index=2}
    if dim == "D":
        return (
            "Dominancia: directo/a, decidido/a, orientado/a a resultados, "
            "empuja a la acción y asume riesgos. Bajo presión puede mostrarse "
            "impaciente o confrontacional."
        )
    if dim == "I":
        return (
            "Influencia: comunicativo/a, entusiasta, sociable, genera adhesión "
            "y motiva a otros. Bajo presión puede priorizar la aceptación social "
            "por sobre los detalles técnicos."
        )
    if dim == "S":
        return (
            "Estabilidad: paciente, leal, colaborador/a, busca armonía y "
            "cohesión del equipo. Bajo presión puede evitar el conflicto "
            "y resistir cambios bruscos."
        )
    if dim == "C":
        return (
            "Cumplimiento / Perfeccionista: metódico/a, preciso/a, cuidadoso/a "
            "con estándares y control de calidad. Prefiere entornos estables, "
            "normas claras y baja ambigüedad. Puede demorarse al decidir porque "
            "analiza toda la información y puede parecer crítico/a cuando ve "
            "errores, pero aporta rigor, seguridad y consistencia. :contentReference[oaicite:3]{index=3}"
        )
    return ""


def build_profile(scores: Dict[str, int]) -> Dict[str, str]:
    main_dim = max(scores, key=lambda k: scores[k])

    if main_dim == "C":
        fortalezas = [
            "Orientación extrema al detalle y la calidad.",
            "Respeto por normas y procedimientos.",
            "Confiable en tareas donde el error es costoso.",
        ]
        alertas = [
            "Puede mostrarse muy crítico/a frente a fallas. :contentReference[oaicite:4]{index=4}",
            "Puede tardar decisiones por sobreanálisis. :contentReference[oaicite:5]{index=5}",
            "Tolera mal la ambigüedad o cambios improvisados. :contentReference[oaicite:6]{index=6}",
        ]
        meta = (
            "Busca entornos estables, reglas claras, expectativas bien definidas "
            "y reconocimiento por la calidad objetiva del trabajo. :contentReference[oaicite:7]{index=7}"
        )
    elif main_dim == "D":
        fortalezas = [
            "Rapidez para decidir y ejecutar.",
            "Enfrenta obstáculos con determinación.",
            "Asume liderazgo en situaciones de presión."
        ]
        alertas = [
            "Puede ser percibido/a como agresivo/a o impaciente.",
            "Puede minimizar los detalles.",
            "Puede imponer su ritmo al resto."
        ]
        meta = "Necesita desafíos claros, autonomía y poder de decisión."
    elif main_dim == "I":
        fortalezas = [
            "Alta capacidad para motivar y persuadir.",
            "Sociable, genera redes y entusiasmo.",
            "Crea climas positivos."
        ]
        alertas = [
            "Puede evitar confrontaciones directas.",
            "Puede subestimar lo técnico/administrativo.",
            "Puede depender de aprobación externa."
        ]
        meta = "Ambiente dinámico, contacto constante con personas y reconocimiento social."
    else:  # S
        fortalezas = [
            "Estabilidad emocional, paciencia, confiabilidad.",
            "Lealtad y apoyo consistente al equipo.",
            "Mantiene procesos en el tiempo."
        ]
        alertas = [
            "Puede evitar conflictos necesarios.",
            "Puede resistirse a cambios bruscos.",
            "Puede sobrecargarse tratando de ayudar a todos."
        ]
        meta = "Ambientes previsibles, ritmos sostenibles y relaciones de confianza."

    return {
        "dimension_principal": main_dim,
        "descripcion": describe_high_dimension(main_dim),
        "fortalezas": "\n- " + "\n- ".join(fortalezas),
        "alertas": "\n- " + "\n- ".join(alertas),
        "lo_que_busca": meta,
    }


# =========================================================
# 5. VISTAS
# =========================================================

def page_intro():
    st.title("Evaluación de Perfil Conductual (DISC)")
    st.write(
        "Esta evaluación mide tu estilo conductual en cuatro dimensiones: "
        "D (Dominancia), I (Influencia), S (Estabilidad) y C (Cumplimiento / Perfeccionista). "
        "En cada bloque verás 4 descripciones de comportamiento. Debes elegir cuál te "
        "representa MÁS y cuál te representa MENOS."
    )
    st.write(
        "El resultado final genera un perfil con fortalezas, riesgos y condiciones de trabajo "
        "preferidas. Por ejemplo, el perfil 'Perfeccionista' (alto C) describe a alguien "
        "metódico, preciso, muy orientado al control de calidad, que busca estabilidad y "
        "normas claras y que puede tardar en decidir porque analiza toda la información. "
        "Aporta rigor, consistencia y seguridad en los procesos. :contentReference[oaicite:8]{index=8}"
    )

    st.text_input(
        "Tu nombre (para el informe final):",
        key="nombre_participante",
        placeholder="Ej: José Ignacio Taj-Taj",
    )

    if st.button("Comenzar ahora"):
        st.session_state.stage = "test"
        st.session_state.current_idx = 0


def page_question():
    total = len(ITEMS_SORTED)
    idx = st.session_state.current_idx
    item = ITEMS_SORTED[idx]

    # Info de progreso
    st.progress((idx + 1) / total)
    st.write(f"Pregunta {idx + 1} de {total}")
    st.caption(
        f"Bloque asociado a la dimensión {item.dimension_group} "
        f"(esto ayuda a análisis interno por tipo de rasgo)."
    )

    # Mostramos la pregunta dentro de un form
    # para capturar la respuesta y auto-avanzar
    form_key = f"form_{item.key}"
    with st.form(key=form_key, clear_on_submit=True):
        st.write(
            "Selecciona UNA opción como MÁS (la que más se parece a ti) "
            "y UNA opción como MENOS (la que menos se parece a ti)."
        )

        col1, col2 = st.columns(2)

        # default preseleccionado si ya respondió antes
        default_mas = st.session_state.answers_mas.get(item.key, None)
        default_menos = st.session_state.answers_menos.get(item.key, None)

        with col1:
            mas_choice = st.radio(
                "Más:",
                options=list(range(len(item.traits))),
                format_func=lambda i: item.traits[i],
                index=default_mas if default_mas is not None else 0,
                key=f"mas_{item.key}",
            )
        with col2:
            menos_choice = st.radio(
                "Menos:",
                options=list(range(len(item.traits))),
                format_func=lambda i: item.traits[i],
                index=default_menos if default_menos is not None else 1,
                key=f"menos_{item.key}",
            )

        submitted = st.form_submit_button("Siguiente ➜")

    # Después de submit, guardamos y avanzamos automáticamente
    if submitted:
        st.session_state.answers_mas[item.key] = mas_choice
        st.session_state.answers_menos[item.key] = menos_choice

        if st.session_state.current_idx < total - 1:
            # pasar a la siguiente pregunta
            st.session_state.current_idx += 1
        else:
            # si ya no quedan preguntas, calcular resultados
            st.session_state.scores = compute_scores()
            st.session_state.profile = build_profile(st.session_state.scores)
            st.session_state.stage = "results"

        st.rerun()  # rerender inmediato para mostrar la próxima pregunta


def page_results():
    st.title("Resultados del Perfil Conductual")

    nombre = st.session_state.nombre_participante or "Participante"
    scores = st.session_state.scores
    profile = st.session_state.profile

    st.subheader(f"Informe de {nombre}")

    st.markdown(
        f"**Puntajes netos DISC (Más suma / Menos resta):**\n\n"
        f"- D (Dominancia): {scores['D']}\n"
        f"- I (Influencia): {scores['I']}\n"
        f"- S (Estabilidad): {scores['S']}\n"
        f"- C (Cumplimiento / Perfeccionista): {scores['C']}\n"
    )

    st.subheader("Tu estilo principal")
    st.markdown(
        f"Dimensión predominante: **{profile['dimension_principal']}**\n\n"
        f"{profile['descripcion']}"
    )

    st.subheader("Fortalezas que aportas")
    st.markdown(profile["fortalezas"])

    st.subheader("Alertas / Riesgos potenciales")
    st.markdown(profile["alertas"])

    st.subheader("Condiciones que buscas en tu entorno de trabajo")
    st.markdown(profile["lo_que_busca"])

    st.info(
        "Interpretación basada en el modelo DISC y perfiles conductuales descritos, "
        "incluyendo el perfil 'Perfeccionista' (C alto): persona metódica, precisa, "
        "que valora normas claras, estabilidad y control de calidad; puede tardar "
        "en decidir porque analiza toda la información y puede ser percibida como "
        "crítica frente a errores, pero aporta consistencia y rigor. :contentReference[oaicite:9]{index=9}"
    )

    # Botón para reiniciar (por si quieres volver a aplicar)
    if st.button("Volver a aplicar el test"):
        nombre_keep = st.session_state.nombre_participante
        st.session_state.clear()
        init_state()
        st.session_state.nombre_participante = nombre_keep
        st.session_state.stage = "test"
        st.session_state.current_idx = 0


# =========================================================
# 6. MAIN
# =========================================================

def main():
    st.set_page_config(
        page_title="Perfil Conductual DISC",
        page_icon="🧠",
        layout="centered"
    )

    init_state()

    if st.session_state.stage == "intro":
        page_intro()
    elif st.session_state.stage == "test":
        page_question()
    elif st.session_state.stage == "results":
        page_results()
    else:
        st.session_state.stage = "intro"
        page_intro()

    st.markdown("---")
    st.markdown(
        "<p style='text-align:center; font-size:12px; color:gray;'>"
        "Sistema de Perfil Conductual estilo DISC. "
        "Resultados de uso orientativo; no equivalen a diagnóstico clínico. "
        "© 2025</p>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
