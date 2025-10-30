import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, CheckCircle, User, Target, Award } from 'lucide-react';

const DISCTest = () => {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState(Array(28).fill(null));
  const [showResults, setShowResults] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);

  const questions = [
    "En situaciones sociales, tiendo a:",
    "Cuando enfrento un desafío, mi enfoque es:",
    "Mi estilo de comunicación preferido es:",
    "En un equipo de trabajo, suelo:",
    "Cuando tomo decisiones, me baso principalmente en:",
    "Mi ritmo de trabajo ideal es:",
    "Ante la presión, mi reacción típica es:",
    "Mis prioridades en el trabajo son:",
    "En reuniones, suelo:",
    "Mi enfoque ante los cambios es:",
    "Cuando doy feedback, soy:",
    "Mi motivación principal proviene de:",
    "En conflictos, tiendo a:",
    "Mi estilo de liderazgo es:",
    "Cuando aprendo algo nuevo, prefiero:",
    "Mis relaciones personales se caracterizan por:",
    "Ante un plazo ajustado, mi estrategia es:",
    "Mi enfoque en la resolución de problemas es:",
    "En mi entorno de trabajo, valoro más:",
    "Cuando establezco metas, soy:",
    "Mi reacción ante la crítica es:",
    "En situaciones de incertidumbre, soy:",
    "Mi estilo de vestimenta refleja:",
    "Cuando colaboro con otros, busco:",
    "Mi enfoque en la planificación es:",
    "Ante el fracaso, mi actitud es:",
    "Mis fortalezas principales son:",
    "Mi legado profesional ideal sería:"
  ];

  const options = [
    [
      { text: "Tomar la iniciativa y dirigir conversaciones", type: "D" },
      { text: "Ser entusiasta y contagiar energía", type: "I" },
      { text: "Escuchar atentamente y apoyar a otros", type: "S" },
      { text: "Analizar cuidadosamente antes de hablar", type: "C" }
    ],
    [
      { text: "Actuar decisivamente para resolverlo rápidamente", type: "D" },
      { text: "Buscar soluciones creativas e innovadoras", type: "I" },
      { text: "Colaborar con otros para encontrar la mejor solución", type: "S" },
      { text: "Analizar todos los datos antes de decidir", type: "C" }
    ],
    [
      { text: "Directa y concisa, voy al grano", type: "D" },
      { text: "Expresiva y entusiasta, uso gestos", type: "I" },
      { text: "Amable y considerada, evito confrontaciones", type: "S" },
      { text: "Precisa y detallada, me aseguro de ser clara", type: "C" }
    ],
    [
      { text: "Liderar y tomar decisiones importantes", type: "D" },
      { text: "Motivar e inspirar a mis compañeros", type: "I" },
      { text: "Apoyar y ayudar a mantener la armonía", type: "S" },
      { text: "Asegurar que todo se haga correctamente", type: "C" }
    ],
    [
      { text: "Resultados y eficiencia", type: "D" },
      { text: "Intuición y emociones", type: "I" },
      { text: "Impacto en las personas", type: "S" },
      { text: "Hechos y análisis lógico", type: "C" }
    ],
    [
      { text: "Rápido y dinámico", type: "D" },
      { text: "Flexible y adaptable", type: "I" },
      { text: "Estable y constante", type: "S" },
      { text: "Metódico y preciso", type: "C" }
    ],
    [
      { text: "Mantenerme firme y enfocado en soluciones", type: "D" },
      { text: "Expresar mis emociones abiertamente", type: "I" },
      { text: "Buscar apoyo y consenso", type: "S" },
      { text: "Retirarme para analizar la situación", type: "C" }
    ],
    [
      { text: "Logros y resultados tangibles", type: "D" },
      { text: "Reconocimiento y relaciones", type: "I" },
      { text: "Estabilidad y armonía", type: "S" },
      { text: "Calidad y precisión", type: "C" }
    ],
    [
      { text: "Dirigir la conversación hacia objetivos claros", type: "D" },
      { text: "Compartir ideas y generar entusiasmo", type: "I" },
      { text: "Escuchar y apoyar las opiniones de otros", type: "S" },
      { text: "Hacer preguntas precisas y analíticas", type: "C" }
    ],
    [
      { text: "Adaptarme rápidamente y aprovechar oportunidades", type: "D" },
      { text: "Verlo como una aventura emocionante", type: "I" },
      { text: "Necesitar tiempo para ajustarme cómodamente", type: "S" },
      { text: "Analizar cuidadosamente los pros y contras", type: "C" }
    ],
    [
      { text: "Directo y honesto, sin rodeos", type: "D" },
      { text: "Entusiasta y positivo, enfocado en lo bueno", type: "I" },
      { text: "Diplomático y considerado, evito herir sentimientos", type: "S" },
      { text: "Detallado y constructivo, con sugerencias específicas", type: "C" }
    ],
    [
      { text: "El desafío y la competencia", type: "D" },
      { text: "El reconocimiento social y la diversión", type: "I" },
      { text: "Las relaciones estables y el apoyo mutuo", type: "S" },
      { text: "La excelencia y el dominio técnico", type: "C" }
    ],
    [
      { text: "Abordarlos directamente para resolverlos", type: "D" },
      { text: "Expresar mis sentimientos abiertamente", type: "I" },
      { text: "Buscar compromisos y mantener la paz", type: "S" },
      { text: "Analizar la situación lógicamente", type: "C" }
    ],
    [
      { text: "Autoritario y orientado a resultados", type: "D" },
      { text: "Carismático e inspirador", type: "I" },
      { text: "Servicial y enfocado en el equipo", type: "S" },
      { text: "Analítico y basado en procesos", type: "C" }
    ],
    [
      { text: "Practicar inmediatamente lo aprendido", type: "D" },
      { text: "Compartirlo con entusiasmo con otros", type: "I" },
      { text: "Aplicarlo gradualmente en contextos familiares", type: "S" },
      { text: "Estudiarlo profundamente antes de aplicarlo", type: "C" }
    ],
    [
      { text: "Independientes y orientadas a objetivos", type: "D" },
      { text: "Animadas y llenas de energía", type: "I" },
      { text: "Estables y basadas en confianza", type: "S" },
      { text: "Profundas y significativas", type: "C" }
    ],
    [
      { text: "Priorizar tareas críticas y actuar rápido", type: "D" },
      { text: "Buscar ayuda creativa y soluciones alternativas", type: "I" },
      { text: "Pedir apoyo y trabajar en equipo", type: "S" },
      { text: "Crear un plan detallado y seguirlo", type: "C" }
    ],
    [
      { text: "Encontrar soluciones prácticas rápidamente", type: "D" },
      { text: "Generar ideas innovadoras y originales", type: "I" },
      { text: "Considerar el impacto en todas las personas involucradas", type: "S" },
      { text: "Analizar sistemáticamente todas las variables", type: "C" }
    ],
    [
      { text: "Resultados medibles y logros", type: "D" },
      { text: "Creatividad y expresión personal", type: "I" },
      { text: "Armonía y cooperación", type: "S" },
      { text: "Precisión y calidad del trabajo", type: "C" }
    ],
    [
      { text: "Ambiciosas y orientadas al éxito", type: "D" },
      { text: "Inspiradoras y motivadoras", type: "I" },
      { text: "Realistas y alcanzables", type: "S" },
      { text: "Detalladas y bien planificadas", type: "C" }
    ],
    [
      { text: "Aceptarla si es constructiva y útil", type: "D" },
      { text: "Sentirme herido pero tratar de aprender", type: "I" },
      { text: "Tomármela personalmente y necesitar tiempo", type: "S" },
      { text: "Analizarla objetivamente para mejorar", type: "C" }
    ],
    [
      { text: "Decidido y proactivo", type: "D" },
      { text: "Optimista y adaptable", type: "I" },
      { text: "Cauteloso y necesita seguridad", type: "S" },
      { text: "Analítico y busca información", type: "C" }
    ],
    [
      { text: "Profesional y poderosa", type: "D" },
      { text: "Colorida y expresiva", type: "I" },
      { text: "Cómoda y tradicional", type: "S" },
      { text: "Elegante y bien coordinada", type: "C" }
    ],
    [
      { text: "Lograr resultados efectivos", type: "D" },
      { text: "Hacer que sea divertido y estimulante", type: "I" },
      { text: "Crear un ambiente armonioso", type: "S" },
      { text: "Asegurar que todo se haga correctamente", type: "C" }
    ],
    [
      { text: "Acción inmediata y flexible", type: "D" },
      { text: "Ideas generales y visión amplia", type: "I" },
      { text: "Planificación gradual y estable", type: "S" },
      { text: "Detalles minuciosos y estructura", type: "C" }
    ],
    [
      { text: "Aprender de él y seguir adelante", type: "D" },
      { text: "Verlo como una experiencia de aprendizaje", type: "I" },
      { text: "Sentirme desanimado pero persistente", type: "S" },
      { text: "Analizar qué salió mal para evitarlo", type: "C" }
    ],
    [
      { text: "Liderazgo y toma de decisiones", type: "D" },
      { text: "Creatividad e influencia social", type: "I" },
      { text: "Paciencia y apoyo a otros", type: "S" },
      { text: "Análisis y atención al detalle", type: "C" }
    ],
    [
      { text: "Haber transformado industrias", type: "D" },
      { text: "Haber inspirado a muchas personas", type: "I" },
      { text: "Haber construido relaciones duraderas", type: "S" },
      { text: "Haber alcanzado la excelencia técnica", type: "C" }
    ]
  ];

  const handleAnswer = (optionIndex) => {
    const newAnswers = [...answers];
    newAnswers[currentQuestion] = optionIndex;
    setAnswers(newAnswers);
  };

  const nextQuestion = () => {
    if (currentQuestion < 27) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      calculateResults();
    }
  };

  const prevQuestion = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
    }
  };

  const calculateResults = () => {
    const scores = { D: 0, I: 0, S: 0, C: 0 };
    
    answers.forEach((answer, index) => {
      if (answer !== null) {
        const selectedOption = options[index][answer];
        scores[selectedOption.type]++;
      }
    });

    const totalQuestions = answers.filter(a => a !== null).length;
    const percentages = {
      D: Math.round((scores.D / totalQuestions) * 100),
      I: Math.round((scores.I / totalQuestions) * 100),
      S: Math.round((scores.S / totalQuestions) * 100),
      C: Math.round((scores.C / totalQuestions) * 100)
    };

    setShowResults(true);
    setIsCompleted(true);
  };

  const resetTest = () => {
    setCurrentQuestion(0);
    setAnswers(Array(28).fill(null));
    setShowResults(false);
    setIsCompleted(false);
  };

  const getProfileDescription = (dominantType) => {
    switch(dominantType) {
      case 'D':
        return "Dominante: Eres directo, decidido y orientado a resultados. Te gusta asumir el control y enfrentar desafíos.";
      case 'I':
        return "Influyente: Eres entusiasta, optimista y sociable. Te encanta inspirar a otros y trabajar en equipo.";
      case 'S':
        return "Estable: Eres paciente, confiable y cooperativo. Valoras la armonía y las relaciones estables.";
      case 'C':
        return "Conforme: Eres analítico, preciso y meticuloso. Te enfocas en la calidad y la exactitud.";
      default:
        return "Perfil equilibrado: Tienes características de múltiples estilos, lo que te permite adaptarte a diferentes situaciones.";
    }
  };

  const getDominantType = () => {
    if (!showResults) return null;
    
    const scores = { D: 0, I: 0, S: 0, C: 0 };
    answers.forEach((answer, index) => {
      if (answer !== null) {
        const selectedOption = options[index][answer];
        scores[selectedOption.type]++;
      }
    });

    return Object.keys(scores).reduce((a, b) => scores[a] > scores[b] ? a : b);
  };

  if (showResults) {
    const dominantType = getDominantType();
    const scores = { D: 0, I: 0, S: 0, C: 0 };
    answers.forEach((answer, index) => {
      if (answer !== null) {
        const selectedOption = options[index][answer];
        scores[selectedOption.type]++;
      }
    });

    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 py-8 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <div className="text-center mb-8">
              <Award className="w-16 h-16 text-blue-600 mx-auto mb-4" />
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Resultados del Test DISC</h1>
              <p className="text-gray-600">Análisis de tu perfil conductual</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">Tu Perfil Dominante</h3>
                <div className="flex items-center space-x-3 mb-4">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center text-white text-lg font-bold ${
                    dominantType === 'D' ? 'bg-red-500' :
                    dominantType === 'I' ? 'bg-yellow-500' :
                    dominantType === 'S' ? 'bg-green-500' :
                    'bg-blue-500'
                  }`}>
                    {dominantType}
                  </div>
                  <span className="text-lg font-medium text-gray-900">
                    {dominantType === 'D' ? 'Dominante' :
                     dominantType === 'I' ? 'Influyente' :
                     dominantType === 'S' ? 'Estable' :
                     'Conforme'}
                  </span>
                </div>
                <p className="text-gray-700">{getProfileDescription(dominantType)}</p>
              </div>

              <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl p-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">Puntajes Detallados</h3>
                <div className="space-y-3">
                  {Object.entries(scores).map(([type, score]) => (
                    <div key={type} className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold ${
                          type === 'D' ? 'bg-red-500' :
                          type === 'I' ? 'bg-yellow-500' :
                          type === 'S' ? 'bg-green-500' :
                          'bg-blue-500'
                        }`}>
                          {type}
                        </span>
                        <span className="font-medium">
                          {type === 'D' ? 'Dominante' :
                           type === 'I' ? 'Influyente' :
                           type === 'S' ? 'Estable' :
                           'Conforme'}
                        </span>
                      </div>
                      <span className="text-lg font-bold text-gray-900">{score}/28</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-xl p-6 mb-8">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Recomendaciones Profesionales</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-white p-4 rounded-lg border-l-4 border-blue-500">
                  <h4 className="font-semibold text-gray-900 mb-2">Fortalezas Clave</h4>
                  <ul className="text-gray-700 space-y-1">
                    <li>• Alta capacidad de liderazgo y toma de decisiones</li>
                    <li>• Excelente en entornos competitivos</li>
                    <li>• Orientado a resultados y metas claras</li>
                  </ul>
                </div>
                <div className="bg-white p-4 rounded-lg border-l-4 border-green-500">
                  <h4 className="font-semibold text-gray-900 mb-2">Áreas de Desarrollo</h4>
                  <ul className="text-gray-700 space-y-1">
                    <li>• Trabajar en la escucha activa</li>
                    <li>• Considerar más el impacto en las personas</li>
                    <li>• Practicar la paciencia en procesos lentos</li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="flex justify-center space-x-4">
              <button
                onClick={resetTest}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                Volver a Realizar el Test
              </button>
              <button
                onClick={() => window.print()}
                className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors font-medium"
              >
                Imprimir Resultados
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white p-6">
            <div className="flex items-center space-x-3 mb-2">
              <Target className="w-8 h-8" />
              <h1 className="text-2xl font-bold">Test DISC Profesional</h1>
            </div>
            <p className="text-blue-100">Descubre tu perfil conductual en 28 preguntas</p>
            <div className="mt-4 flex items-center justify-between">
              <span className="text-sm text-blue-200">
                Pregunta {currentQuestion + 1} de 28
              </span>
              <div className="w-64 bg-blue-500 rounded-full h-2">
                <div 
                  className="bg-white rounded-full h-2 transition-all duration-300"
                  style={{ width: `${((currentQuestion + 1) / 28) * 100}%` }}
                ></div>
              </div>
            </div>
          </div>

          {/* Question */}
          <div className="p-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-8 leading-relaxed">
              {questions[currentQuestion]}
            </h2>

            <div className="space-y-4">
              {options[currentQuestion].map((option, index) => (
                <button
                  key={index}
                  onClick={() => handleAnswer(index)}
                  className={`w-full p-4 text-left rounded-xl border-2 transition-all duration-200 hover:shadow-md ${
                    answers[currentQuestion] === index
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-200 hover:border-gray-300 text-gray-700'
                  }`}
                >
                  <div className="flex items-start space-x-3">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center mt-0.5 ${
                      answers[currentQuestion] === index
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 text-gray-400'
                    }`}>
                      {answers[currentQuestion] === index && <CheckCircle className="w-4 h-4" />}
                    </div>
                    <span className="font-medium">{option.text}</span>
                  </div>
                </button>
              ))}
            </div>

            {/* Navigation */}
            <div className="flex justify-between items-center mt-8 pt-6 border-t border-gray-200">
              <button
                onClick={prevQuestion}
                disabled={currentQuestion === 0}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                  currentQuestion === 0
                    ? 'text-gray-400 cursor-not-allowed'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                <ChevronLeft className="w-4 h-4" />
                <span>Anterior</span>
              </button>

              <div className="text-sm text-gray-500">
                {currentQuestion + 1} / 28
              </div>

              <button
                onClick={nextQuestion}
                disabled={answers[currentQuestion] === null}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                  answers[currentQuestion] === null
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                <span>
                  {currentQuestion === 27 ? 'Ver Resultados' : 'Siguiente'}
                </span>
                {currentQuestion < 27 && <ChevronRight className="w-4 h-4" />}
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-6 text-center text-sm text-gray-500">
          <p>Test DISC Profesional • Basado en el modelo de William Moulton Marston</p>
        </div>
      </div>
    </div>
  );
};

export default DISCTest;
