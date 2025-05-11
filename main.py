import React, { useState, useEffect } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [pantalla, setPantalla] = useState("inicio");
  const [tipoPrueba, setTipoPrueba] = useState("diagnostico");
  const [preguntas, setPreguntas] = useState([]);
  const [respuestas, setRespuestas] = useState({});
  const [preguntaActual, setPreguntaActual] = useState(0);
  const [tiempo, setTiempo] = useState(40 * 60);
  const [tiempoInicial, setTiempoInicial] = useState(40 * 60);
  const [tiempoActivo, setTiempoActivo] = useState(false);
  const [datosUsuario, setDatosUsuario] = useState({ nombre: "", correo: "" });
  const [resultados, setResultados] = useState(null);
  const [resultadosTemporales, setResultadosTemporales] = useState(null);
  const [comentarioResultado, setComentarioResultado] = useState("");

  useEffect(() => {
    let intervalo;
    if (tiempoActivo && tiempo > 0) {
      intervalo = setInterval(() => setTiempo((t) => t - 1), 1000);
    } else if (tiempo === 0) {
      finalizarSimulacro();
    }
    return () => clearInterval(intervalo);
  }, [tiempoActivo, tiempo]);

  const iniciarPrueba = async (tipo) => {
    setTipoPrueba(tipo);
    const duracion = tipo === "simulacro" ? 108 * 60 : 40 * 60;
    setTiempo(duracion);
    setTiempoInicial(duracion);
    setTiempoActivo(true);
    setPreguntaActual(0);
    setRespuestas({});
    setPantalla("simulacro");

    try {
      const endpoint = tipo === "simulacro" ? "/simulacro_completo" : "/simulacro";
      const { data } = await axios.get(`https://backend-mvp-a6w0.onrender.com${endpoint}`);
      setPreguntas(data);
    } catch {
      alert("Error al cargar preguntas.");
      setPantalla("inicio");
    }
  };

  const seleccionarRespuesta = (ejercicio, letra) => {
    setRespuestas({ ...respuestas, [ejercicio]: letra });
  };

  const siguientePregunta = () => {
    if (preguntaActual < preguntas.length - 1) {
      setPreguntaActual(preguntaActual + 1);
    }
  };

  const preguntaAnterior = () => {
    if (preguntaActual > 0) {
      setPreguntaActual(preguntaActual - 1);
    }
  };

  const calcularPuntajePorCurso = (curso) => {
    if (tipoPrueba === "simulacro") {
      switch (curso) {
        case "RM":
        case "RV": return 0.63;
        case "Aritmética":
        case "Álgebra":
        case "Geometría":
        case "Trigonometría": return 0.76;
        case "Física": return 0.81;
        case "Química": return 0.46;
        default: return 0.5;
      }
    } else {
      switch (curso) {
        case "RM": return 1.8;
        case "Aritmética":
        case "Álgebra":
        case "Geometría":
        case "Trigonometría": return 2.2;
        case "Física": return 2.4;
        case "Química": return 1.4;
        default: return 2.0;
      }
    }
  };

  const finalizarSimulacro = () => {
    setTiempoActivo(false);
    let correctas = 0, incorrectas = 0, sinResp = 0, nota = 0;
    const detalles = {};

    preguntas.forEach((p) => {
      const r = respuestas[p.ejercicio];
      if (!r) {
        sinResp++;
        detalles[p.ejercicio] = "Sin responder";
      } else if (r === p.respuesta_correcta) {
        correctas++;
        nota += calcularPuntajePorCurso(p.curso);
        detalles[p.ejercicio] = "Correcta";
      } else {
        incorrectas++;
        detalles[p.ejercicio] = `Incorrecta (Respuesta: ${p.respuesta_correcta})`;
      }
    });

    nota = Math.min(nota, 20);
    const resultado = {
      correctas,
      incorrectas,
      sinResp,
      nota,
      detalles,
      tiempoUsado: tiempoInicial - tiempo,
    };
    setResultadosTemporales(resultado);
    setPantalla("formulario");
  };

  const procesarFormulario = async () => {
    if (!datosUsuario.nombre || !datosUsuario.correo.includes("@")) {
      alert("Por favor completa todos los campos correctamente.");
      return;
    }

    const r = resultadosTemporales;
    setResultados(r);

    try {
      await axios.post("https://backend-mvp-a6w0.onrender.com/guardar-resultado", {
        nombre: datosUsuario.nombre,
        correo: datosUsuario.correo,
        resultado: r.nota,
        preguntas_correctas: r.correctas,
        preguntas_incorrectas: r.incorrectas,
        preguntas_sin_responder: r.sinResp,
        tiempo_usado: r.tiempoUsado,
      });
    } catch {
      alert("Error al guardar resultados");
    }

    setPantalla("resultados");
  };

  const formatoTiempo = (s) =>
    `${Math.floor(s / 60).toString().padStart(2, "0")}:${(s % 60).toString().padStart(2, "0")}`;

  if (pantalla === "inicio") {
    return (
      <div className="container inicio-container">
        <h1>EDBOT</h1>
        <p>Selecciona una evaluación:</p>
        <button onClick={() => iniciarPrueba("diagnostico")}>Prueba Diagnóstica</button>
        <button onClick={() => iniciarPrueba("simulacro")}>Simulacro Completo</button>
      </div>
    );
  }

  if (pantalla === "simulacro" && preguntas.length > 0) {
    const p = preguntas[preguntaActual];
    return (
      <div className="container simulacro-container">
        <div className="encabezado-simulacro">
          <div className="progreso">
            <div>Pregunta {preguntaActual + 1} de {preguntas.length}</div>
            <div className="barra-progreso">
              <div
                className="progreso-completado"
                style={{ width: `${((preguntaActual + 1) / preguntas.length) * 100}%` }}
              ></div>
            </div>
          </div>
          <div className="temporizador">⏱️ {formatoTiempo(tiempo)}</div>
        </div>
        <h2 dangerouslySetInnerHTML={{ __html: p.ejercicio }} />
        <ul className="opciones-lista">
          {p.alternativas.map((alt) => (
            <li key={alt.letra}>
              <label>
                <input
                  type="radio"
                  name={`pregunta-${p.ejercicio}`}
                  value={alt.letra}
                  checked={respuestas[p.ejercicio] === alt.letra}
                  onChange={() => seleccionarRespuesta(p.ejercicio, alt.letra)}
                />
                <span dangerouslySetInnerHTML={{ __html: `${alt.letra}: ${alt.texto}` }} />
              </label>
            </li>
          ))}
        </ul>
        <button onClick={preguntaAnterior} disabled={preguntaActual === 0}>Anterior</button>
        {preguntaActual === preguntas.length - 1 ? (
          <button onClick={finalizarSimulacro}>Finalizar</button>
        ) : (
          <button onClick={siguientePregunta}>Siguiente</button>
        )}
      </div>
    );
  }

  if (pantalla === "formulario") {
    return (
      <div className="container formulario-container">
        <h2>Ingresa tus datos</h2>
        <input
          placeholder="Nombre completo"
          value={datosUsuario.nombre}
          onChange={(e) => setDatosUsuario({ ...datosUsuario, nombre: e.target.value })}
        />
        <input
          placeholder="Correo electrónico"
          value={datosUsuario.correo}
          onChange={(e) => setDatosUsuario({ ...datosUsuario, correo: e.target.value })}
        />
        <button onClick={procesarFormulario}>Ver resultados</button>
      </div>
    );
  }

  if (pantalla === "resultados") {
    return (
      <div className="container resultados-container">
        <h1>Resultados del {tipoPrueba === "simulacro" ? "Simulacro" : "Diagnóstico"}</h1>
        <p><strong>Nombre:</strong> {datosUsuario.nombre}</p>
        <p><strong>Correo:</strong> {datosUsuario.correo}</p>
        <p><strong>Nota:</strong> {resultados.nota.toFixed(1)}</p>
        <p><strong>Correctas:</strong> {resultados.correctas}</p>
        <p><strong>Incorrectas:</strong> {resultados.incorrectas}</p>
        <p><strong>Sin responder:</strong> {resultados.sinResp}</p>
        <button onClick={() => setPantalla("inicio")}>Volver al inicio</button>
      </div>
    );
  }

  return <div className="cargando-container">Cargando...</div>;
}

export default App;
