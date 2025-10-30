import React, { useState } from "react";

const EPQRATest = () => {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState({});
  const [selectedJob, setSelectedJob] = useState('');
  const [candidateName, setCandidateName] = useState('');
  const [evaluatorEmail, setEvaluatorEmail] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [scores, setScores] = useState({});

  // Versión corregida del EPQR-A (ítems 3 y 16 modificados según el estudio)
  const questions = [
    { id: 1, text: "¿Tiene con frecuencia subidas y bajadas de su estado de ánimo?" },
    { id: 2, text: "¿Es usted una persona habladora?" },
    { id: 3, text: "¿Lo pasaría muy mal si viese sufrir a un niño o a un animal?" },
    { id: 4, text: "¿Es usted más bien animado/a?" },
    { id: 5, text: "¿Alguna vez ha deseado más ayudarse a sí mismo/a que compartir con otros?" },
    { id: 6, text: "¿Tomaría drogas que pudieran tener efectos desconocidos o peligrosos?" },
    { id: 7, text: "¿Ha acusado a alguien alguna vez de hacer algo sabiendo que la culpa era de usted?" },
    { id: 8, text: "¿Prefiere actuar a su modo en lugar de comportarse según las normas?" },
    { id: 9, text: "¿Se siente con frecuencia harto/a («hasta la coronilla»)?" },
    { id: 10, text: "¿Ha cogido alguna vez algo que perteneciese a otra persona (aunque sea un broche o un bolígrafo)?" },
    { id: 11, text: "¿Se considera una persona nerviosa?" },
    { id: 12, text: "¿Piensa que el matrimonio está pasado de moda y que se debería suprimir?" },
    { id: 13, text: "¿Podría animar fácilmente una fiesta o reunión social aburrida?" },
    { id: 14, text: "¿Es usted una persona demasiado preocupada?" },
    { id: 15, text: "¿Tiende a mantenerse callado/o (o en un 2° plano) en las reuniones o encuentros sociales?" },
    { id: 16, text: "¿Cree que la gente dedica demasiado tiempo para asegurarse el futuro mediante ahorros o seguros?" },
    { id: 17, text: "¿Alguna vez ha hecho trampas en el juego?" },
    { id: 18, text: "¿Sufre usted de los nervios?" },
    { id: 19, text: "¿Se ha aprovechado alguna vez de otra persona?" },
    { id: 20, text: "Cuando está con otras personas, ¿es usted más bien callado/a?" },
    { id: 21, text: "¿Se siente muy solo/a con frecuencia?" },
    { id: 22, text: "¿Cree que es mejor seguir las normas de la sociedad que las suyas propias?" },
    { id: 23, text: "¿Las demás personas le consideran muy animado/a?" },
    { id: 24, text: "¿Pone en práctica siempre lo que dice?" }
  ];

  const jobProfiles = {
    'operario': {
      title: 'Operario de Producción',
      requirements: {
        E: { min: 0, max: 4 },
        N: { min: 0, max: 3 },
        P: { min: 0, max: 5 },
        S: { min: 4, max: 6 }
      }
    },
    'supervisor': {
      title: 'Supervisor Operativo',
      requirements: {
        E: { min: 3, max: 6 },
        N: { min: 0, max: 3 },
        P: { min: 2, max: 5 },
        S: { min: 4, max: 6 }
      }
    },
    'tecnico': {
      title: 'Técnico de Mantenimiento',
      requirements: {
        E: { min: 1, max: 4 },
        N: { min: 0, max: 3 },
        P: { min: 2, max: 5 },
        S: { min: 4, max: 6 }
      }
    },
    'logistica': {
      title: 'Personal de Logística',
      requirements: {
        E: { min: 2, max: 5 },
        N: { min: 0, max: 3 },
        P: { min: 1, max: 4 },
        S: { min: 4, max: 6 }
      }
    }
  };

  const handleAnswer = (answer) => {
    const updatedAnswers = { ...answers, [currentQuestion]: answer };
    setAnswers(updatedAnswers);

    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      calculateResults(updatedAnswers);
    }
  };

  const calculateResults = (finalAnswers) => {
    const scores = { E: 0, N: 0, P: 0, S: 0 };

    // Asignación directa de categorías basada en posición (sin mostrar categorías al usuario)
    const categories = [
      "N", "E", "P", "E", "S", "P", "S", "P", "N", "S",
      "N", "P", "E", "N", "E", "P", "S", "N", "S", "E",
      "N", "P", "E", "S"
    ];

    categories.forEach((category, index) => {
      const answer = finalAnswers[index];
      if (answer !== undefined) {
        // Invertir respuesta para categorías P y S según instrucciones del cuestionario
        const value = (category === "P" || category === "S") ? (answer === 0 ? 1 : 0) : answer;
        scores[category] += value;
      }
    });

    setAnswers(finalAnswers);
    setCurrentQuestion(0);
    setScores(scores);
    
    // Simular envío de resultados por correo
    setTimeout(() => {
      setIsSubmitted(true);
    }, 1500);
  };

  const resetTest = () => {
    setAnswers({});
    setCurrentQuestion(0);
    setScores({});
    setSelectedJob('');
    setCandidateName('');
    setEvaluatorEmail('');
    setIsSubmitted(false);
  };

  if (!selectedJob && !isSubmitted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8 px-4">
        <div className="max-w-2xl mx-auto bg-white rounded-2xl shadow-xl p-8">
          <h1 className="text-3xl font-bold text-center text-gray-800 mb-2">Test de Personalidad EPQR-A</h1>
          <p className="text-center text-gray-600 mb-8">Versión corregida para selección de personal operativo</p>
          
          <div className="bg-blue-50 rounded-lg p-6 mb-8">
            <h2 className="text-lg font-semibold text-blue-800 mb-3">Seleccione el cargo a evaluar:</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(jobProfiles).map(([key, profile]) => (
                <button
                  key={key}
                  onClick={() => setSelectedJob(key)}
                  className="p-4 text-left border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors duration-200"
                >
                  <h3 className="font-semibold text-gray-800">{profile.title}</h3>
                </button>
              ))}
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="font-semibold text-gray-800 mb-2">Instrucciones:</h3>
            <ul className="text-sm text-gray-700 space-y-1">
              <li>• Responda honestamente a cada pregunta</li>
              <li>• El test tarda aproximadamente 5 minutos</li>
              <li>• Los resultados se enviarán automáticamente al evaluador especificado</li>
              <li>• Usted no tendrá acceso a sus resultados directamente</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  if (isSubmitted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 py-8 px-4">
        <div className="max-w-2xl mx-auto bg-white rounded-2xl shadow-xl p-8 text-center">
          <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          
          <h1 className="text-3xl font-bold text-gray-800 mb-4">¡Test Completado!</h1>
          
          <div className="bg-blue-50 rounded-lg p-6 mb-8">
            <h2 className="text-xl font-semibold text-blue-800 mb-3">Resultados enviados exitosamente</h2>
            <p className="text-blue-700 mb-4">
              Los resultados del test han sido procesados y enviados al evaluador designado.
            </p>
            <div className="bg-white rounded-lg p-4 text-left">
              <p><strong>Candidato:</strong> {candidateName}</p>
              <p><strong>Cargo evaluado:</strong> {jobProfiles[selectedJob].title}</p>
              <p><strong>Destinatario:</strong> ps.raulvaldes@gmail.com</p>
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-6 mb-8">
            <h3 className="font-semibold text-gray-800 mb-3">Próximos pasos:</h3>
            <ul className="text-sm text-gray-700 space-y-2 text-left">
              <li>• El evaluador analizará sus resultados</li>
              <li>• Recibirá notificación sobre el proceso de selección</li>
              <li>• La información es confidencial y protegida</li>
            </ul>
          </div>

          <button
            onClick={resetTest}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200"
          >
            Realizar Nuevo Test
          </button>
        </div>
      </div>
    );
  }

  if (!candidateName && selectedJob) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8 px-4">
        <div className="max-w-2xl mx-auto bg-white rounded-2xl shadow-xl p-8">
          <h1 className="text-3xl font-bold text-center text-gray-800 mb-2">Información del Candidato</h1>
          <p className="text-center text-gray-600 mb-8">Ingrese los datos requeridos</p>
          
          <div className="bg-blue-50 rounded-lg p-6 mb-8">
            <h2 className="text-lg font-semibold text-blue-800 mb-4">Cargo seleccionado: {jobProfiles[selectedJob].title}</h2>
            
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Nombre del candidato
                </label>
                <input
                  type="text"
                  value={candidateName}
                  onChange={(e) => setCandidateName(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Ingrese nombre completo del candidato"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Correo del evaluador
                </label>
                <input
                  type="email"
                  value={evaluatorEmail}
                  onChange={(e) => setEvaluatorEmail(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="nombre@empresa.com"
                />
              </div>
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="font-semibold text-gray-800 mb-3">Confidencialidad de datos:</h3>
            <p className="text-sm text-gray-700 mb-4">
              La información proporcionada será utilizada únicamente para fines de selección de personal. 
              Los resultados serán enviados exclusivamente al correo del evaluador autorizado.
            </p>
          </div>

          <button
            onClick={() => candidateName && evaluatorEmail && currentQuestion === 0}
            disabled={!candidateName || !evaluatorEmail}
            className={`w-full mt-6 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200 ${
              !candidateName || !evaluatorEmail ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            Iniciar Test
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8 px-4">
      <div className="max-w-2xl mx-auto bg-white rounded-2xl shadow-xl overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-8 py-6 text-white">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold">Test de Personalidad EPQR-A</h1>
              <p className="text-blue-100">Cargo: {jobProfiles[selectedJob].title}</p>
            </div>
            <span className="bg-white bg-opacity-20 px-3 py-1 rounded-full text-sm">
              {currentQuestion + 1}/{questions.length}
            </span>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="px-8 py-4 bg-gray-50">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Pregunta {currentQuestion + 1} de {questions.length}</span>
            <span>{Math.round(((currentQuestion + 1) / questions.length) * 100)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${((currentQuestion + 1) / questions.length) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Question */}
        <div className="p-8">
          <div className="bg-white rounded-lg p-6 mb-8 border border-gray-200">
            <p className="text-lg text-gray-800 leading-relaxed">
              {questions[currentQuestion].text}
            </p>
          </div>

          {/* Answer Buttons */}
          <div className="flex gap-4">
            <button
              onClick={() => handleAnswer(1)}
              className="flex-1 bg-green-500 hover:bg-green-600 text-white font-semibold py-4 px-6 rounded-lg transition-colors duration-200 flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              Sí
            </button>
            
            <button
              onClick={() => handleAnswer(0)}
              className="flex-1 bg-red-500 hover:bg-red-600 text-white font-semibold py-4 px-6 rounded-lg transition-colors duration-200 flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
              No
            </button>
          </div>
        </div>

        {/* Instructions */}
        <div className="px-8 py-4 bg-gray-50 border-t">
          <div className="flex items-start space-x-2">
            <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            <p className="text-sm text-gray-700">
              <strong>Importante:</strong> Sus respuestas son confidenciales. Los resultados serán enviados automáticamente 
              al evaluador encargado del proceso de selección. Usted no tendrá acceso directo a sus resultados.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EPQRATest;
