import streamlit as st
import sqlite3
import pandas as pd
import hashlib
from datetime import datetime
import math

# --- 1. CONFIGURACIÓN DE LA BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('rebuilt_health.db')
    c = conn.cursor()
    # Tabla de Usuarios (Cambiado a username)
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, nombre TEXT, sexo TEXT, estatura REAL, edad INTEGER)''')
    # Tabla de Registros Diarios
    c.execute('''CREATE TABLE IF NOT EXISTS daily_logs
                 (username TEXT, fecha TEXT, peso REAL, cuello REAL, cintura REAL, cadera REAL, ingesta_kcal REAL, calorias_activas REAL)''')
    conn.commit()
    conn.close()

# --- 2. SEGURIDAD Y AUTENTICACIÓN ---
def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def verify_login(username, password):
    conn = sqlite3.connect('rebuilt_health.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user

def register_user(username, password, nombre, sexo, estatura, edad):
    conn = sqlite3.connect('rebuilt_health.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password, nombre, sexo, estatura, edad) VALUES (?, ?, ?, ?, ?, ?)',
                  (username, hash_password(password), nombre, sexo, estatura, edad))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False # El nombre de usuario ya existe

# --- 3. MOTORES DE CÁLCULO CLÍNICO ---
def calcular_grasa_naval(sexo, estatura, cuello, cintura, cadera=0):
    try:
        if sexo == 'H':
            return 495 / (1.0324 - 0.19077 * math.log10(cintura - cuello) + 0.15456 * math.log10(estatura)) - 450
        elif sexo == 'M':
            return 495 / (1.29579 - 0.35004 * math.log10(cintura + cadera - cuello) + 0.22100 * math.log10(estatura)) - 450
    except:
        return 0.0
    return 0.0

def calcular_katch_mcardle(peso, porcentaje_grasa):
    lbm = peso * (1 - (porcentaje_grasa / 100))
    tmb = 370 + (21.6 * lbm)
    return lbm, tmb

# --- 4. INTERFAZ DE USUARIO (UI) ---
st.set_page_config(page_title="Re/Built Health", layout="centered")

init_db()

# Control de Sesión
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# Variable temporal para pre-llenar el usuario tras el registro
if 'last_registered_user' not in st.session_state:
    st.session_state['last_registered_user'] = ""

if not st.session_state['logged_in']:
    st.title("RE/BUILT HEALTH")
    st.subheader("Sistema de Cuantificación Metabólica")
    
    menu = ["Iniciar Sesión", "Registrarse"]
    choice = st.sidebar.selectbox("Acceso", menu)
    
    if choice == "Iniciar Sesión":
        # Extrae el usuario de la memoria y fuerza la contraseña en blanco
        username = st.text_input("Nombre de Usuario", value=st.session_state['last_registered_user'], key="login_user")
        password = st.text_input("Contraseña", value="", type="password", key="login_pass")
        
        if st.button("Entrar"):
            user = verify_login(username, password)
            if user:
                st.session_state['logged_in'] = True
                st.session_state['username'] = user[0]
                st.session_state['nombre'] = user[2]
                st.session_state['sexo'] = user[3]
                st.session_state['estatura'] = user[4]
                st.rerun()
            else:
                st.error("Credenciales incorrectas.")
                
    elif choice == "Registrarse":
        st.write("Crea tu cuenta clínica")
        new_nombre = st.text_input("Nombre Completo", key="reg_nombre")
        new_username = st.text_input("Nombre de Usuario (Único)", key="reg_user")
        new_password = st.text_input("Contraseña", value="", type="password", key="reg_pass")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            new_sexo = st.selectbox("Sexo Biológico", ["H", "M"], key="reg_sexo")
        with col2:
            new_estatura = st.number_input("Estatura (cm)", min_value=100.0, max_value=250.0, step=0.1, key="reg_estatura")
        with col3:
            new_edad = st.number_input("Edad", min_value=15, max_value=100, step=1, key="reg_edad")
            
        # Bloque de Disclaimer y Consentimiento
        st.markdown("---")
        
        with st.expander("📄 Leer Consentimiento Informado y Términos de Uso completos"):
            st.markdown("""
            **1. Naturaleza de los Datos:**
            Los datos recopilados incluyen edad, sexo biológico, medidas antropométricas y registros diarios de ingesta y gasto calórico.
            
            **2. Uso para Investigación Científica:**
            Al utilizar esta plataforma, autorizas que tu información sea almacenada y utilizada de forma estrictamente anonimizada para investigaciones, publicaciones científicas y análisis estadísticos en el área de la salud.
            
            **3. Privacidad y Seguridad:**
            Tus datos de identidad directa (como tu nombre) no serán vinculados a tus métricas corporales en ninguna publicación o base de datos externa. La información se aloja en servidores seguros en la nube con acceso restringido.
            
            **4. Derecho a Revocación (Retiro):**
            El registro de datos es voluntario. Tienes el derecho de solicitar la eliminación total de tu información de nuestro repositorio investigativo en cualquier momento, sin necesidad de justificación y sin que esto afecte el uso futuro de la aplicación.
            
            **5. Responsabilidad y Contacto:**
            Esta plataforma es una herramienta de cuantificación y no sustituye la evaluación médica profesional. Para consultas sobre la privacidad de tu información o para ejercer tu derecho a eliminar tus datos del estudio, contáctanos a través de nuestro Instagram oficial: **@re_built_health**.
            """)

        st.markdown("**Consentimiento**")
        consentimiento = st.checkbox("He leído y acepto el consentimiento informado para el uso de datos en investigación.", key="reg_consent")
        st.markdown("---")
            
        if st.button("Crear Cuenta"):
            if not consentimiento:
                st.warning("Debes aceptar el consentimiento informado para crear una cuenta.")
            else:
                if register_user(new_username, new_password, new_nombre, new_sexo, new_estatura, new_edad):
                    st.success("Cuenta creada exitosamente. Selecciona 'Iniciar Sesión' en el menú lateral.")
                    st.session_state['last_registered_user'] = new_username
                else:
                    st.error("Este nombre de usuario ya está en uso.")

else:
    # --- DASHBOARD PRINCIPAL (Usuario Logueado) ---
    st.sidebar.title(f"Bienvenido, {st.session_state['nombre']}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state['logged_in'] = False
        st.rerun()
        
    st.title("Panel Clínico de Control")
    st.markdown("---")
    
    st.subheader("Ingreso de Datos Diarios")
    col1, col2 = st.columns(2)
    
    with col1:
        peso = st.number_input("Peso Total (kg)", min_value=30.0, max_value=200.0, value=70.0, step=0.1)
        cuello = st.number_input("Cuello (cm)", min_value=20.0, max_value=60.0, value=38.0, step=0.1)
        cintura = st.number_input("Cintura (cm)", min_value=40.0, max_value=150.0, value=80.0, step=0.1)
        
    with col2:
        cadera = 0.0
        if st.session_state['sexo'] == 'M':
            cadera = st.number_input("Cadera (cm)", min_value=50.0, max_value=150.0, step=0.1)
        else:
            st.text_input("Cadera (cm)", value="No requerido (Biología H)", disabled=True)
            
        ingesta = st.number_input("Ingesta Total (kcal)", min_value=0.0, step=10.0)
        activas = st.number_input("Calorías Activas (Apple Watch/Garmin)", min_value=0.0, step=10.0)
        
    if st.button("Calcular y Registrar"):
        # Ejecución matemática
        grasa = calcular_grasa_naval(st.session_state['sexo'], st.session_state['estatura'], cuello, cintura, cadera)
        lbm, tmb = calcular_katch_mcardle(peso, grasa)
        tdee = tmb + activas
        balance = ingesta - tdee
        
        # Guardar en base de datos (Lógica Upsert: Previene duplicados)
        conn = sqlite3.connect('rebuilt_health.db')
        c = conn.cursor()
        fecha_hoy = str(datetime.now().date())
        
        c.execute('SELECT * FROM daily_logs WHERE username=? AND fecha=?', (st.session_state['username'], fecha_hoy))
        registro_existente = c.fetchone()
        
        if registro_existente:
            c.execute('''UPDATE daily_logs 
                         SET peso=?, cuello=?, cintura=?, cadera=?, ingesta_kcal=?, calorias_activas=?
                         WHERE username=? AND fecha=?''',
                      (peso, cuello, cintura, cadera, ingesta, activas, st.session_state['username'], fecha_hoy))
        else:
            c.execute('INSERT INTO daily_logs VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                      (st.session_state['username'], fecha_hoy, peso, cuello, cintura, cadera, ingesta, activas))
                      
        conn.commit()
        conn.close()
        
        # Mostrar métricas
        st.markdown("### Resultados Metabólicos del Día")
        met1, met2, met3 = st.columns(3)
        met1.metric(label="Grasa Corporal (Naval)", value=f"{grasa:.1f} %")
        met2.metric(label="Masa Magra (LBM)", value=f"{lbm:.1f} kg")
        met3.metric(label="TMB (Katch-McArdle)", value=f"{tmb:.0f} kcal")
        
        met4, met5, met6 = st.columns(3)
        met4.metric(label="TDEE Dinámico", value=f"{tdee:.0f} kcal")
        met5.metric(label="Ingesta Registrada", value=f"{ingesta:.0f} kcal")
        met6.metric(label="Balance Diario", value=f"{balance:.0f} kcal", delta=f"{balance:.0f} kcal", delta_color="inverse")

    # --- HISTORIAL Y TENDENCIAS ---
    st.markdown("---")
    st.subheader("Auditoría Histórica")
    
    conn_hist = sqlite3.connect('rebuilt_health.db')
    query = '''
        SELECT fecha AS Fecha, peso AS Peso_kg, cuello AS Cuello_cm, cintura AS Cintura_cm, cadera AS Cadera_cm,
               ingesta_kcal AS Ingesta, calorias_activas AS Gasto_Activo 
        FROM daily_logs 
        WHERE username=? 
        ORDER BY fecha ASC
    '''
    df_historial = pd.read_sql_query(query, conn_hist, params=(st.session_state.get('username', ''),))
    conn_hist.close()
    
    if not df_historial.empty:
        # Calcular el % de Grasa dinámicamente para toda la matriz histórica
        df_historial['% Grasa'] = df_historial.apply(
            lambda row: calcular_grasa_naval(
                st.session_state['sexo'], 
                st.session_state['estatura'], 
                row['Cuello_cm'], 
                row['Cintura_cm'], 
                row['Cadera_cm']
            ), axis=1
        ).round(1)
        
        # Reordenar las columnas para priorizar las métricas clave de progreso
        columnas_visibles = ['Fecha', 'Peso_kg', '% Grasa', 'Cuello_cm', 'Cintura_cm', 'Cadera_cm', 'Ingesta', 'Gasto_Activo']
        df_mostrar = df_historial[columnas_visibles]
        
        st.dataframe(df_mostrar, use_container_width=True)
        
        # Gráficos de tendencia paralelos
        col_graf1, col_graf2 = st.columns(2)
        with col_graf1:
            st.markdown("### Tendencia de Peso (kg)")
            st.line_chart(df_historial.set_index('Fecha')['Peso_kg'], color="#2563EB")
        with col_graf2:
            st.markdown("### Tendencia de Grasa (%)")
            st.line_chart(df_historial.set_index('Fecha')['% Grasa'], color="#10B981")
    else:
        st.info("La matriz de datos está vacía. Comienza tu registro.")