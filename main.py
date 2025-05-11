from fastapi import FastAPI
from pydantic import BaseModel
import asyncpg
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI()

DATABASE_URL = "postgresql://postgres.cnvcwksnsbwafgesgdcn:Pacucha.13.@aws-0-sa-east-1.pooler.supabase.com:5432/postgres"

async def connect_db():
    try:
        return await asyncpg.connect(DATABASE_URL)
    except Exception as e:
        print(f"Error de conexión: {e}")
        return None

class Usuario(BaseModel):
    nombre: str
    correo: str
    resultado: float
    preguntas_correctas: int
    preguntas_incorrectas: int
    preguntas_sin_responder: int
    tiempo_usado: int

@app.get("/simulacro")
async def get_simulacro():
    conn = await connect_db()
    if conn is None:
        return {"error": "No hay conexión con la base de datos"}
    ejercicios = await conn.fetch('SELECT * FROM ejercicios_admision')
    await conn.close()
    return [
        {
            "ejercicio": e["ejercicio"],
            "imagen": e["imagen"],
            "alternativas": [
                {"letra": "A", "texto": e["a"]},
                {"letra": "B", "texto": e["b"]},
                {"letra": "C", "texto": e["c"]},
                {"letra": "D", "texto": e["d"]},
                {"letra": "E", "texto": e["e"]},
            ],
            "respuesta_correcta": e["alt_correcta"],
            "curso": e["curso"],
            "tema": e["tema"],
            "dificultad": e["dificultad"],
            "ciclo": e["ciclo"]
        } for e in ejercicios
    ]

@app.get("/simulacro_completo")
async def get_simulacro_completo():
    conn = await connect_db()
    if conn is None:
        return {"error": "No hay conexión con la base de datos"}
    ejercicios = await conn.fetch('SELECT * FROM primer_simulacro')
    await conn.close()
    return [
        {
            "ejercicio": e["ejercicio"],
            "imagen": e["imagen"],
            "alternativas": [
                {"letra": "A", "texto": e["a"]},
                {"letra": "B", "texto": e["b"]},
                {"letra": "C", "texto": e["c"]},
                {"letra": "D", "texto": e["d"]},
                {"letra": "E", "texto": e["e"]},
            ],
            "respuesta_correcta": e["alt_correcta"],
            "curso": e["curso"],
            "tema": e["tema"],
            "dificultad": e["dificultad"],
            "ciclo": e["ciclo"]
        } for e in ejercicios
    ]

@app.post("/guardar-resultado")
async def guardar_resultado(usuario: Usuario):
    conn = await connect_db()
    if conn is None:
        return {"error": "No hay conexión con la base de datos"}

    await conn.execute('''
        CREATE TABLE IF NOT EXISTS resultados_simulacro (
            id SERIAL PRIMARY KEY,
            nombre TEXT,
            correo TEXT,
            resultado FLOAT,
            preguntas_correctas INT,
            preguntas_incorrectas INT,
            preguntas_sin_responder INT,
            tiempo_usado INT,
            fecha_realizacion TIMESTAMP
        )''')

    await conn.execute('''
        INSERT INTO resultados_simulacro (nombre, correo, resultado, preguntas_correctas,
        preguntas_incorrectas, preguntas_sin_responder, tiempo_usado, fecha_realizacion)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    ''', usuario.nombre, usuario.correo, usuario.resultado, usuario.preguntas_correctas,
         usuario.preguntas_incorrectas, usuario.preguntas_sin_responder, usuario.tiempo_usado, datetime.now())

    await conn.close()
    return {"status": "success", "message": "Resultado guardado correctamente"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
