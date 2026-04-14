import sqlite3
import pandas as pd

def init_db():
    conn = sqlite3.connect('vitor_empire.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rdps 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, cliente TEXT, atividade TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS estudos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, materia TEXT, horas REAL, data TEXT)''')
    conn.commit()
    conn.close()

def save_rdp(data, cliente, atividade, status):
    conn = sqlite3.connect('vitor_empire.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("INSERT INTO rdps (data, cliente, atividade, status) VALUES (?, ?, ?, ?)", 
              (data, cliente, atividade, status))
    conn.commit()
    conn.close()

def get_rdps():
    conn = sqlite3.connect('vitor_empire.db', check_same_thread=False)
    df = pd.read_sql_query("SELECT * FROM rdps ORDER BY data DESC", conn)
    conn.close()
    return df

def save_estudo(materia, horas, data):
    conn = sqlite3.connect('vitor_empire.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("INSERT INTO estudos (materia, horas, data) VALUES (?, ?, ?)", (materia, horas, data))
    conn.commit()
    conn.close()

def get_estudos():
    conn = sqlite3.connect('vitor_empire.db', check_same_thread=False)
    df = pd.read_sql_query("SELECT * FROM estudos ORDER BY data DESC", conn)
    conn.close()
    return df
