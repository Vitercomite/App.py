import sqlite3

def init_db():
    conn = sqlite3.connect('vitor_empire.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rdps 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, atividade TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS estudos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, materia TEXT, horas REAL, data TEXT)''')
    conn.commit()
    conn.close()

def save_rdp(data, atividade, status):
    conn = sqlite3.connect('vitor_empire.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("INSERT INTO rdps (data, atividade, status) VALUES (?, ?, ?)", (data, atividade, status))
    conn.commit()
    conn.close()

def get_rdps():
    conn = sqlite3.connect('vitor_empire.db', check_same_thread=False)
    df = pd.read_sql_query("SELECT * FROM rdps", conn)
    conn.close()
    return df

def save_estudo(materia, horas, data):
    conn = sqlite3.connect('vitor_empire.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("INSERT INTO estudos (materia, horas, data) VALUES (?, ?, ?)", (materia, horas, data))
    conn.commit()
    conn.close()

# Executa a criação das tabelas ao importar
init_db()
