# 1. CONFIGURACIÓN INICIAL

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import os

# Se utiliza la librería 'warnings' para ignorar alertas secundarias 
warnings.filterwarnings('ignore') 

# 2. DEFINICIÓN DE RUTAS

# ! IMPORTANTE: Ajustar esta ruta al CSV.
UBICACION_ARCHIVO_CSV = r'C:\Users\Dani\Documents\Lucho\Data Ciencia\Seminario en CS\TP4\winemag-data-130k-v2.csv'

CARPETA_GRAFICOS = r'C:\Users\Dani\Documents\Lucho\Data Ciencia\Seminario en CS\TP4\GRAFICOS_TP4' 

# Control de flujo para crear la carpeta de gráficos si no existe
if not os.path.exists(CARPETA_GRAFICOS):
    os.makedirs(CARPETA_GRAFICOS)
    print(f" Carpeta de gráficos creada en: ./{CARPETA_GRAFICOS}")
else:
    print(f" Carpeta de gráficos encontrada: ./{CARPETA_GRAFICOS}")

# 3. CARGA Y PREPARACIÓN DE DATOS (TP2)

print("\n\n 3. CARGA Y PREPARACIÓN DE DATOS (TP2)")

df = None # Se inicializa df como None para manejo de errores

try:
    # 3.1. Carga del archivo
    
    print(f"\n[Paso 3.1] Cargando archivo: {UBICACION_ARCHIVO_CSV}...")
    # Se utiliza la codificación y delimitador descubiertos en el TP2
    df = pd.read_csv(UBICACION_ARCHIVO_CSV, delimiter=';', encoding='latin-1') 
    
    print(f" Archivo CSV cargado.")
    print(f" Dimensiones iniciales: {df.shape[0]} filas, {df.shape[1]} columnas")

    # 3.2. Limpieza y Transformación (basado en hallazgos del TP2)
    print("\n[Paso 3.2] Iniciando limpieza y transformación (TP2)...")
    
    # Eliminar columna 'ID', esta columna es un índice redundante.
    if 'ID' in df.columns:
        df = df.drop('ID', axis=1)
        print("\n Columna 'ID' eliminada.")
         
    # Convertir 'price' a numérico, resuelve el DtypeWarning identificado en el TP2
    if 'price' in df.columns:
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        print(" Columna 'price' convertida a numérico (float64).")

    # Eliminar duplicados exactos (identificados en TP2)
    duplicados_iniciales = df.duplicated().sum()
    if duplicados_iniciales > 0:
        df = df.drop_duplicates(keep='first')
        print(f" Se eliminaron {duplicados_iniciales} filas duplicadas exactas.")
    
    # 3.3. Imputación de Datos Faltantes (Nulos)
    print("\n[Paso 3.3] Iniciando imputación de datos faltantes (TP2)...")
    
    # ESTRATEGIA VARIABLES CATEGÓRICAS (TP2): Etiqueta 'N/A - Desconocido'
    # Se aplica esta estrategia para no perder filas con datos valiosos en otras columnas (TP2)
    col_categoricas = df.select_dtypes(include=['object']).columns
    df[col_categoricas] = df[col_categoricas].fillna('N/A - Desconocido')
    print(" Valores nulos categóricos reemplazados con 'N/A - Desconocido'.")

    # ESTRATEGIA VARIABLES NUMÉRICAS (TP2): Imputación con Mediana
    # Se usa Mediana, ya que el análisis del TP2 demostró que 'price' es asimétrico y la media no es representativa.
    mediana_price = df['price'].median()
    mediana_points = df['points'].median()
    
    df['price'].fillna(mediana_price, inplace=True)
    df['points'].fillna(mediana_points, inplace=True)
    print(f" Nulos de 'price' reemplazados con mediana ({mediana_price}).")
    print(f" Nulos de 'points' reemplazados con mediana ({mediana_points}).")

    print("\n[PREPARACIÓN FINALIZADA]")
    print(f" Dimensiones finales (df): {df.shape[0]} filas, {df.shape[1]} columnas")
    print(f" Total de valores nulos restantes: {df.isnull().sum().sum()}")


except FileNotFoundError:
    print(f"ERROR")
    print(f"ERROR: Archivo no encontrado en la ruta: {UBICACION_ARCHIVO_CSV}. Verifique ubicacion de archivo")
    df = None

# 4. FILTRADO DE OUTLIERS (Identificado en TP2)
print("\n\n 4. FILTRADO DE OUTLIERS (PARA VISUALIZACIÓN)")
# Basado en el análisis del TP2, el 6.89% de los precios son outliers (superiores a $73.00).  
# Son valores legítimos (vinos de lujo) pero distorsionan los gráficos.
# Para crear visualizaciones claras se crea un segundo DataFrame filtrado para los análisis de correlación y distribución.

df_filtrado = None

