from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import asyncpg
import os
import uvicorn

app = FastAPI()

DATABASE_URL = "postgresql://postgres.cnvcwksnsbwafgesgdcn:Pacucha.13.@aws-0-sa-east-1.pooler.supabase.com:5432/postgres"

async def connect_db():
    try:
        return await asyncpg.connect(DATABASE_URL)
    except Exception as e:
        print(f"❌ Error al conectar a la base de datos: {e}")
        return None

class UsuarioDiagnostico(BaseModel):
    nombre: str
    correo: str
    resultado: float
    preguntas_correctas: int
    preguntas_incorrectas: int
    preguntas_sin_responder: int
    tiempo_usado: int
    tipo: str  # debe ser "diagnostico"

class UsuarioSimulacro(BaseModel):
    nombre: str
    correo: str
    resultado: float
    preguntas_correctas: int
    preguntas_incorrectas: int
    preguntas_sin_responder: int
    tiempo_usado: int
    tipo: str  # debe ser "simulacro"
    respuestas_usuario: dict

@app.post("/guardar-resultado")
async def guardar_resultado(data: dict):
    try:
        conn = await connect_db()
        if conn is None:
            return JSONResponse(status_code=500, content={"error": "No se pudo conectar a la base de datos"})

        tipo = data.get("tipo")

        if tipo == "simulacro":
            usuario = UsuarioSimulacro(**data)
            tabla = "resultados_simulacro_v2"

            await conn.execute(f'''
                CREATE TABLE IF NOT EXISTS {tabla} (
                    id SERIAL PRIMARY KEY,
                    nombre TEXT,
                    correo TEXT,
                    resultado FLOAT,
                    preguntas_correctas INTEGER,
                    preguntas_incorrectas INTEGER,
                    preguntas_sin_responder INTEGER,
                    tiempo_usado INTEGER,
                    tipo TEXT,
                    respuestas_usuario JSONB,
                    fecha_realizacion TIMESTAMP
                )
            ''')

            await conn.execute(f'''
                INSERT INTO {tabla}
                (nombre, correo, resultado, preguntas_correctas, preguntas_incorrectas, preguntas_sin_responder, tiempo_usado, tipo, respuestas_usuario, fecha_realizacion)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
            ''',
            usuario.nombre,
            usuario.correo,
            usuario.resultado,
            usuario.preguntas_correctas,
            usuario.preguntas_incorrectas,
            usuario.preguntas_sin_responder,
            usuario.tiempo_usado,
            usuario.tipo,
            usuario.respuestas_usuario,
            datetime.now())

        else:  # diagnóstico
            usuario = UsuarioDiagnostico(**data)
            tabla = "resultados_simulacro"

            await conn.execute(f'''
                CREATE TABLE IF NOT EXISTS {tabla} (
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

            await conn.execute(f'''
                INSERT INTO {tabla}
                (nombre, correo, resultado, preguntas_correctas, preguntas_incorrectas, preguntas_sin_responder, tiempo_usado, fecha_realizacion)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
            ''',
            usuario.nombre,
            usuario.correo,
            usuario.resultado,
            usuario.preguntas_correctas,
            usuario.preguntas_incorrectas,
            usuario.preguntas_sin_responder,
            usuario.tiempo_usado,
            datetime.now())

        await conn.close()
        return {"status": "success", "message": f"Resultado guardado correctamente en {tabla}"}

    except Exception as e:
        print("❌ Error al guardar resultado:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})

# Middleware
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
