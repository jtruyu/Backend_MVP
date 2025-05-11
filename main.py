# Archivo main.py extendido
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
from datetime import datetime

app = FastAPI()

DATABASE_URL = "postgresql://postgres.cnvcwksnsbwafgesgdcn:Pacucha.13.@aws-0-sa-east-1.pooler.supabase.com:5432/postgres"

async def connect_db():
    try:
        return await asyncpg.connect(DATABASE_URL)
    except Exception as e:
        print(f"DB error: {e}")
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
async def simulacro():
    conn = await connect_db()
    if not conn:
        return {"error": "db error"}
    rows = await conn.fetch('SELECT * FROM ejercicios_admision')
    await conn.close()
    return [
        {
            "ejercicio": r["ejercicio"],
            "imagen": r["imagen"],
            "alternativas": [
                {"letra": "A", "texto": r["a"]},
                {"letra": "B", "texto": r["b"]},
                {"letra": "C", "texto": r["c"]},
                {"letra": "D", "texto": r["d"]},
                {"letra": "E", "texto": r["e"]},
            ],
            "respuesta_correcta": r["alt_correcta"],
            "curso": r["curso"],
            "tema": r["tema"],
            "dificultad": r["dificultad"],
            "ciclo": r["ciclo"]
        } for r in rows
    ]

@app.get("/simulacro_completo")
async def simulacro_completo():
    conn = await connect_db()
    if not conn:
        return {"error": "db error"}
    rows = await conn.fetch('SELECT * FROM primer_simulacro')
    await conn.close()
    return [
        {
            "ejercicio": r["ejercicio"],
            "imagen": r["imagen"],
            "alternativas": [
                {"letra": "A", "texto": r["a"]},
                {"letra": "B", "texto": r["b"]},
                {"letra": "C", "texto": r["c"]},
                {"letra": "D", "texto": r["d"]},
                {"letra": "E", "texto": r["e"]},
            ],
            "respuesta_correcta": r["alt_correcta"],
            "curso": r["curso"],
            "tema": r["tema"],
            "dificultad": r["dificultad"],
            "ciclo": r["ciclo"]
        } for r in rows
    ]

@app.post("/guardar-resultado")
async def guardar(usuario: Usuario):
    conn = await connect_db()
    if not conn:
        return {"error": "db error"}
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
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
    ''', usuario.nombre, usuario.correo, usuario.resultado, usuario.preguntas_correctas,
         usuario.preguntas_incorrectas, usuario.preguntas_sin_responder, usuario.tiempo_usado, datetime.now())
    await conn.close()
    return {"status": "ok"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
