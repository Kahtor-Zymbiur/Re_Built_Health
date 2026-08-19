# --- HISTORIAL Y TENDENCIAS ---
    st.markdown("---")
    st.subheader("Auditoría Histórica")
    
    # Extraer registros directamente desde la pestaña de Google Sheets
    todos_los_registros = pestaña_registros.get_all_records()
    
    # Filtrar solo los registros que corresponden al usuario en sesión
    datos_usuario = [r for r in todos_los_registros if str(r.get('username', '')) == st.session_state.get('username', '')]
    
    df_historial = pd.DataFrame(datos_usuario)
    
    if not df_historial.empty:
        # Renombrar columnas extraídas de Sheets para mantener compatibilidad con la UI
        df_historial = df_historial.rename(columns={
            'fecha': 'Fecha',
            'peso': 'Peso_kg',
            'cuello': 'Cuello_cm',
            'cintura': 'Cintura_cm',
            'cadera': 'Cadera_cm',
            'ingesta': 'Ingesta',
            'activas': 'Gasto_Activo'
        })
        
        # Forzar formato numérico (Sheets puede retornar celdas vacías como strings "")
        cols_numericas = ['Peso_kg', 'Cuello_cm', 'Cintura_cm', 'Cadera_cm', 'Ingesta', 'Gasto_Activo']
        for col in cols_numericas:
            if col in df_historial.columns:
                df_historial[col] = pd.to_numeric(df_historial[col], errors='coerce').fillna(0)
        
        # Ordenar cronológicamente para evitar errores en las líneas de tendencia
        df_historial['Fecha_dt'] = pd.to_datetime(df_historial['Fecha'], errors='coerce')
        df_historial = df_historial.sort_values(by='Fecha_dt')
        
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
        
        # Intersección defensiva por si alguna columna falla desde Sheets
        columnas_existentes = [c for c in columnas_visibles if c in df_historial.columns]
        df_mostrar = df_historial[columnas_existentes]
        
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