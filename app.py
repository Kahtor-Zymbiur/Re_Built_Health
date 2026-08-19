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

hoja_principal = conectar_gsheets()
pestaña_usuarios = hoja_principal.worksheet("Usuarios")
pestaña_registros = hoja_principal.worksheet("Registros")
pestaña_codigos = hoja_principal.worksheet("Códigos")

# --- LECTURA SEGURA: EXTRACCIÓN CRUDA ---
def obtener_registros_seguro(pestaña):
    try:
        data = pestaña.get_all_values()
        if not data or len(data) < 2:
            return []
        
        encabezados = [str(col).strip().lower() for col in data[0]]
        df = pd.DataFrame(data[1:], columns=encabezados)
        return df.to_dict('records')
    except Exception:
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
        return False, "Código inválido o inexistente."
    
    return False, "Error desconocido."

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def verify_login(username, password):
    hashed_pw = hash_password(password)
    usuarios = obtener_registros_seguro(pestaña_usuarios)
    
    for user in usuarios:
        if str(user.get('username', '')) == username and str(user.get('password', '')) == hashed_pw:
            estatura_segura = float(str(user.get('estatura', '170')).replace(',', '.'))
            return (user['username'], user['password'], user.get('nombre', ''), user.get('sexo', 'H'), estatura_segura, user.get('edad', 0))
    return None

def register_user(username, password, nombre, sexo, estatura, edad):
    hashed_pw = hash_password(password)
    nueva_fila = [username, hashed_pw, nombre, sexo, float(estatura), int(edad)]
    pestaña_usuarios.append_row(nueva_fila)
    return True

# --- 3. MOTORES DE CÁLCULO CLÍNICO ---
def calcular_grasa_naval(sexo, estatura, cuello, cintura, cadera=0):
    try:
        est = float(str(estatura).replace(',', '.'))
        cue = float(str(cuello).replace(',', '.'))
        cin = float(str(cintura).replace(',', '.'))
        cad = float(str(cadera).replace(',', '.'))
        
        if cin <= cue: return 0.0
            
        if sexo == 'H':
            return 495 / (1.0324 - 0.19077 * math.log10(cin - cue) + 0.15456 * math.log10(est)) - 450
        elif sexo == 'M':
            if (cin + cad) <= cue: return 0.0
            return 495 / (1.29579 - 0.35004 * math.log10(cin + cad - cue) + 0.22100 * math.log10(est)) - 450
    except Exception:
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
        
        with st.expander("📄 Leer Consentimiento Informado"):
            st.markdown("Al utilizar esta plataforma, autorizas que tu información sea almacenada y utilizada de forma estrictamente anonimizada para investigaciones en el área de la salud.")

        consentimiento = st.checkbox("He leído y acepto el consentimiento informado.", key="reg_consent")
        st.markdown("---")
            
        if st.button("Crear Cuenta"):
            if not consentimiento:
                st.warning("Debes aceptar el consentimiento informado.")
            elif not new_codigo:
                st.warning("Debes ingresar tu código.")
            else:
                usuarios_existentes = [str(u.get('username', '')) for u in obtener_registros_seguro(pestaña_usuarios)]
                if new_username in usuarios_existentes:
                    st.error("Nombre de usuario en uso.")
                else:
                    es_valido, msj_codigo = verificar_y_quemar_codigo(new_codigo)
                    if es_valido:
                        register_user(new_username, new_password, new_nombre, new_sexo, new_estatura, new_edad)
                        st.success("Cuenta creada. Inicia sesión.")
                        st.session_state['last_registered_user'] = new_username
                    else:
                        st.error(msj_codigo)

