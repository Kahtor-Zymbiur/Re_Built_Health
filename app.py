import streamlit as st
import pandas as pd
import hashlib
from datetime import datetime, date
import math
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import fitz  # Librería PyMuPDF para el lector interactivo

# --- DICCIONARIO DE TRADUCCIONES ---
TEXTS = {
    'ES': {
        'title': 'RE/BUILT HEALTH',
        'subtitle': 'Sistema de Cuantificación Metabólica',
        'access': 'Acceso',
        'login_menu': 'Iniciar Sesión',
        'register_menu': 'Registrarse',
        'username': 'Nombre de Usuario',
        'password': 'Contraseña',
        'enter_btn': 'Entrar',
        'invalid_creds': 'Credenciales incorrectas.',
        'create_account': 'Crea tu cuenta clínica',
        'unique_code': 'Código de Acceso Único (Recibido por correo)',
        'fullname': 'Nombre Completo',
        'username_unique': 'Nombre de Usuario (Único)',
        'biological_sex': 'Sexo Biológico',
        'height': 'Estatura',
        'birthdate': 'Fecha de Nacimiento',
        'day': 'Día',
        'month': 'Mes',
        'year': 'Año',
        'invalid_date': 'Fecha inválida',
        'consent_title': '📄 Leer Consentimiento Informado',
        'consent_text': 'Al utilizar esta plataforma, autorizas que tu información sea almacenada y utilizada de forma estrictamente anonimizada para investigaciones en el área de la salud.',
        'consent_check': 'He leído y acepto el consentimiento informado.',
        'create_btn': 'Crear Cuenta',
        'consent_warn': 'Debes aceptar el consentimiento informado.',
        'code_warn': 'Debes ingresar tu código.',
        'user_in_use': 'Nombre de usuario en uso.',
        'account_created': 'Cuenta creada. Inicia sesión.',
        'welcome': 'Bienvenido',
        'logout': 'Cerrar Sesión',
        'panel_title': 'Panel Clínico de Control',
        'data_history': '📋 Datos y antecedentes metabólicos',
        'age': 'Edad',
        'years': 'años',
        'lean_mass': 'Masa Magra (Actual)',
        'bmr': 'TMB (Actual)',
        'daily_entry': '📝 Ingreso de Datos Diarios',
        'record_date': 'Fecha del Registro',
        'total_weight': 'Peso Total',
        'neck': 'Cuello',
        'waist': 'Cintura',
        'hip': 'Cadera',
        'not_required_m': 'No requerido (Biología H)',
        'total_intake': 'Ingesta Total (kcal)',
        'active_cals': 'Calorías Activas',
        'calc_register_btn': 'Calcular y Registrar',
        'daily_results': '### Resultados Metabólicos del Día',
        'body_fat': 'Grasa Corporal (Naval)',
        'dyn_tdee': 'TDEE Dinámico',
        'reg_intake': 'Ingesta Registrada',
        'daily_balance': 'Balance Diario',
        'audit_history': 'Auditoría Histórica',
        'trends': 'Tendencias',
        'select_period': 'Seleccionar período de visualización:',
        '7_days': '7 Días',
        '1_month': '1 Mes',
        '1_year': '1 Año',
        'full_history': 'Historial Completo',
        'weight_graph': '#### Peso',
        'fat_graph': '#### Grasa (%)',
        'no_data': 'Sin datos en este período',
        'last_7_records': '#### Últimos 7 Registros',
        'download_csv': '📥 Descargar Historial Completo (CSV)',
        'empty_matrix': 'La matriz de datos está vacía. Comienza tu registro.',
        'metric': 'Métrico (kg/cm)',
        'imperial': 'Imperial (lbs/in)',
        'lang_label': 'Idioma / Language',
        'unit_label': 'Sistema de Medidas',
        'reader_btn': '📖 Abrir Manual de Usuario',
        'prev': '⬅️ Anterior',
        'next': 'Siguiente ➡️',
        'page': 'Página',
        'of': 'de',
        'manual_error': 'Error al cargar el lector:',
        'pdf_not_found': 'El archivo no se encuentra en el servidor. Por favor, asegúrate de que esté en la carpeta.'
    },
    'EN': {
        'title': 'RE/BUILT HEALTH',
        'subtitle': 'Metabolic Quantification System',
        'access': 'Access',
        'login_menu': 'Login',
        'register_menu': 'Register',
        'username': 'Username',
        'password': 'Password',
        'enter_btn': 'Enter',
        'invalid_creds': 'Invalid credentials.',
        'create_account': 'Create your clinical account',
        'unique_code': 'Unique Access Code (Received via email)',
        'fullname': 'Full Name',
        'username_unique': 'Username (Unique)',
        'biological_sex': 'Biological Sex',
        'height': 'Height',
        'birthdate': 'Date of Birth',
        'day': 'Day',
        'month': 'Month',
        'year': 'Year',
        'invalid_date': 'Invalid date',
        'consent_title': '📄 Read Informed Consent',
        'consent_text': 'By using this platform, you authorize your information to be stored and used in a strictly anonymized manner for health research purposes.',
        'consent_check': 'I have read and accept the informed consent.',
        'create_btn': 'Create Account',
        'consent_warn': 'You must accept the informed consent.',
        'code_warn': 'You must enter your code.',
        'user_in_use': 'Username is already in use.',
        'account_created': 'Account created. Please log in.',
        'welcome': 'Welcome',
        'logout': 'Logout',
        'panel_title': 'Clinical Control Panel',
        'data_history': '📋 Metabolic Data & Background',
        'age': 'Age',
        'years': 'years',
        'lean_mass': 'Lean Mass (Current)',
        'bmr': 'BMR (Current)',
        'daily_entry': '📝 Daily Data Entry',
        'record_date': 'Record Date',
        'total_weight': 'Total Weight',
        'neck': 'Neck',
        'waist': 'Waist',
        'hip': 'Hips',
        'not_required_m': 'Not required (M Biology)',
        'total_intake': 'Total Intake (kcal)',
        'active_cals': 'Active Calories',
        'calc_register_btn': 'Calculate & Register',
        'daily_results': '### Daily Metabolic Results',
        'body_fat': 'Body Fat (Navy)',
        'dyn_tdee': 'Dynamic TDEE',
        'reg_intake': 'Registered Intake',
        'daily_balance': 'Daily Balance',
        'audit_history': 'Historical Audit',
        'trends': 'Trends',
        'select_period': 'Select visualization period:',
        '7_days': '7 Days',
        '1_month': '1 Month',
        '1_year': '1 Year',
        'full_history': 'Full History',
        'weight_graph': '#### Weight',
        'fat_graph': '#### Fat (%)',
        'no_data': 'No data in this period',
        'last_7_records': '#### Last 7 Records',
        'download_csv': '📥 Download Full History (CSV)',
        'empty_matrix': 'The data matrix is empty. Start your records.',
        'metric': 'Metric (kg/cm)',
        'imperial': 'Imperial (lbs/in)',
        'lang_label': 'Language',
        'unit_label': 'Measurement System',
        'reader_btn': '📖 Open User Manual',
        'prev': '⬅️ Previous',
        'next': 'Next ➡️',
        'page': 'Page',
        'of': 'of',
        'manual_error': 'Error loading reader:',
        'pdf_not_found': 'The file is not found on the server. Please ensure it is in the folder.'
    }
}

