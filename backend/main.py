import sqlite3
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from typing import List
import asyncio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据库初始化

def get_db_connection():
    conn = sqlite3.connect('poll.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS poll_question (
            id INTEGER PRIMARY KEY,
            question_text TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS poll_option (
            id INTEGER PRIMARY KEY,
            question_id INTEGER NOT NULL,
            option_text TEXT NOT NULL,
            votes INTEGER DEFAULT 0,
            FOREIGN KEY(question_id) REFERENCES poll_question(id)
        )
    ''')
    # 插入默认问题和选项（仅当无数据时）
    cursor.execute('SELECT COUNT(*) FROM poll_question')
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO poll_question (id, question_text) VALUES (1, '你最喜欢的编程语言是？')")
        cursor.executemany(
            "INSERT INTO poll_option (id, question_id, option_text, votes) VALUES (?, 1, ?, 0)",
            [(1, "Python"), (2, "Java"), (3, "C")]
        )
    conn.commit()
    conn.close()

init_db()

#Pydantic模组

class Option(BaseModel):
    id: int
    text: str
    votes: int = 0

class VoteRequest(BaseModel):
    option_id: int

# 辅助函数

def fetch_poll():
    conn = get_db_connection()
    question_row = conn.execute("SELECT question_text FROM poll_question WHERE id=1").fetchone()
    options_rows = conn.execute("SELECT id, option_text, votes FROM poll_option WHERE question_id=1").fetchall()
    conn.close()
    question = question_row['question_text']
    options = [Option(id=row['id'], text=row['option_text'], votes=row['votes']) for row in options_rows]
    return question, options

def increment_vote(option_id: int):
    conn = get_db_connection()
    conn.execute("UPDATE poll_option SET votes = votes + 1 WHERE id = ?", (option_id,))
    conn.commit()
    conn.close()

#连接管理

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, data):
        json_data = jsonable_encoder(data)
        to_remove = []
        for connection in self.active_connections:
            try:
                await connection.send_json(json_data)
            except Exception:
                to_remove.append(connection)
        for c in to_remove:
            self.disconnect(c)

manager = ConnectionManager()

#路由
@app.get("/api/poll")
def get_poll():
    question, options = fetch_poll()
    return {"question": question, "options": options}

@app.post("/api/poll/vote")
async def vote(req: VoteRequest):
    increment_vote(req.option_id)
    question, options = fetch_poll()
    await manager.broadcast({"question": question, "options": options})
    return {"message": "Voted"}

@app.websocket("/ws/poll")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        question, options = fetch_poll()
        await websocket.send_json(jsonable_encoder({"question": question, "options": options}))
        while True:
            await asyncio.sleep(10) 
    except WebSocketDisconnect:
        manager.disconnect(websocket)