if df is not None:
    try:
        # Límite superior definido por el Rango Intercuartílico en el TP2
        LIMITE_SUPERIOR_PRECIO = 73.00 
        
        # Crear el DataFrame filtrado
        df_filtrado = df[df['price'] <= LIMITE_SUPERIOR_PRECIO].copy()
        
        print(f"\n Se ha creado 'df_filtrado' (sin outliers > ${LIMITE_SUPERIOR_PRECIO}).")
        print(f"            - df (completo): {df.shape[0]} filas")
        print(f"            - df_filtrado (para gráficos): {df_filtrado.shape[0]} filas")
        
    except Exception as e:
        print(f"Ocurrió un error al filtrar outliers: {e}")
else:
    print("\n ADVERTENCIA: El DataFrame 'df' no se cargó.")


# 5. ANÁLISIS Y VISUALIZACIÓN (TP4)
print("\n\n 5. ANÁLISIS Y VISUALIZACIÓN (TP4)")

# Verificación final antes de graficar
if (df is not None) and (df_filtrado is not None):
    
    # 5.1 PREGUNTA 1: ¿Correlación Precio vs. Puntuación?
    print("\n[Paso 5.1] Iniciando Gráfico 1 (Correlación Precio vs. Puntos)...")
    
    plt.figure(figsize=(12, 7))
    # Usamos seaborn para un gráfico de dispersión, se usa 'alpha=0.3' para ver la densidad de puntos donde se superponen
    scatterplot = sns.scatterplot(
        data=df_filtrado, 
        x='points', 
        y='price', 
        alpha=0.3, # Transparencia para ver densidad
        s=15       # Tamaño de puntos
    )
    
    # Añadir una línea de regresión (tendencia)
    sns.regplot(
        data=df_filtrado, 
        x='points', 
        y='price', 
        scatter=False, # No dibujar los puntos de nuevo
        color='red',
        line_kws={'linestyle':'--'},
        ax=scatterplot # Dibuja en el mismo gráfico
    )
    
    plt.title('Pregunta 1: Correlación entre Puntuación y Precio (Vinos hasta $73)', fontsize=16)
    plt.xlabel('Puntuación (Points)', fontsize=12)
    plt.ylabel('Precio (USD)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    
    ruta_g1 = os.path.join(CARPETA_GRAFICOS, 'G1_Correlacion_Precio_Puntos.png')
    try:
        plt.savefig(ruta_g1)
        print(f"ÉXITO: Gráfico 1 (Scatterplot) guardado en: {ruta_g1}")
    except Exception as e:
        print(f"Error al guardar Gráfico 1: {e}")
    plt.close() # Cerrar la figura para liberar memoria

    # 5.2 PREGUNTA 2: Distribución del Malbec Argentino
    print("\n[Paso 5.2] Iniciando Gráficos 2 y 3 (Distribución Malbec Argentino)...")
    
    # Aplicar filtros (replicando SQL del TP3)
    # Usamos .str.contains('Malbec') para incluir blends, como en el TP3
    df_malbec_arg = df[
        (df['country'] == 'Argentina') & 
        (df['variety'].str.contains('Malbec', case=False))
    ].copy()

    # Usamos el filtrado (sin outliers) para el gráfico de PRECIO
    df_malbec_arg_filtrado = df_filtrado[
        (df_filtrado['country'] == 'Argentina') & 
        (df_filtrado['variety'].str.contains('Malbec', case=False))
    ].copy()

    print(f"            - Se filtraron {df_malbec_arg.shape[0]} reseñas de Malbec Argentino.")

    # Gráfico 2: Histograma de Puntuaciones
    plt.figure(figsize=(12, 7))
    sns.histplot(df_malbec_arg['points'], bins=15, kde=True, color='purple')
    plt.title('Pregunta 2.A: Distribución de Puntuaciones (Malbec Argentino)', fontsize=16)
    plt.xlabel('Puntuación (Points)', fontsize=12)
    plt.ylabel('Cantidad de Reseñas', fontsize=12)
    # Se añade la mediana como referencia central
    plt.axvline(df_malbec_arg['points'].median(), color='red', linestyle='--', label=f"Mediana: {df_malbec_arg['points'].median():.1f}")
    plt.legend()
    
    ruta_g2 = os.path.join(CARPETA_GRAFICOS, 'G2_Histograma_Puntos_Malbec.png')
    try:
        plt.savefig(ruta_g2)
        print(f"ÉXITO: Gráfico 2 (Histograma Malbec) guardado en: {ruta_g2}")
    except Exception as e:
        print(f"Error al guardar Gráfico 2: {e}")
    plt.close()

    # Gráfico 3: Boxplot de Precios
    plt.figure(figsize=(12, 7))
    sns.boxplot(data=df_malbec_arg_filtrado, y='price', color='lightblue')
    # Se añaden puntos con 'jitter' para ver la densidad de datos
    sns.stripplot(data=df_malbec_arg_filtrado, y='price', color='black', alpha=0.1, jitter=True)
    plt.title('Pregunta 2.B: Distribución de Precios (Malbec Argentino, hasta $73)', fontsize=16)
    plt.ylabel('Precio (USD)', fontsize=12)
    
    ruta_g3 = os.path.join(CARPETA_GRAFICOS, 'G3_Boxplot_Precio_Malbec.png')
    try:
        plt.savefig(ruta_g3)
        print(f"ÉXITO: Gráfico 3 (Boxplot Malbec) guardado en: {ruta_g3}")
    except Exception as e:
        print(f"Error al guardar Gráfico 3: {e}")
    plt.close()

    # 5.3 PREGUNTA 3: Relación Calidad-Precio por País
    print("\n[Paso 5.3] Iniciando Gráfico 4 (Ratio Calidad-Precio por País)...")
    
    # 1. Identificar Top 10 países por volumen (usamos df completo)
    top_10_countries = df['country'].value_counts().head(10).index
    
    # 2. Filtrar el df completo solo a esos países
    df_top10 = df[df['country'].isin(top_10_countries)].copy()
    
    # 3. Calcular la métrica derivada (del TP1)
    # Se filtran precios > 0 para evitar división por cero
    df_top10 = df_top10[df_top10['price'] > 0]
    df_top10['ratio_calidad_precio'] = df_top10['points'] / df_top10['price']
    
    # 4. Agrupar y calcular la media del ratio
    avg_rcp_countries = df_top10.groupby('country')['ratio_calidad_precio'].mean().sort_values(ascending=False)
    
    # 5. Graficar (Barplot)
    plt.figure(figsize=(12, 7))
    barplot_rcp = sns.barplot(
        x=avg_rcp_countries.index, 
        y=avg_rcp_countries.values, 
        palette='viridis'
    )
    plt.title('Pregunta 3: Relación Calidad-Precio Promedio (Top 10 Países por Volumen)', fontsize=16)
    plt.xlabel('País', fontsize=12)
    plt.ylabel('Ratio Promedio (Puntos por Dólar)', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    
    # Añadir etiquetas de valor sobre las barras
    for p in barplot_rcp.patches:
        barplot_rcp.annotate(format(p.get_height(), '.2f'), 
                           (p.get_x() + p.get_width() / 2., p.get_height()), 
                           ha = 'center', va = 'center', 
                           xytext = (0, 9), 
                           textcoords = 'offset points')
    
    ruta_g4 = os.path.join(CARPETA_GRAFICOS, 'G4_Ratio_Calidad_Precio_Pais.png')
    try:
        plt.savefig(ruta_g4)
        print(f"ÉXITO: Gráfico 4 (Barplot Ratio P/P) guardado en: {ruta_g4}")
    except Exception as e:
        print(f"Error al guardar Gráfico 4: {e}")
    plt.close()

# 5.4 PREGUNTA 4: Influencia de Catadores y Rango de Precios
    print("\n[Paso 5.4] Iniciando Gráfico 5 (Análisis de Catadores)...")

    # 1. Filtrar el df completo para excluir los 'N/A - Desconocido', esto es para analizar la influencia de catadores reales.
    df_catadores_reales = df[df['taster_name'] != 'N/A - Desconocido']
    
    # 2. Identificar Top 5 catadores por volumen
    top_5_tasters_list = df_catadores_reales['taster_name'].value_counts().head(5).index.tolist()

    # 3. Filtrar el df_filtrado (sin outliers de precio) para el boxplot de precios
    df_top5_tasters_filtered = df_filtrado[df_filtrado['taster_name'].isin(top_5_tasters_list)]

    # 4. Graficar (Boxplot ordenado por influencia)
    plt.figure(figsize=(14, 8))
    sns.boxplot(
        data=df_top5_tasters_filtered,
        x='taster_name',
        y='price',
        order=top_5_tasters_list, # Ordenar los boxplots por el conteo (influencia)
        palette='Spectral'
    )
    plt.title('Pregunta 4: Rango de Precios Reseñados por los 5 Catadores Más Influyentes (Vinos hasta $73)', fontsize=16)
    plt.xlabel('Catador (Ordenado por n° de reseñas: de izq. a der.)', fontsize=12)
    plt.ylabel('Precio (USD) de los vinos que reseñan', fontsize=12)
    plt.xticks(rotation=15, ha='right')

    ruta_g5 = os.path.join(CARPETA_GRAFICOS, 'G5_Boxplot_Precio_Catadores.png')
    try:
        plt.savefig(ruta_g5)
        print(f"ÉXITO: Gráfico 5 (Boxplot Catadores) guardado en: {ruta_g5}")
    except Exception as e:
        print(f"Error al guardar Gráfico 5: {e}")
    plt.close()

else:
    print("\n ERROR CRÍTICO: Los DataFrames no están listos. No se pueden generar gráficos.")

print(f"\n\n Todos los gráficos han sido guardados en la carpeta: {CARPETA_GRAFICOS}")