def t(key):
    lang = st.session_state.get('lang', 'ES')
    return TEXTS[lang].get(key, key)

# --- CONVERSORES DE UNIDADES ---
def to_kg(val, unit_sys): return val * 0.453592 if unit_sys == 'Imperial (lbs/in)' else val
def to_cm(val, unit_sys): return val * 2.54 if unit_sys == 'Imperial (lbs/in)' else val
def from_kg(val, unit_sys): return val / 0.453592 if unit_sys == 'Imperial (lbs/in)' else val
def from_cm(val, unit_sys): return val / 2.54 if unit_sys == 'Imperial (lbs/in)' else val

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
                return True, "Código validado correctamente." if st.session_state.lang == 'ES' else "Code validated successfully."
            elif estado == "Activado":
                return False, "Este código ya fue utilizado." if st.session_state.lang == 'ES' else "This code was already used."
            elif estado == "Disponible":
                return False, "Este código aún no ha sido autorizado." if st.session_state.lang == 'ES' else "Code not yet authorized."
            else:
                return False, "Estado inválido." if st.session_state.lang == 'ES' else "Invalid status."
    except gspread.exceptions.CellNotFound:
        return False, "Código inválido." if st.session_state.lang == 'ES' else "Invalid code."
    return False, "Error desconocido." if st.session_state.lang == 'ES' else "Unknown error."

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def verify_login(username, password):
    hashed_pw = hash_password(password)
    usuarios = obtener_registros_seguro(pestaña_usuarios)
    
    for user in usuarios:
        if str(user.get('username', '')) == username and str(user.get('password', '')) == hashed_pw:
            estatura_segura = float(str(user.get('estatura', '170')).replace(',', '.'))
            fecha_nac = user.get('fecha_nacimiento', user.get('edad', '1990-01-01'))
            return (user['username'], user['password'], user.get('nombre', ''), user.get('sexo', 'H'), estatura_segura, fecha_nac)
    return None

