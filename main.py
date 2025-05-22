from fastapi import FastAPI, Query, Body
from pydantic import BaseModel
import asyncpg
import os
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import random # Import random for shuffling

app = FastAPI()

DATABASE_URL = "postgresql://postgres.cnvcwksnsbwafgesgdcn:Pacucha.13.@aws-0-sa-east-1.pooler.supabase.com:5432/postgres"

async def connect_db():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

# Modelo para recibir los datos del usuario (para prueba diagnóstica)
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
    """ Devuelve todos los ejercicios de la tabla ejercicios_admision ordenados por curso """
    try:
        conn = await connect_db()
        if conn is None:
            return {"error": "No se pudo conectar a la base de datos"}

        # Definir el orden 
específico de los cursos
        orden_cursos = ["RM", "Aritmética", "Algebra", "Geometría", "Trigonometría", "Física", "Química"]
        
        # Consulta para obtener todos los ejercicios
        ejercicios = await conn.fetch('SELECT ejercicio, imagen, a, b, c, d, e, alt_correcta, curso, tema, dificultad, ciclo FROM "ejercicios_admision"')
        await conn.close()

        if not ejercicios:
            return {"error": "No 
hay ejercicios en la base de datos"}

        # Ordenar los ejercicios según el orden de cursos definido
        ejercicios_ordenados = sorted(
            ejercicios, 
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
    """Guarda los resultados del simulacro junto con la información del usuario"""
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
    """ Devuelve todos los temas únicos de la tabla física_prácticas_cepreuni """
    try:
        conn = await connect_db()
        if conn is None:
            return {"error": "No se pudo conectar a la base de datos"}
        
        # Consulta para obtener temas únicos
        temas_data = await conn.fetch('SELECT DISTINCT tema FROM "física_prácticas_cepreuni" ORDER BY tema')
        await conn.close()

        if not temas_data:
            return {"error": "No hay temas en la base de datos para física_prácticas_cepreuni"}
        
        return [tema["tema"] for tema in temas_data]

    except Exception as e:
        return {"error": str(e)}

@app.get("/banco-preguntas/fisica/ejercicios")
async def get_ejercicios_fisica_por_temas(temas: str = Query(...)):
    """ Devuelve ejercicios de la tabla física_prácticas_cepreuni para los temas seleccionados """
    # temas será un string separado por comas, ej: "Tema1,Tema2,Tema3"
    try:
        conn = await connect_db()
        if conn is None:
            return {"error": "No se pudo conectar a la base de datos"}

        lista_temas = [tema.strip() for tema in temas.split(',')]
        
        # Consulta para obtener ejercicios por temas
        # Usamos ANY($1::text[]) para pasar la lista de temas
        query = """
            SELECT id, ejercicio, imagen, a, b, c, d, e, alt_correcta, tema, subtema, dificultad, tipo, ciclo 
            FROM "física_prácticas_cepreuni"
            WHERE tema = ANY($1::text[])
        """
        ejercicios = await conn.fetch(query, lista_temas)
        await conn.close()

        if not ejercicios:
            return {"message": "No hay ejercicios para los temas seleccionados"} # No es un error, puede que no haya preguntas para esa comb.

        preguntas_final = [
            {
                "id": p["id"], # Es buena idea tener un ID único por pregunta
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
        
        random.shuffle(preguntas_final) # Devolver las preguntas en orden aleatorio
        return preguntas_final

    except Exception as e:
        return {"error": str(e)}
# --- FIN NUEVOS ENDPOINTS ---

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  
    uvicorn.run(app, host="0.0.0.0", port=port)
