import sqlite3
import pandas as pd

def create_tables():
    conn = sqlite3.connect('vitor_empire.db')
    c = conn.cursor()
    # Tabela de RDPs (Trabalho na Dürr)
    c.execute('''CREATE TABLE IF NOT EXISTS rdps 
                 (id INTEGER PRIMARY KEY, data TEXT, atividade TEXT, status TEXT)''')
    # Tabela de Estudos (FUVEST)
    c.execute('''CREATE TABLE IF NOT EXISTS estudos 
                 (id INTEGER PRIMARY KEY, materia TEXT, horas REAL, data TEXT)''')
    conn.commit()
    conn.close()

def save_rdp(data, atividade, status):
    conn = sqlite3.connect('vitor_empire.db')
    c = conn.cursor()
    c.execute("INSERT INTO rdps (data, atividade, status) VALUES (?, ?, ?)", (data, atividade, status))
    conn.commit()
    conn.close()

# Inicializa o banco ao carregar
create_tables()