def register_user(username, password, nombre, sexo, estatura, fecha_nacimiento):
    hashed_pw = hash_password(password)
    nueva_fila = [username, hashed_pw, nombre, sexo, float(estatura), str(fecha_nacimiento)]
    pestaña_usuarios.append_row(nueva_fila)
    return True

# --- 3. MOTORES DE CÁLCULO CLÍNICO ---
def calcular_edad(fecha_nac_str):
    try:
        fn = datetime.strptime(str(fecha_nac_str).strip(), "%Y-%m-%d").date()
        hoy = datetime.now().date()
        return hoy.year - fn.year - ((hoy.month, hoy.day) < (fn.month, fn.day))
    except Exception:
        try:
            return int(fecha_nac_str)
        except:
            return 0

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

# --- CSS RESPONSIVO PARA FORZAR AL MODAL A OCUPAR TODA LA PANTALLA EN MÓVILES ---
st.markdown("""
    <style>
    /* Hace que la ventana flotante (modal) ocupe casi el 95% de la pantalla en dispositivos móviles y se adapte */
    div[data-testid="stModal"] > div {
        width: 95vw !important;
        max-width: 900px !important;
        height: 90vh !important;
        top: 5vh !important;
    }
    </style>
""", unsafe_allow_html=True)

# Inicializar estados
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'last_registered_user' not in st.session_state: st.session_state['last_registered_user'] = ""
if 'lang' not in st.session_state: st.session_state['lang'] = 'ES'
if 'unit_sys' not in st.session_state: st.session_state['unit_sys'] = 'Métrico (kg/cm)'

# Controles globales en el sidebar
st.sidebar.markdown(f"**{t('lang_label')}**")
lang_sel = st.sidebar.radio("Idioma", ['ES', 'EN'], index=0 if st.session_state['lang'] == 'ES' else 1, label_visibility="collapsed")
if lang_sel != st.session_state['lang']:
    st.session_state['lang'] = lang_sel
    st.rerun()

st.sidebar.markdown(f"**{t('unit_label')}**")
unit_opts = ['Métrico (kg/cm)', 'Imperial (lbs/in)']
unit_idx = 0 if st.session_state['unit_sys'] == 'Métrico (kg/cm)' else 1
unit_sel = st.sidebar.radio("Sistema", unit_opts, index=unit_idx, label_visibility="collapsed")
if unit_sel != st.session_state['unit_sys']:
    st.session_state['unit_sys'] = unit_sel
    st.rerun()

