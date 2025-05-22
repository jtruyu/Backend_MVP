from fastapi import FastAPI, Query, Body
from pydantic import BaseModel
import asyncpg
import os
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import random # Importar random para la selección aleatoria

app = FastAPI()

DATABASE_URL = "postgresql://postgres.cnvcwksnsbwafgesgdcn:Pacucha.13.@aws-0-sa-east-1.pooler.supabase.com:5432/postgres"

async def connect_db():
    """Establece una conexión a la base de datos PostgreSQL."""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

# Modelo para recibir los datos del usuario para el diagnóstico
class Usuario(BaseModel):
    nombre: str
    correo: str
    resultado: float
    preguntas_correctas: int
    preguntas_incorrectas: int
    preguntas_sin_responder: int
    tiempo_usado: int

@app.get("/diagnostico/")
async def get_diagnostico():
    """
    Devuelve 10 ejercicios aleatorios de la tabla ejercicios_admision
    ordenados por curso para la prueba diagnóstica.
    """
    try:
        conn = await connect_db()
        if conn is None:
            return {"error": "No se pudo conectar a la base de datos"}

        # Consulta para obtener todos los ejercicios
        ejercicios = await conn.fetch('SELECT ejercicio, imagen, a, b, c, d, e, alt_correcta, curso, tema, dificultad, ciclo FROM "ejercicios_admision"')
        await conn.close()

        if not ejercicios:
            return {"error": "No hay ejercicios en la base de datos"}
        
        # Seleccionar 10 ejercicios aleatorios
        # Usamos random.sample para asegurar que sean únicos y no más de los disponibles
        num_preguntas_a_seleccionar = min(10, len(ejercicios))
        preguntas_seleccionadas = random.sample(ejercicios, num_preguntas_a_seleccionar)

        # Definir el orden específico de los cursos para el diagnóstico
        orden_cursos = ["RM", "Aritmética", "Algebra", "Geometría", "Trigonometría", "Física", "Química"]
        
        # Ordenar los ejercicios seleccionados según el orden de cursos definido
        ejercicios_ordenados = sorted(
            preguntas_seleccionadas, 
            key=lambda x: orden_cursos.index(x["curso"]) if x["curso"] in orden_cursos else 999
        )

        preguntas_final = [
            {
                "ejercicio": p["ejercicio"],
                "imagen": p["imagen"],
                "alternativas": [
                    {"letra": "A", "texto": p["a"]},
                    {"letra": "B", "texto": p["b"]},
                    {"letra": "C", "texto": p["c"]},
                    {"letra": "D", "texto": p["d"]},
                    {"letra": "E", "texto": p["e"]},
                ],
                "respuesta_correcta": p["alt_correcta"],
                "curso": p["curso"],
                "tema": p["tema"],
                "dificultad": p["dificultad"],
                "ciclo": p["ciclo"]
            }
            for p in ejercicios_ordenados
        ]

        return preguntas_final

    except Exception as e:
        return {"error": str(e)}

@app.post("/guardar-diagnostico")
async def guardar_diagnostico(usuario: Usuario):
    """Guarda los resultados del simulacro junto con la información del usuario."""
    try:
        conn = await connect_db()
        if conn is None:
            return {"error": "No se pudo conectar a la base de datos"}
        
        # Crear la tabla si no existe
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS resultados_diagnostico (
                id SERIAL PRIMARY KEY,
                nombre TEXT,
                correo TEXT,
                resultado FLOAT,
                preguntas_correctas INTEGER,
                preguntas_incorrectas INTEGER,
                preguntas_sin_responder INTEGER,
                tiempo_usado INTEGER,
                fecha_realizacion TIMESTAMP
            )
        ''')
        
        # Insertar los datos del resultado
        await conn.execute('''
            INSERT INTO resultados_diagnostico
            (nombre, correo, resultado, preguntas_correctas, preguntas_incorrectas, preguntas_sin_responder, tiempo_usado, fecha_realizacion)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ''', 
        usuario.nombre, 
        usuario.correo, 
        usuario.resultado, 
        usuario.preguntas_correctas, 
        usuario.preguntas_incorrectas,
        usuario.preguntas_sin_responder,
        usuario.tiempo_usado,
        datetime.now()
        )
        
        await conn.close()
        return {"status": "success", "message": "Resultado guardado correctamente"}
    
    except Exception as e:
        return {"error": str(e)}

# --- NUEVOS ENDPOINTS PARA BANCO DE PREGUNTAS ---
@app.get("/banco-preguntas/fisica/temas")
async def get_temas_fisica_cepreuni():
    """ Devuelve todos los temas únicos de la tabla física_prácticas_cepreuni. """
    try:
        conn = await connect_db()
        if conn is None:
            return {"error": "No se pudo conectar a la base de datos"}
            
        # Consulta para obtener temas únicos de la tabla con tilde
        temas_data = await conn.fetch('SELECT DISTINCT tema FROM "física_prácticas_cepreuni" ORDER BY tema')
        await conn.close()

        if not temas_data:
            return {"error": "No hay temas en la base de datos para física_prácticas_cepreuni"}
            
        return [tema["tema"] for tema in temas_data]

    except Exception as e:
        return {"error": str(e)}

@app.get("/banco-preguntas/")
async def get_banco_preguntas(temas: str = Query(..., description="Lista de temas separados por comas")):
    """ 
    Devuelve ejercicios de la tabla física_prácticas_cepreuni basados en los temas seleccionados.
    """
    try:
        conn = await connect_db()
        if conn is None:
            return {"error": "No se pudo conectar a la base de datos"}

        temas_list = [tema.strip() for tema in temas.split(',')]
        
        # Construir la cláusula WHERE para filtrar por temas usando ANY con la tabla con tilde
        query = 'SELECT ejercicio, imagen, a, b, c, d, e, alt_correcta, tema, subtema, dificultad, tipo, ciclo FROM "física_prácticas_cepreuni" WHERE tema = ANY($1::text[])'
        
        ejercicios = await conn.fetch(query, temas_list)
        await conn.close()

        if not ejercicios:
            return {"error": "No hay ejercicios para los temas seleccionados en la base de datos"}

        preguntas_final = [
            {
                "ejercicio": p["ejercicio"],
                "imagen": p["imagen"],
                "alternativas": [
                    {"letra": "A", "texto": p["a"]},
                    {"letra": "B", "texto": p["b"]},
                    {"letra": "C", "texto": p["c"]},
                    {"letra": "D", "texto": p["d"]},
                    {"letra": "E", "texto": p["e"]},
                ],
                "respuesta_correcta": p["alt_correcta"],
                "tema": p["tema"],
                "subtema": p["subtema"],
                "dificultad": p["dificultad"],
                "tipo": p["tipo"],
                "ciclo": p["ciclo"]
            }
            for p in ejercicios
        ]
        
        # Las preguntas se mezclarán en el frontend para una nueva ronda
        return preguntas_final

    except Exception as e:
        return {"error": str(e)}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas las origenes. En producción, se recomienda especificar dominios.
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permite todos los encabezados
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  
    uvicorn.run(app, host="0.0.0.0", port=port)

