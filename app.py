from flask import Flask, render_template, request, redirect, send_file, session
import mysql.connector
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "supersecreto"  # Necesario para login y sesiones

# 🔹 Conexión a MySQL
db = mysql.connector.connect(
    host="localhost",
    user="root",         # tu usuario MySQL
    password="inframen2025",     # tu contraseña MySQL
    database="pupuseria_db"
)
cursor = db.cursor()

# ---------------- RUTA MENÚ ----------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        nombre = request.form["nombre"]
        telefono = request.form.get("telefono", "")

        pedidos = [
            ("Frijol con Queso", int(request.form.get("frijol", 0))),
            ("Revueltas", int(request.form.get("revueltas", 0))),
            ("Especialidad de la casa", int(request.form.get("especial", 0)))
        ]
        fecha = datetime.now()

        for pupusa, cantidad in pedidos:
            if cantidad > 0:
                cursor.execute(
                    "INSERT INTO pedidos (nombre, telefono, pupusa, cantidad, fecha) VALUES (%s, %s, %s, %s, %s)",
                    (nombre, telefono, pupusa, cantidad, fecha)
                )
                db.commit()

        return redirect("/")

    return render_template("index.html")

# ---------------- LOGIN ADMIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        password = request.form["password"]

        if usuario == "admin" and password == "tuks123":
            session["admin"] = True
            return redirect("/admin")
        else:
            return render_template("login.html", error="Usuario o contraseña incorrectos")

    return render_template("login.html")

# ---------------- PANEL ADMIN ----------------
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/login")

    cursor.execute("SELECT * FROM pedidos ORDER BY fecha DESC")
    pedidos = cursor.fetchall()

    df = pd.DataFrame(pedidos, columns=["ID", "Nombre", "Teléfono", "Pupusa", "Cantidad", "Fecha"])
    excel_path = "pedidos.xlsx"

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Pedidos")
        resumen = df.groupby("Pupusa")["Cantidad"].sum().reset_index()
        resumen.to_excel(writer, index=False, sheet_name="Resumen")

    resumen_list = resumen.values.tolist()
    return render_template("admin.html", pedidos=pedidos, resumen=resumen_list)

# ---------------- EXPORTAR EXCEL ----------------
@app.route("/export_excel")
def export_excel():
    if not session.get("admin"):
        return redirect("/login")

    excel_path = "pedidos.xlsx"
    if os.path.exists(excel_path):
        return send_file(excel_path, as_attachment=True)
    else:
        return "No hay archivo de pedidos disponible aún."

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/")
    
# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
