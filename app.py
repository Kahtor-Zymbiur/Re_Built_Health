import streamlit as st
import pandas as pd
import hashlib
from datetime import datetime
import math
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# --- 1. CONFIGURACIÓN DE LA BASE DE DATOS ---
@st.cache_resource
def conectar_gsheets():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    credenciales_dict = json.loads(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credenciales_dict, scope)
    cliente = gspread.authorize(creds)
    return cliente.open_by_url("https://docs.google.com/spreadsheets/d/1qh9cq3nPmYEtnQ_QQGXC1F4Ik0UQKI0eI4WeAGmrZ_c/edit?gid=0#gid=0")

# Inicializar la conexión a las pestañas
hoja_principal = conectar_gsheets()
pestaña_usuarios = hoja_principal.worksheet("Usuarios")
pestaña_registros = hoja_principal.worksheet("Registros")
pestaña_codigos = hoja_principal.worksheet("Códigos")

# --- FUNCIÓN DE LECTURA SEGURA PARA EVITAR CRASH DE GSPREAD ---
def obtener_registros_seguro(pestaña):
    try:
        return pestaña.get_all_records()
    except IndexError:
        return []

# --- 2. SEGURIDAD, AUTENTICACIÓN Y CÓDIGOS ---
def verificar_y_quemar_codigo(codigo_ingresado):
    try:
        celda_codigo = pestaña_codigos.find(codigo_ingresado, in_column=1)
        if celda_codigo:
            fila = celda_codigo.row
            estado = pestaña_codigos.cell(fila, 2).value
            
            if estado == "Usado":
                pestaña_codigos.update_cell(fila, 2, "Activado")
                return True, "Código validado correctamente."
            elif estado == "Activado":
                return False, "Este código ya fue utilizado para crear una cuenta."
            elif estado == "Disponible":
                return False, "Este código aún no ha sido autorizado por una compra."
            else:
                return False, "El estado del código no es válido."
    except gspread.exceptions.CellNotFound:
        return False, "Código inválido o inexistente. Verifica que esté bien escrito."
    
    return False, "Error desconocido al verificar el código."

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def verify_login(username, password):
    hashed_pw = hash_password(password)
    usuarios = obtener_registros_seguro(pestaña_usuarios)
    
    for user in usuarios:
        if str(user['username']) == username and str(user['password']) == hashed_pw:
            return (user['username'], user['password'], user['nombre'], user['sexo'], user['estatura'], user['edad'])
    return None

def register_user(username, password, nombre, sexo, estatura, edad):
    hashed_pw = hash_password(password)
    nueva_fila = [username, hashed_pw, nombre, sexo, float(estatura), int(edad)]
    pestaña_usuarios.append_row(nueva_fila)
    return True

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

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if 'last_registered_user' not in st.session_state:
    st.session_state['last_registered_user'] = ""