sys = st.session_state['unit_sys']
w_unit = "kg" if sys == 'Métrico (kg/cm)' else "lbs"
d_unit = "cm" if sys == 'Métrico (kg/cm)' else "in"

# --- VENTANA EMERGENTE (MODAL) ADAPTABLE ---
@st.dialog("📖 Manual de Usuario / User Manual", width="large")
def abrir_modal_manual():
    if st.session_state.get('lang', 'ES') == 'EN':
        ruta_manual = "manual_en.pdf"
    else:
        ruta_manual = "manual_es.pdf"

    try:
        doc = fitz.open(ruta_manual)
        total_paginas = len(doc)
        
        if 'pagina_actual' not in st.session_state:
            st.session_state['pagina_actual'] = 0
            st.session_state['pdf_cargado'] = ruta_manual
            
        if st.session_state.get('pdf_cargado') != ruta_manual:
            st.session_state['pagina_actual'] = 0
            st.session_state['pdf_cargado'] = ruta_manual

        col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
        
        with col_nav1:
            # Eliminado st.rerun()
            if st.button(t('prev')) and st.session_state['pagina_actual'] > 0:
                st.session_state['pagina_actual'] -= 1
                
        with col_nav2:
            st.markdown(f"<p style='text-align: center; font-weight: bold;'>{t('page')} {st.session_state['pagina_actual'] + 1} {t('of')} {total_paginas}</p>", unsafe_allow_html=True)
            
        with col_nav3:
            # Eliminado st.rerun()
            if st.button(t('next')) and st.session_state['pagina_actual'] < total_paginas - 1:
                st.session_state['pagina_actual'] += 1

        pagina = doc.load_page(st.session_state['pagina_actual'])
        imagen_pagina = pagina.get_pixmap(dpi=150)
        
        st.image(imagen_pagina.tobytes(), use_container_width=True)

    except FileNotFoundError:
        st.info(f"{t('pdf_not_found')} ('{ruta_manual}')")
    except Exception as e:
        st.error(f"{t('manual_error')} {e}")

if not st.session_state['logged_in']:
    st.title(t('title'))
    st.subheader(t('subtitle'))
    
    menu_options = [t('login_menu'), t('register_menu')]
    choice = st.sidebar.selectbox(t('access'), menu_options)
    
    if choice == t('login_menu'):
        username = st.text_input(t('username'), value=st.session_state['last_registered_user'], key="login_user")
        password = st.text_input(t('password'), value="", type="password", key="login_pass")
        
        if st.button(t('enter_btn')):
            user = verify_login(username, password)
            if user:
                st.session_state['logged_in'] = True
                st.session_state['username'] = user[0]
                st.session_state['nombre'] = user[2]
                st.session_state['sexo'] = user[3]
                st.session_state['estatura'] = user[4]
                st.session_state['fecha_nacimiento'] = user[5]
                st.rerun()
            else:
                st.error(t('invalid_creds'))
                
    elif choice == t('register_menu'):
        st.write(t('create_account'))
        
        new_codigo = st.text_input(t('unique_code'), key="reg_codigo")
        new_nombre = st.text_input(t('fullname'), key="reg_nombre")
        new_username = st.text_input(t('username_unique'), key="reg_user")
        new_password = st.text_input(t('password'), value="", type="password", key="reg_pass")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            sex_options = ["H", "M"]
            new_sexo = st.selectbox(t('biological_sex'), sex_options, key="reg_sexo")
        with col2:
            min_h, max_h, def_h = (100.0, 250.0, 170.0) if sys == 'Métrico (kg/cm)' else (39.0, 98.0, 67.0)
            new_estatura_ui = st.number_input(f"{t('height')} ({d_unit})", min_value=min_h, max_value=max_h, value=def_h, step=0.1, key="reg_estatura")
            new_estatura_cm = to_cm(new_estatura_ui, sys)
            
        with col3:
            st.markdown(f"<span style='font-size: 14px;'>{t('birthdate')}</span>", unsafe_allow_html=True)
            c_dia, c_mes, c_ano = st.columns(3)
            with c_dia:
                dia = st.selectbox(t('day'), list(range(1, 32)), key="reg_dia")
            with c_mes:
                mes = st.selectbox(t('mes'), list(range(1, 13)), key="reg_mes")
            with c_ano:
                ano = st.selectbox(t('year'), list(range(datetime.now().year, 1919, -1)), index=36, key="reg_ano")
            
            try:
                new_fecha_nac = date(ano, mes, dia)
            except ValueError:
                st.error(t('invalid_date'))
                new_fecha_nac = date(1990, 1, 1)
            
        st.markdown("---")
        
        with st.expander(t('consent_title')):
            st.markdown(t('consent_text'))

        consentimiento = st.checkbox(t('consent_check'), key="reg_consent")
        st.markdown("---")
            
        if st.button(t('create_btn')):
            if not consentimiento:
                st.warning(t('consent_warn'))
            elif not new_codigo:
                st.warning(t('code_warn'))
            else:
                usuarios_existentes = [str(u.get('username', '')) for u in obtener_registros_seguro(pestaña_usuarios)]
                if new_username in usuarios_existentes:
                    st.error(t('user_in_use'))
                else:
                    es_valido, msj_codigo = verificar_y_quemar_codigo(new_codigo)
                    if es_valido:
                        register_user(new_username, new_password, new_nombre, new_sexo, new_estatura_cm, new_fecha_nac)
                        st.success(t('account_created'))
                        st.session_state['last_registered_user'] = new_username
                    else:
                        st.error(msj_codigo)