else:
    st.sidebar.title(f"Bienvenido, {st.session_state.get('nombre', '')}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state['logged_in'] = False
        st.rerun()
        
    st.title("Panel Clínico de Control")
    st.markdown("---")
    
    st.subheader("Ingreso de Datos Diarios")
    
    # Campo para seleccionar la fecha de registro
    fecha_ingreso = st.date_input("Fecha del Registro", value=datetime.now().date())
    
    col1, col2 = st.columns(2)
    
    with col1:
        peso = st.number_input("Peso Total (kg)", min_value=30.0, max_value=200.0, value=70.0, step=0.1)
        cuello = st.number_input("Cuello (cm)", min_value=20.0, max_value=60.0, value=38.0, step=0.1)
        cintura = st.number_input("Cintura (cm)", min_value=40.0, max_value=150.0, value=80.0, step=0.1)
        
    with col2:
        cadera = 0.0
        if st.session_state.get('sexo', 'H') == 'M':
            cadera = st.number_input("Cadera (cm)", min_value=50.0, max_value=150.0, step=0.1)
        else:
            st.text_input("Cadera (cm)", value="No requerido (Biología H)", disabled=True)
            
        ingesta = st.number_input("Ingesta Total (kcal)", min_value=0.0, step=10.0)
        activas = st.number_input("Calorías Activas", min_value=0.0, step=10.0)
        
    if st.button("Calcular y Registrar"):
        grasa = calcular_grasa_naval(st.session_state['sexo'], st.session_state['estatura'], cuello, cintura, cadera)
        lbm, tmb = calcular_katch_mcardle(peso, grasa)
        tdee = tmb + activas
        balance = ingesta - tdee
        
        fecha_registro = str(fecha_ingreso)
        username_actual = st.session_state['username']
        
        registros_existentes = obtener_registros_seguro(pestaña_registros)
        
        fila_a_actualizar = None
        for i, registro in enumerate(registros_existentes):
            if str(registro.get('username', '')) == username_actual and str(registro.get('fecha', '')) == fecha_registro:
                fila_a_actualizar = i + 2
                break
                
        nueva_fila = [username_actual, fecha_registro, peso, cuello, cintura, cadera, ingesta, activas]
        
        if fila_a_actualizar:
            rango = f"A{fila_a_actualizar}:H{fila_a_actualizar}"
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
        df_historial = df_historial.rename(columns={
            'fecha': 'Fecha',
            'peso_kg': 'Peso_kg',
            'cuello_cm': 'Cuello_cm',
            'cintura_cm': 'Cintura_cm',
            'cadera_cm': 'Cadera_cm',
            'ingesta': 'Ingesta',
            'gasto_activo': 'Gasto_Activo'
        })
        
        cols_numericas = ['Peso_kg', 'Cuello_cm', 'Cintura_cm', 'Cadera_cm', 'Ingesta', 'Gasto_Activo']
        for col in cols_numericas:
            if col not in df_historial.columns:
                df_historial[col] = 0.0
            df_historial[col] = df_historial[col].astype(str).str.replace(',', '.')
            df_historial[col] = pd.to_numeric(df_historial[col], errors='coerce').fillna(0.0)
        
        if 'Fecha' not in df_historial.columns:
            df_historial['Fecha'] = str(datetime.now().date())
        df_historial['Fecha_dt'] = pd.to_datetime(df_historial['Fecha'], errors='coerce')
        df_historial = df_historial.sort_values(by='Fecha_dt')
        
        df_historial['% Grasa'] = df_historial.apply(
            lambda row: calcular_grasa_naval(
                st.session_state.get('sexo', 'H'), 
                st.session_state.get('estatura', 170.0), 
                row.get('Cuello_cm', 0.0), 
                row.get('Cintura_cm', 0.0), 
                row.get('Cadera_cm', 0.0)
            ), axis=1
        ).round(1)
        
        columnas_visibles = ['Fecha', 'Peso_kg', '% Grasa', 'Cuello_cm', 'Cintura_cm', 'Cadera_cm', 'Ingesta', 'Gasto_Activo']
        columnas_existentes = [c for c in columnas_visibles if c in df_historial.columns]
        df_mostrar = df_historial[columnas_existentes]
        
       # 1. Dashboard de Tendencia (Gráficos)
        st.markdown("#### Tendencias")
        filtro = st.radio(
            "Seleccionar período de visualización:", 
            ["7 Días", "1 Mes", "1 Año", "Historial Completo"], 
            horizontal=True
        )

        # Aplicar el filtro de tiempo sobre los datos
        fecha_actual = pd.to_datetime(datetime.now().date())
        if filtro == "7 Días":
            df_grafico = df_historial[df_historial['Fecha_dt'] >= (fecha_actual - pd.Timedelta(days=7))]
        elif filtro == "1 Mes":
            df_grafico = df_historial[df_historial['Fecha_dt'] >= (fecha_actual - pd.Timedelta(days=30))]
        elif filtro == "1 Año":
            df_grafico = df_historial[df_historial['Fecha_dt'] >= (fecha_actual - pd.Timedelta(days=365))]
        else:
            df_grafico = df_historial

        col_graf1, col_graf2 = st.columns(2)
        with col_graf1:
            st.markdown("#### Tendencia de Peso (kg)")
            if 'Peso_kg' in df_grafico.columns and not df_grafico.empty:
                st.line_chart(df_grafico.set_index('Fecha')['Peso_kg'], color="#2563EB")
            else:
                st.info("Sin datos en este período")
                
        with col_graf2:
            st.markdown("#### Tendencia de Grasa (%)")
            if '% Grasa' in df_grafico.columns and not df_grafico.empty:
                st.line_chart(df_grafico.set_index('Fecha')['% Grasa'], color="#10B981")
            else:
                st.info("Sin datos en este período")
                
        # 2. Tabla de Auditoría (Filtro de 7 días)
        st.markdown("#### Últimos 7 Registros")
        df_ultimos_7 = df_mostrar.tail(7)
        st.dataframe(df_ultimos_7, use_container_width=True)
        
        # 3. Exportación del Historial Completo
        csv_data = df_mostrar.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Historial Completo (CSV)",
            data=csv_data,
            file_name=f"Rebuilt_Historial_{st.session_state['username']}.csv",
            mime="text/csv"
        )
        
    else:
        st.info("La matriz de datos está vacía. Comienza tu registro.")