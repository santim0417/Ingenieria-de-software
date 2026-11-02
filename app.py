from flask import Flask, render_template, request, redirect, url_for, flash, session
import re

app = Flask(__name__)
app.secret_key = 'clave_secreta_sicapp_qa'

# Base de Datos Sintética de Prueba (Seeding QA - TC-SIC9-01)
USUARIOS_DB = {
    "maria.giraldo663@pascualbravo.edu.co": {
        "password": "Password123",  # 11 caracteres (Válida: 8-16)
        "nombre": "MARIA YAZMIN GIRALDO SALAZAR",
        "documento": "1037498663 CC",
        "carrera": "028 - TECNOLOGÍA EN DESARROLLO DE SOFTWARE",
        "jornada": "JORNADA ÚNICA",
        "rol": "ESTUDIANTE",
        "intentos_fallidos": 0,
        "bloqueado": False
    },
    "santiago.moreno@pascualbravo.edu.co": {
        "password": "DocentePass1",
        "nombre": "SANTIAGO MORENO SARMIENTO",
        "documento": "1098765432 CC",
        "carrera": "DOCENTE DEPARTAMENTO DE SISTEMAS",
        "jornada": "COMPLETA",
        "rol": "DOCENTE",
        "intentos_fallidos": 0,
        "bloqueado": False
    }
}

def es_correo_valido(email):
    regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(regex, email) is not None

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        # TC-SIC8-02: Validación de formato de correo
        if not es_correo_valido(email):
            flash("Error: Formato de correo electrónico no válido", "danger")
            return render_template('login.html')

        # TC-SIC2-01 y TC-SIC2-03: Validación de longitud de contraseña (BVA)
        if len(password) < 8:
            flash("Error: La contraseña debe contener al menos 8 caracteres.", "danger")
            return render_template('login.html')
        elif len(password) > 16:
            flash("Error: La contraseña no puede superar los 16 caracteres.", "danger")
            return render_template('login.html')

        user = USUARIOS_DB.get(email)

        if not user:
            flash("Error: Credenciales inválidas.", "danger")
            return render_template('login.html')

        # TC-SIC2-06: Verificación de Bloqueo por Intentos Fallidos
        if user['bloqueado']:
            flash("Error: Cuenta Bloqueada temporalmente por 3 intentos fallidos consecutivos. Alerta de seguridad emitida.", "danger")
            return render_template('login.html')

        # TC-SIC2-04 y TC-SIC2-05: Validación de Credenciales (Tabla de Decisión)
        if user['password'] == password:
            user['intentos_fallidos'] = 0
            session['usuario'] = user
            session['device_token_push'] = "FCM_TOKEN_SIMULATED_2026_XYZ"
            return redirect(url_for('home'))
        else:
            user['intentos_fallidos'] += 1
            if user['intentos_fallidos'] >= 3:
                user['bloqueado'] = True
                flash("Error: Cuenta Bloqueada temporalmente al 3er intento fallido consecutivo.", "danger")
            else:
                intentos_restantes = 3 - user['intentos_fallidos']
                flash(f"Error: Credenciales inválidas. Te quedan {intentos_restantes} intento(s).", "danger")
            return render_template('login.html')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    session.pop('device_token_push', None)
    flash("Sesión cerrada. Token Push desvinculado correctamente.", "info")
    return redirect(url_for('login'))

@app.route('/home')
def home():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('home.html', usuario=session['usuario'])

@app.route('/estudiantes')
def estudiantes():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('estudiantes.html', usuario=session['usuario'])

@app.route('/extension')
def extension():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('extension.html', usuario=session['usuario'])

@app.route('/gestion-notas')
def gestion_notas():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    usuario = session['usuario']
    if usuario['rol'] != 'DOCENTE':
        return render_template('403.html', usuario=usuario), 403
    
    return render_template('gestion_notas.html', usuario=usuario)

if __name__ == '__main__':
    app.run(debug=True, port=5000)