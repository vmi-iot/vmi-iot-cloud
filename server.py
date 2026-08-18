"""
Projeto PLC - Backend Cloud-Ready
"""
import os
import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="API PLC VMI-IOT")

# O Render define a porta automaticamente, localmente usamos 8000
port = int(os.getenv("PORT", 8000))
DB_PATH = "server_data.db"

class LeituraInput(BaseModel):
    machine_id: str
    tag: str
    valor: float
    timestamp: str

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS leituras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_id TEXT NOT NULL,
            tag TEXT NOT NULL,
            valor REAL NOT NULL,
            timestamp TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn

# --- Serve o HTML na raiz (ex: https://seu-projeto.onrender.com) ---
@app.get("/", response_class=HTMLResponse)
def dashboard():
    with open("dashboard.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/sync")
def receber_dados(leitura: LeituraInput):
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO leituras (machine_id, tag, valor, timestamp) VALUES (?, ?, ?, ?)",
            (leitura.machine_id, leitura.tag, leitura.valor, leitura.timestamp)
        )
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history/{machine_id}")
def historico_maquina(machine_id: str, tag: str = None):
    conn = get_db()
    if tag:
        query = "SELECT timestamp, valor FROM leituras WHERE machine_id = ? AND tag = ? ORDER BY timestamp DESC LIMIT 100"
        params = (machine_id, tag)
    else:
        query = "SELECT timestamp, valor FROM leituras WHERE machine_id = ? ORDER BY timestamp DESC LIMIT 100"
        params = (machine_id,)
    
    cursor = conn.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return {
        "machine_id": machine_id,
        "data": [{"time": row[0], "value": row[1]} for row in rows]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=port)