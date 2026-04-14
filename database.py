import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "vitor_empire.db"


def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS rdps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        cliente TEXT,
        projeto TEXT,
        efetividade REAL,
        h_espera REAL,
        total_h REAL,
        status TEXT,
        risco_atraso TEXT,
        nps_score REAL,
        timestamp TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS study_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        horas_estudo REAL,
        questoes_resolvidas INTEGER,
        acertos INTEGER,
        topicos TEXT,
        timestamp TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS career_goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meta TEXT,
        prazo TEXT,
        progresso REAL,
        categoria TEXT,
        timestamp TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS flashcards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        termo_pt TEXT,
        termo_de TEXT,
        pronuncia TEXT,
        frase_corporativa TEXT,
        nivel TEXT,
        timestamp TEXT
    )''')

    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# INSERTS
# ─────────────────────────────────────────────

def save_rdp(data, cliente, projeto, efetividade, h_espera,
             total_h, status, risco_atraso, nps_score):

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        INSERT INTO rdps (
            data, cliente, projeto, efetividade,
            h_espera, total_h, status, risco_atraso,
            nps_score, timestamp
        ) VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (
        str(data), cliente, projeto, float(efetividade),
        float(h_espera), float(total_h), status,
        risco_atraso, float(nps_score),
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


def save_study(data, horas, questoes, acertos, topicos):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        INSERT INTO study_logs (
            data, horas_estudo, questoes_resolvidas,
            acertos, topicos, timestamp
        ) VALUES (?,?,?,?,?,?)
    """, (
        str(data), float(horas), int(questoes),
        int(acertos), topicos,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


def save_career_goal(meta, prazo, progresso, categoria):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        INSERT INTO career_goals (
            meta, prazo, progresso, categoria, timestamp
        ) VALUES (?,?,?,?,?)
    """, (
        meta, str(prazo), float(progresso),
        categoria, datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


def update_goal_progress(goal_id, progresso):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        UPDATE career_goals SET progresso=? WHERE id=?
    """, (float(progresso), int(goal_id)))

    conn.commit()
    conn.close()


def save_flashcard(termo_pt, termo_de, pronuncia, frase, nivel="B1"):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        INSERT INTO flashcards (
            termo_pt, termo_de, pronuncia,
            frase_corporativa, nivel, timestamp
        ) VALUES (?,?,?,?,?,?)
    """, (
        termo_pt, termo_de, pronuncia,
        frase, nivel, datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# GETTERS
# ─────────────────────────────────────────────

def get_history():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM rdps ORDER BY data DESC", conn)
    conn.close()
    return df


def get_study_history():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM study_logs ORDER BY data DESC", conn)
    conn.close()
    return df


def get_career_goals():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM career_goals ORDER BY prazo ASC", conn)
    conn.close()
    return df


def get_flashcards():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM flashcards ORDER BY timestamp DESC", conn)
    conn.close()
    return df


# ─────────────────────────────────────────────
# STATS
# ─────────────────────────────────────────────

def get_rdp_stats():
    conn = get_connection()
    c = conn.cursor()

    stats = {}

    c.execute("SELECT COUNT(*) FROM rdps")
    stats['total_rdps'] = c.fetchone()[0]

    c.execute("SELECT AVG(efetividade) FROM rdps")
    val = c.fetchone()[0]
    stats['avg_efetividade'] = round(val, 1) if val else 0

    c.execute("SELECT AVG(nps_score) FROM rdps")
    val = c.fetchone()[0]
    stats['avg_nps'] = round(val, 1) if val else 0

    c.execute("SELECT COUNT(*) FROM rdps WHERE status='On Track'")
    stats['on_track'] = c.fetchone()[0]

    conn.close()
    return stats