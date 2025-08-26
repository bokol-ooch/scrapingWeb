# Script: descargarListaCorredores.py
# Autor: Fernando Cisneros Chavez (verdevenus23@gmail.com)
# Fecha: 31 de julio de 2025
# Licencia: MIT

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import requests
import time
import csv
import pandas as pd
import ast
import json

# Login
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get("https://admon.marcate.network/admin/")
time.sleep(1)

driver.find_element(By.NAME, "usuario").send_keys("usuario")
driver.find_element(By.NAME, "pass").send_keys("psswd")
driver.find_element(By.NAME, "pass").submit()
time.sleep(3)

# Extraer cookies de Selenium para requests
selenium_cookies = driver.get_cookies()

# Crear sesión requests y agregar cookies
session = requests.Session()
for cookie in selenium_cookies:
    session.cookies.set(cookie['name'], cookie['value'])

# Añadir headers importantes para simular navegador
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36',
    'Referer': 'https://admon.marcate.network/admin/inscritos'
})

# Cambia este ID por el que necesites (según dropdown)
carrera_id = "SPTMCAR1749666649" # carrera 2025
#carrera_id = "SPTMCAR1749673645" # carrera 2025 DONATIVO
#carrera_id = "SPTMCAR1718045103" # carrera 2024
#carrera_id = "SPTMCAR1718125661" # carrera 2024 (con causa)

# Obtener totales
url_total = "https://admon.marcate.network/admin/inscritos/TotalInscritos"
respuesta_total = session.post(url_total, data={'carreraId': carrera_id})

print("Respuesta total status:", respuesta_total.status_code)
#print("Respuesta total text (debug):", respuesta_total.text[:100])  # Imprime primeros 100 caracteres

data_total = respuesta_total.json()

total = data_total.get('total', 0)
totalReinbursment = data_total.get('totalReinbursment', 0)
Cupo = total + totalReinbursment

print(f"Total inscritos: {total}, Reembolsos: {totalReinbursment}, Cupo: {Cupo}")

if Cupo == 0:
    print("No hay inscritos.")
else:
    LOTE = 20000
    loads = (Cupo // LOTE) + (1 if Cupo % LOTE != 0 else 0)

    inscritos = []

    for i in range(loads):
        offset = i * LOTE
        url_get = f"https://admon.marcate.network/admin/inscritos/get/{carrera_id}/{LOTE}/{offset}"
        resp = session.post(url_get)
        print(f"Lote {i+1}/{loads} - status: {resp.status_code}")
        # Verificar que la respuesta sea JSON válida y guardando en CSV
        try:
            lineas = resp.text.replace("},{","}};{{").split("};{")
#            print(lineas[:2])
            datos_dict = [json.loads(item) for item in lineas]
            df = pd.DataFrame(datos_dict)
            meses = {
                'enero': '01',
                'febrero': '02',
                'marzo': '03',
                'abril': '04',
                'mayo': '05',
                'junio': '06',
                'julio': '07',
                'agosto': '08',
                'septiembre': '09',
                'octubre': '10',
                'noviembre': '11',
                'diciembre': '12'
            }
            
            def convertir_fecha(fecha_str):
                try:
                    fecha_limpia = fecha_str.split(" a las")[0].strip()
        
        # Separar partes
                    partes = fecha_limpia.split(" ")
                    dia = partes[0].zfill(2)
                    mes = meses[partes[2].strip().lower()]
                    anio = partes[4].strip()                    
                    return f"{dia}/{mes}/{anio}"
                except Exception as e:
                    print(f"error {e}")
            # Aplicar la función a la columna
            df['fecha_formateada'] = df['fechaIns'].apply(convertir_fecha)

            df_agrupado = df['fecha_formateada'].value_counts().reset_index()
            df_agrupado.columns = ['fecha', 'inscritos_hoy']
            
            # Ordenar fechas
            df_agrupado['fecha_dt'] = pd.to_datetime(df_agrupado['fecha'], format='%d/%m/%Y')
            df_agrupado = df_agrupado.sort_values('fecha_dt', ascending=False).reset_index(drop=True)
            
            # Calcular acumulado de abajo hacia arriba
            df_agrupado['inscritos_acumulado'] = df_agrupado['inscritos_hoy'][::-1].cumsum()[::-1]
            
            # Dejar solo las columnas finales
            resultado = df_agrupado[['fecha', 'inscritos_hoy', 'inscritos_acumulado']]
            
            print(resultado)

            nombreCSV = f"{carrera_id}{str(LOTE)}{str(offset)}.csv"
            resultado.to_csv( nombreCSV, index=False, encoding="utf-8")
            print("CSV generado correctamente.")
        except Exception as e:
            print(resp.headers.get('Content-Type'))
            print("Error parseando txt:", e)

# Cerrar Selenium
driver.quit()