else:
    st.sidebar.title(f"{t('welcome')}, {st.session_state.get('nombre', '')}")
    
    if st.sidebar.button(t('reader_btn')):
        abrir_modal_manual()
        
    if st.sidebar.button(t('logout')):
        st.session_state['logged_in'] = False
        st.rerun()
        
    st.title(t('panel_title'))
    
    # --- CÁLCULO DE DATOS PARA EL PANEL ---
    todos_los_registros = obtener_registros_seguro(pestaña_registros)
    datos_usuario = [r for r in todos_los_registros if str(r.get('username', '')) == st.session_state.get('username', '')]
    
    edad_actual = calcular_edad(st.session_state.get('fecha_nacimiento', '1990-01-01'))
    lbm_actual = 0.0
    tmb_actual = 0.0
    
    if datos_usuario:
        df_temp = pd.DataFrame(datos_usuario)
        df_temp['fecha_dt'] = pd.to_datetime(df_temp['fecha'], errors='coerce')
        df_temp = df_temp.sort_values(by='fecha_dt')
        ultimo_reg = df_temp.iloc[-1]
        
        ultimo_peso = float(str(ultimo_reg.get('peso_kg', 0)).replace(',', '.'))
        ultimo_cuello = float(str(ultimo_reg.get('cuello_cm', 0)).replace(',', '.'))
        ultima_cintura = float(str(ultimo_reg.get('cintura_cm', 0)).replace(',', '.'))
        ultima_cadera = float(str(ultimo_reg.get('cadera_cm', 0)).replace(',', '.'))
        
        ultima_grasa = calcular_grasa_naval(st.session_state.get('sexo', 'H'), st.session_state.get('estatura', 170.0), ultimo_cuello, ultima_cintura, ultima_cadera)
        lbm_actual, tmb_actual = calcular_katch_mcardle(ultimo_peso, ultima_grasa)

    # --- RENDERIZADO DEL PANEL CLÍNICO ---
    st.subheader(t('data_history'))
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    with col_p1:
        st.metric(label=t('age'), value=f"{edad_actual} {t('years')}")
    with col_p2:
        val_estatura = from_cm(st.session_state.get('estatura', 0), sys)
        st.metric(label=t('height'), value=f"{val_estatura:.1f} {d_unit}")
    with col_p3:
        val_lbm = from_kg(lbm_actual, sys)
        st.metric(label=t('lean_mass'), value=f"{val_lbm:.1f} {w_unit}")
    with col_p4:
        st.metric(label=t('bmr'), value=f"{tmb_actual:.0f} kcal")
        
    st.markdown("---")
    
    # --- FORMULARIO DE INGRESO DIARIO ---
    st.subheader(t('daily_entry'))
    fecha_ingreso = st.date_input(t('record_date'), value=datetime.now().date())
    
    col1, col2 = st.columns(2)
    
    with col1:
        min_w, max_w, def_w = (30.0, 200.0, 70.0) if sys == 'Métrico (kg/cm)' else (66.0, 440.0, 154.0)
        peso_ui = st.number_input(f"{t('total_weight')} ({w_unit})", min_value=min_w, max_value=max_w, value=def_w, step=0.1)
        
        min_n, max_n, def_n = (20.0, 60.0, 38.0) if sys == 'Métrico (kg/cm)' else (8.0, 24.0, 15.0)
        cuello_ui = st.number_input(f"{t('neck')} ({d_unit})", min_value=min_n, max_value=max_n, value=def_n, step=0.1)
        
        min_c, max_c, def_c = (40.0, 150.0, 80.0) if sys == 'Métrico (kg/cm)' else (16.0, 60.0, 31.5)
        cintura_ui = st.number_input(f"{t('waist')} ({d_unit})", min_value=min_c, max_value=max_c, value=def_c, step=0.1)
        
    with col2:
        cadera_ui = 0.0
        if st.session_state.get('sexo', 'H') == 'M':
            min_hip, max_hip = (50.0, 150.0) if sys == 'Métrico (kg/cm)' else (20.0, 60.0)
            cadera_ui = st.number_input(f"{t('hip')} ({d_unit})", min_value=min_hip, max_value=max_hip, step=0.1)
        else:
            st.text_input(f"{t('hip')} ({d_unit})", value=t('not_required_m'), disabled=True)
            
        ingesta = st.number_input(t('total_intake'), min_value=0.0, step=10.0)
        activas = st.number_input(t('active_cals'), min_value=0.0, step=10.0)
        
    if st.button(t('calc_register_btn')):
        peso_kg = to_kg(peso_ui, sys)
        cuello_cm = to_cm(cuello_ui, sys)
        cintura_cm = to_cm(cintura_ui, sys)
        cadera_cm = to_cm(cadera_ui, sys)
        
        grasa = calcular_grasa_naval(st.session_state['sexo'], st.session_state['estatura'], cuello_cm, cintura_cm, cadera_cm)
        lbm, tmb = calcular_katch_mcardle(peso_kg, grasa)
        tdee = tmb + activas
        balance = ingesta - tdee
        
        fecha_registro = str(fecha_ingreso)
        username_actual = st.session_state['username']
        
        fila_a_actualizar = None
        for i, registro in enumerate(todos_los_registros):
            if str(registro.get('username', '')) == username_actual and str(registro.get('fecha', '')) == fecha_registro:
                fila_a_actualizar = i + 2
                break
                
        nueva_fila = [username_actual, fecha_registro, peso_kg, cuello_cm, cintura_cm, cadera_cm, ingesta, activas]
        
        if fila_a_actualizar:
            rango = f"A{fila_a_actualizar}:H{fila_a_actualizar}"
            pestaña_registros.update(rango, [nueva_fila])
        else:
            pestaña_registros.append_row(nueva_fila)
        
        st.markdown(t('daily_results'))
        met1, met2, met3 = st.columns(3)
        met1.metric(label=t('body_fat'), value=f"{grasa:.1f} %")
        val_lbm_disp = from_kg(lbm, sys)
        met2.metric(label=t('lean_mass'), value=f"{val_lbm_disp:.1f} {w_unit}")
        met3.metric(label="TMB", value=f"{tmb:.0f} kcal")
        
        met4, met5, met6 = st.columns(3)
        met4.metric(label=t('dyn_tdee'), value=f"{tdee:.0f} kcal")
        met5.metric(label=t('reg_intake'), value=f"{ingesta:.0f} kcal")
        met6.metric(label=t('daily_balance'), value=f"{balance:.0f} kcal", delta=f"{balance:.0f} kcal", delta_color="inverse")

    # --- HISTORIAL Y TENDENCIAS ---
    st.markdown("---")
    st.subheader(t('audit_history'))
    
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
        
        df_historial['Peso_disp'] = df_historial['Peso_kg'].apply(lambda x: from_kg(x, sys)).round(1)
        df_historial['Cuello_disp'] = df_historial['Cuello_cm'].apply(lambda x: from_cm(x, sys)).round(1)
        df_historial['Cintura_disp'] = df_historial['Cintura_cm'].apply(lambda x: from_cm(x, sys)).round(1)
        df_historial['Cadera_disp'] = df_historial['Cadera_cm'].apply(lambda x: from_cm(x, sys)).round(1)
        
        df_historial = df_historial.rename(columns={
            'Peso_disp': f'Peso ({w_unit})',
            'Cuello_disp': f'Cuello ({d_unit})',
            'Cintura_disp': f'Cintura ({d_unit})',
            'Cadera_disp': f'Cadera ({d_unit})'
        })
        
        columnas_visibles = ['Fecha', f'Peso ({w_unit})', '% Grasa', f'Cuello ({d_unit})', f'Cintura ({d_unit})', f'Cadera ({d_unit})', 'Ingesta', 'Gasto_Activo']
        columnas_existentes = [c for c in columnas_visibles if c in df_historial.columns]
        df_mostrar = df_historial[columnas_existentes]
        
        st.markdown(t('trends'))
        opciones_filtro = [t('7_days'), t('1_month'), t('1_year'), t('full_history')]
        filtro = st.radio(t('select_period'), opciones_filtro, horizontal=True)

        fecha_actual = pd.to_datetime(datetime.now().date())
        if filtro == t('7_days'):
            df_grafico = df_historial[df_historial['Fecha_dt'] >= (fecha_actual - pd.Timedelta(days=7))]
        elif filtro == t('1_month'):
            df_grafico = df_historial[df_historial['Fecha_dt'] >= (fecha_actual - pd.Timedelta(days=30))]
        elif filtro == t('1_year'):
            df_grafico = df_historial[df_historial['Fecha_dt'] >= (fecha_actual - pd.Timedelta(days=365))]
        else:
            df_grafico = df_historial

        col_graf1, col_graf2 = st.columns(2)
        with col_graf1:
            st.markdown(f"{t('weight_graph')} ({w_unit})")
            if f'Peso ({w_unit})' in df_grafico.columns and not df_grafico.empty:
                st.line_chart(df_grafico.set_index('Fecha')[f'Peso ({w_unit})'], color="#2563EB")
            else:
                st.info(t('no_data'))
                
        with col_graf2:
            st.markdown(t('fat_graph'))
            if '% Grasa' in df_grafico.columns and not df_grafico.empty:
                st.line_chart(df_grafico.set_index('Fecha')['% Grasa'], color="#10B981")
            else:
                st.info(t('no_data'))
                
        st.markdown(t('last_7_records'))
        df_ultimos_7 = df_mostrar.tail(7)
        st.dataframe(df_ultimos_7, use_container_width=True)
        
        csv_data = df_mostrar.to_csv(index=False).encode('utf-8')
        st.download_button(
            label=t('download_csv'),
            data=csv_data,
            file_name=f"Rebuilt_Historial_{st.session_state.get('username', 'usuario')}.csv",
            mime="text/css"
        )
        
    else:
        st.info(t('empty_matrix'))