if not st.session_state['logged_in']:
    st.title("RE/BUILT HEALTH")
    st.subheader("Sistema de Cuantificación Metabólica")
    
    menu = ["Iniciar Sesión", "Registrarse"]
    choice = st.sidebar.selectbox("Acceso", menu)
    
    if choice == "Iniciar Sesión":
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
        
        new_codigo = st.text_input("Código de Acceso Único (Recibido por correo)", key="reg_codigo")
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
            elif not new_codigo:
                st.warning("Debes ingresar el código de acceso enviado a tu correo.")
            else:
                usuarios_existentes = pestaña_usuarios.col_values(1)
                if new_username in usuarios_existentes:
                    st.error("Este nombre de usuario ya está en uso. Por favor elige otro.")
                else:
                    es_valido, msj_codigo = verificar_y_quemar_codigo(new_codigo)
                    
                    if es_valido:
                        register_user(new_username, new_password, new_nombre, new_sexo, new_estatura, new_edad)
                        st.success("Cuenta creada exitosamente. Selecciona 'Iniciar Sesión' en el menú lateral.")
                        st.session_state['last_registered_user'] = new_username
                    else:
                        st.error(msj_codigo)

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
        grasa = calcular_grasa_naval(st.session_state['sexo'], st.session_state['estatura'], cuello, cintura, cadera)
        lbm, tmb = calcular_katch_mcardle(peso, grasa)
        tdee = tmb + activas
        balance = ingesta - tdee
        
        fecha_hoy = str(datetime.now().date())
        username_actual = st.session_state['username']
        
        registros_existentes = obtener_registros_seguro(pestaña_registros)
        
        fila_a_actualizar = None
        for i, registro in enumerate(registros_existentes):
            if str(registro['username']) == username_actual and str(registro['fecha']) == fecha_hoy:
                fila_a_actualizar = i + 2
                break
                
        nueva_fila = [username_actual, fecha_hoy, peso, "", cuello, cintura, cadera, ingesta, activas]
        
        if fila_a_actualizar:
            rango = f"A{fila_a_actualizar}:I{fila_a_actualizar}"
            pestaña_registros.update(rango, [nueva_fila])
        else:
            pestaña_registros.append_row(nueva_fila)
        
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
    
    todos_los_registros = obtener_registros_seguro(pestaña_registros)
    datos_usuario = [r for r in todos_los_registros if str(r.get('username', '')).strip() == st.session_state.get('username', '')]
    
    df_historial = pd.DataFrame(datos_usuario)
    
    if not df_historial.empty:
        # 1. Limpiar columnas (quitar espacios invisibles y forzar minúsculas) para evitar el KeyError
        df_historial.columns = [str(col).strip().lower() for col in df_historial.columns]
        
        # 2. Renombrar al formato oficial de la UI
        df_historial = df_historial.rename(columns={
            'fecha': 'Fecha',
            'peso': 'peso_kg',
            'cuello': 'cuello_cm',
            'cintura': 'cintura_cm',
            'cadera': 'cadera_cm',
            'ingesta': 'ingesta',
            'activas': 'gasto_activo'
        })
        
        # 3. Validación defensiva: Si Sheets no envió alguna columna, la creamos artificialmente
        cols_numericas = ['Fecha', 'peso_kg', 'cuello_cm', 'cintura_cm', 'cadera_cm', 'ingesta', 'gasto_activo']
        for col in cols_numericas:
            if col not in df_historial.columns:
                # Si falta la fecha, ponemos la de hoy; si falta un número, ponemos 0
                df_historial[col] = str(datetime.now().date()) if col == 'Fecha' else 0
                
        # 4. Forzar formato numérico resolviendo el conflicto de las comas decimales
        cols_numericas = ['peso_kg', 'cuello_cm', 'cintura_cm', 'cadera_cm', 'ingesta', 'gasto_activo']
        for col in cols_numericas:
            # Convertir a texto, cambiar coma por punto y luego transformar a número matemático
            df_historial[col] = df_historial[col].astype(str).str.replace(',', '.')
            df_historial[col] = pd.to_numeric(df_historial[col], errors='coerce').fillna(0)
        
        # 5. Ordenar por fecha cronológica
        df_historial['Fecha_dt'] = pd.to_datetime(df_historial['Fecha'], errors='coerce')
        df_historial = df_historial.sort_values(by='Fecha_dt')
        
        # 6. Calcular Grasa
        df_historial['% Grasa'] = df_historial.apply(
            lambda row: calcular_grasa_naval(
                st.session_state['sexo'], 
                st.session_state['estatura'], 
                row['cuello_cm'], 
                row['cintura_cm'], 
                row['cadera_cm']
            ), axis=1
        ).round(1)
        
        # 7. Despliegue en pantalla
        columnas_visibles = ['Fecha', 'Peso_kg', '% Grasa', 'Cuello_cm', 'Cintura_cm', 'Cadera_cm', 'Ingesta', 'Gasto_Activo']
        df_mostrar = df_historial[columnas_visibles]
        
        st.dataframe(df_mostrar, use_container_width=True)
        
        col_graf1, col_graf2 = st.columns(2)
        with col_graf1:
            st.markdown("### Tendencia de Peso (kg)")
            st.line_chart(df_historial.set_index('Fecha')['Peso_kg'], color="#2563EB")
        with col_graf2:
            st.markdown("### Tendencia de Grasa (%)")
            st.line_chart(df_historial.set_index('Fecha')['% Grasa'], color="#10B981")
    else:
        st.info("La matriz de datos está vacía. Comienza tu registro.")