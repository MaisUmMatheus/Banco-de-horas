from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Configuração inicial
DB = "banco_horas.db"
HORAS_INICIAIS = 40 * 60  # 40h em minutos
ALMOCO_ESPERADO = 90      # 1h30 em minutos

# Criar tabelas se não existirem
def init_db():
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        # Tabela principal (registros de almoço)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS almocos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            hora_saida TEXT,
            hora_retorno TEXT,
            tempo_almoco INTEGER,
            deficit INTEGER
        )
        """)
        # Tabela de semanas
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS semanas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            deficit_total INTEGER
        )
        """)
        conn.commit()

init_db()

# Função para calcular saldo e déficit acumulado
def calcular_saldo():
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(deficit) FROM almocos")
        total_deficit = cursor.fetchone()[0] or 0
        return HORAS_INICIAIS - total_deficit, total_deficit

# Página principal
@app.route("/")
def index():
    saldo, total_deficit = calcular_saldo()
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM almocos ORDER BY id DESC")
        registros = cursor.fetchall()

        cursor.execute("SELECT * FROM semanas ORDER BY id DESC")
        semanas = cursor.fetchall()

    return render_template("index.html", registros=registros, saldo=saldo, total_deficit=total_deficit, semanas=semanas)

# Adicionar registro de almoço
@app.route("/add", methods=["POST"])
def add():
    data = request.form["data"]
    hora_saida = request.form["hora_saida"]
    hora_retorno = request.form["hora_retorno"]

    # Calcular tempo de almoço
    formato = "%H:%M"
    t1 = datetime.strptime(hora_saida, formato)
    t2 = datetime.strptime(hora_retorno, formato)
    tempo_almoco = int((t2 - t1).total_seconds() / 60)

    # Déficit = quanto faltou para 90min
    deficit = max(0, ALMOCO_ESPERADO - tempo_almoco)

    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO almocos (data, hora_saida, hora_retorno, tempo_almoco, deficit) VALUES (?, ?, ?, ?, ?)",
            (data, hora_saida, hora_retorno, tempo_almoco, deficit)
        )
        conn.commit()

    return redirect("/")

# Excluir registro de almoço
@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM almocos WHERE id=?", (id,))
        conn.commit()
    return redirect("/")

# Resetar todos os registros
@app.route("/reset", methods=["POST"])
def reset():
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM almocos")
        conn.commit()
    return redirect("/")

# Adicionar semana
@app.route("/add_semana", methods=["POST"])
def add_semana():
    nome = request.form["nome"]
    _, total_deficit = calcular_saldo()

    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO semanas (nome, deficit_total) VALUES (?, ?)", (nome, total_deficit))
        conn.commit()

    return redirect("/")

# Excluir semana
@app.route("/delete_semana/<int:id>", methods=["POST"])
def delete_semana(id):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM semanas WHERE id=?", (id,))
        conn.commit()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
