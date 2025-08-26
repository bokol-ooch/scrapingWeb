# Script: WebScrapingCarreraOptimizado.py
# Autor: Fernando Cisneros Chavez
# Fecha: 23 de agosto de 2025
# Licencia: MIT

import os
import re
import time
import json
import smtplib
import requests
import pandas as pd
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from cryptography.fernet import Fernet

def convertir_fecha(fecha_str):
    meses = {
        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
        'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
        'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
    }
    try:
        fecha_limpia = fecha_str.split(" a las")[0].strip()
        partes = fecha_limpia.split(" ")
        dia = partes[0].zfill(2)
        mes = meses[partes[2].strip().lower()]
        anio = partes[4].strip()
        return f"{dia}/{mes}/{anio}"
    except Exception:
        return None

def formatear_tabla_html(tabla):
    html = "<table border='1' style='border-collapse: collapse;'>"
    for i, fila in enumerate(tabla):
        html += "<tr>"
        for celda in fila:
            tag = "th" if i == 0 else "td"
            html += f"<{tag} style='padding: 10px;'>{celda}</{tag}>"
        html += "</tr>"
    html += "</table>"
    return html
	
# Carga de archivos CSV
df_2024 = pd.read_csv("inscritos2024.csv")
dfD_2024 = pd.read_csv("inscritosDonativo2024.csv")

# Conversión de fechas
df_2024.iloc[:, 0] = pd.to_datetime(df_2024.iloc[:, 0], dayfirst=True, errors='coerce')
dfD_2024.iloc[:, 0] = pd.to_datetime(dfD_2024.iloc[:, 0], dayfirst=True, errors='coerce')
df_2024.dropna(subset=[df_2024.columns[0]], inplace=True)
dfD_2024.dropna(subset=[dfD_2024.columns[0]], inplace=True)

# Fechas base
hoy = pd.to_datetime(datetime.today().date())
ayer = hoy - timedelta(days=1)
antier = ayer - timedelta(days=1)
hace_un_ano = hoy - pd.DateOffset(years=1)

# Buscar fechas más cercanas disponibles en los archivos CSV
def buscar_fecha_valida(base_fecha, fechas_disponibles):
    while base_fecha not in fechas_disponibles:
        base_fecha -= timedelta(days=1)
    return base_fecha

fechas_disponibles_2024 = set(df_2024.iloc[:, 0])
fechas_disponiblesD_2024 = set(dfD_2024.iloc[:, 0])

fecha_hoy_2024 = buscar_fecha_valida(hace_un_ano, fechas_disponibles_2024)
fecha_ayer_2024 = buscar_fecha_valida(fecha_hoy_2024 - timedelta(days=1), fechas_disponibles_2024)
fecha_antier_2024 = buscar_fecha_valida(fecha_hoy_2024 - timedelta(days=2), fechas_disponibles_2024)

fecha_hoyD_2024 = buscar_fecha_valida(hace_un_ano, fechas_disponiblesD_2024)
fecha_ayerD_2024 = buscar_fecha_valida(hace_un_ano - timedelta(days=1), fechas_disponiblesD_2024)
fecha_antierD_2024 = buscar_fecha_valida(hace_un_ano - timedelta(days=2), fechas_disponiblesD_2024)

# Extraer valores
fila_hoy = df_2024[df_2024.iloc[:, 0] == fecha_hoy_2024]
fila_ayer = df_2024[df_2024.iloc[:, 0] == fecha_ayer_2024]
fila_antier = df_2024[df_2024.iloc[:, 0] == fecha_antier_2024]

fila_hoyD = dfD_2024[dfD_2024.iloc[:, 0] == fecha_hoyD_2024]
fila_ayerD = dfD_2024[dfD_2024.iloc[:, 0] == fecha_ayerD_2024]
fila_antierD = dfD_2024[dfD_2024.iloc[:, 0] == fecha_antierD_2024]

inscritos_hoy_2024 = int(fila_hoy.iloc[0, 2])
inscritos_ayer_2024 = int(fila_ayer.iloc[0, 2])
inscritos_antier_2024 = int(fila_antier.iloc[0, 2])

inscritosD_hoy_2024 = int(fila_hoyD.iloc[0, 2])
inscritosD_ayer_2024 = int(fila_ayerD.iloc[0, 2])
inscritosD_antier_2024 = int(fila_antierD.iloc[0, 2])

# Iniciar navegador Chrome
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get("https://admon.marcate.network/admin/")
time.sleep(1)

# Login
driver.find_element(By.NAME, "usuario").send_keys("usuario")
driver.find_element(By.NAME, "pass").send_keys("psswd" + Keys.RETURN)
time.sleep(1)

# Crear sesión desde cookies de Selenium
selenium_cookies = driver.get_cookies()
session = requests.Session()

for cookie in selenium_cookies:
    session.cookies.set(cookie['name'], cookie['value'])

session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36',
    'Referer': 'https://admon.marcate.network/admin/inscritos'
})

# Función para obtener todos los inscritos por carrera desde la API
def obtener_inscritos_api(carrera_id):
    url_total = "https://admon.marcate.network/admin/inscritos/TotalInscritos"
    respuesta_total = session.post(url_total, data={'carreraId': carrera_id})
    data_total = respuesta_total.json()
    
    total = data_total.get('total', 0)
    total_reembolsos = data_total.get('totalReinbursment', 0)
    cupo_total = total + total_reembolsos

    if cupo_total == 0:
        return pd.DataFrame()

    lote = 20000
    cargas = (cupo_total // lote) + (1 if cupo_total % lote != 0 else 0)
    data_inscritos = []

    for i in range(cargas):
        offset = i * lote
        url_get = f"https://admon.marcate.network/admin/inscritos/get/{carrera_id}/{lote}/{offset}"
        resp = session.post(url_get)
        print(f"Lote {i+1}/{cargas} - Status: {resp.status_code}")

        try:
            lineas = resp.text.replace("},{", "}};{{").split("};{")
            registros = [json.loads(item) for item in lineas]
            data_inscritos.extend(registros)
        except Exception as e:
            print("Error al procesar lote:", e)

    return pd.DataFrame(data_inscritos)

# Procesar fechas del DataFrame de inscritos
def agrupar_por_fecha(df):
    meses = {
        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
        'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
        'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
    }

    def convertir_fecha(fecha_str):
        try:
            fecha_limpia = fecha_str.split(" a las")[0].strip()
            partes = fecha_limpia.split(" ")
            dia = partes[0].zfill(2)
            mes = meses[partes[2].lower()]
            anio = partes[4]
            return f"{dia}/{mes}/{anio}"
        except Exception:
            return None

    df['fecha_formateada'] = df['fechaIns'].apply(convertir_fecha)
    df = df.dropna(subset=['fecha_formateada'])

    df_agrupado = df['fecha_formateada'].value_counts().reset_index()
    df_agrupado.columns = ['fecha', 'inscritos_hoy']
    df_agrupado['fecha_dt'] = pd.to_datetime(df_agrupado['fecha'], format='%d/%m/%Y')
    df_agrupado = df_agrupado.sort_values('fecha_dt', ascending=False).reset_index(drop=True)
    df_agrupado['inscritos_acumulado'] = df_agrupado['inscritos_hoy'][::-1].cumsum()[::-1]

    return df_agrupado[['fecha', 'inscritos_hoy', 'inscritos_acumulado']]
	
# Carreras: normal y con donativo
carrera_normal_id = "SPTM45fCAR17456456456456456456456"
carrera_donativo_id = "SPTMCdfg4AR175645456456456456456"

df_inscritos_normal = obtener_inscritos_api(carrera_normal_id)
df_inscritos_donativo = obtener_inscritos_api(carrera_donativo_id)

inscritos_2025  = df_inscritos_normal.shape[0]
inscritosD_2025 = df_inscritos_donativo.shape[0]

resultado_normal = agrupar_por_fecha(df_inscritos_normal)
resultado_donativo = agrupar_por_fecha(df_inscritos_donativo)

# Cierre del navegador Selenium
driver.quit()

# Utilidad para encontrar la fecha más cercana anterior en los datos disponibles
def encontrar_fecha_valida(fechas_disponibles, fecha_inicial):
    while fecha_inicial.strftime('%d/%m/%Y') not in fechas_disponibles:
        fecha_inicial -= timedelta(days=1)
    return fecha_inicial.strftime('%d/%m/%Y')

# Convertimos sets para búsqueda
fechas_normal = set(resultado_normal['fecha'])
fechas_donativo = set(resultado_donativo['fecha'])

# Fechas de comparación (ayer, antier, anteayer)
fecha_ayer = encontrar_fecha_valida(fechas_normal, hoy - timedelta(days=1))
fecha_antier = encontrar_fecha_valida(fechas_normal, hoy - timedelta(days=2))
fecha_anteayer = encontrar_fecha_valida(fechas_normal, hoy - timedelta(days=3))

fecha_ayerD = encontrar_fecha_valida(fechas_donativo, hoy - timedelta(days=1))
fecha_antierD = encontrar_fecha_valida(fechas_donativo, hoy - timedelta(days=2))
fecha_anteayerD = encontrar_fecha_valida(fechas_donativo, hoy - timedelta(days=3))

def valor_en_fecha(df, fecha_str):
    fila = df[df['fecha'] == fecha_str]
    if not fila.empty:
        return int(fila.iloc[0]['inscritos_acumulado'])
    return 0

# Valores normales (2025)
inscritos_ayer = valor_en_fecha(resultado_normal, fecha_ayer)
inscritos_antier = valor_en_fecha(resultado_normal, fecha_antier)
inscritos_anteayer = valor_en_fecha(resultado_normal, fecha_anteayer)

# Donativos (2025)
inscritosD_ayer = valor_en_fecha(resultado_donativo, fecha_ayerD)
inscritosD_antier = valor_en_fecha(resultado_donativo, fecha_antierD)
inscritosD_anteayer = valor_en_fecha(resultado_donativo, fecha_anteayerD)

# Tabla para inscritos normales
tabla = [
    ["Fecha", "Inscritos<br>2024", "Inscritos<br>2025", "Diferencia", "Diferencia (%)", "Nuevos inscritos"],
    [antier.strftime('%d/%m/%Y'), inscritos_antier_2024, inscritos_antier,
     inscritos_antier - inscritos_antier_2024,
     f"{round(((inscritos_antier - inscritos_antier_2024) / inscritos_antier_2024) * 100, 2)}%",
     inscritos_antier - inscritos_anteayer],
    [ayer.strftime('%d/%m/%Y'), inscritos_ayer_2024, inscritos_ayer,
     inscritos_ayer - inscritos_ayer_2024,
     f"{round(((inscritos_ayer - inscritos_ayer_2024) / inscritos_ayer_2024) * 100, 2)}%",
     inscritos_ayer - inscritos_antier],
    [hoy.strftime('%d/%m/%Y'), inscritos_hoy_2024, inscritos_2025,
     inscritos_2025 - inscritos_hoy_2024,
     f"{round(((inscritos_2025 - inscritos_hoy_2024) / inscritos_hoy_2024) * 100, 2)}%",
     inscritos_2025 - inscritos_ayer]
]

# Tabla para inscritos con donativo
tablaD = [
    ["Fecha", "Inscritos<br>2024", "Inscritos<br>2025", "Diferencia", "Diferencia (%)", "Nuevos inscritos"],
    [antier.strftime('%d/%m/%Y'), inscritosD_antier_2024, inscritosD_antier,
     inscritosD_antier - inscritosD_antier_2024,
     f"{round(((inscritosD_antier - inscritosD_antier_2024) / inscritosD_antier_2024) * 100, 2)}%",
     inscritosD_antier - inscritosD_anteayer],
    [ayer.strftime('%d/%m/%Y'), inscritosD_ayer_2024, inscritosD_ayer,
     inscritosD_ayer - inscritosD_ayer_2024,
     f"{round(((inscritosD_ayer - inscritosD_ayer_2024) / inscritosD_ayer_2024) * 100, 2)}%",
     inscritosD_ayer - inscritosD_antier],
    [hoy.strftime('%d/%m/%Y'), inscritosD_hoy_2024, inscritosD_2025,
     inscritosD_2025 - inscritosD_hoy_2024,
     f"{round(((inscritosD_2025 - inscritosD_hoy_2024) / inscritosD_hoy_2024) * 100, 2)}%",
     inscritosD_2025 - inscritosD_ayer]
]

def tabla_a_html(tabla):
    html = "<table border='1' style='border-collapse: collapse;'>"
    for i, fila in enumerate(tabla):
        html += "<tr>"
        for celda in fila:
            tag = 'th' if i == 0 else 'td'
            html += f"<{tag} style='padding: 10px;'>{celda}</{tag}>"
        html += "</tr>"
    html += "</table>"
    return html

tabla_html = tabla_a_html(tabla)
tablaD_html = tabla_a_html(tablaD)

cuerpo_html = f"""
<html>
    <body>
        <p>Hola,</p>
        <p>A continuación te envío el reporte de corredores inscritos:</p>
        <p><b>Inscritos sin donativo:</b></p>
        {tabla_html}
        <p><b>Inscritos con donativo:</b></p>
        {tablaD_html}
        <p>Saludos.</p>
    </body>
</html>
"""

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

# Datos del correo
key = b'aaaaaaaaaaaaaaaaaaaaaaaAaaaaaAAAAaaaaAAAaaaaAAAaa='
cipher = Fernet(key)
PSSWDtoken  = b'gAAAAABoqhEqpP0NsWcdUq935pu0bW7f6y1ylpV6RzaYlpdTGeVjXkEt_QfSSdFq6vFzj_e_J6X9exJfx6vMVbf8qE4Wd2e5kw=='
sender_email = "sender@correo.com.mx"
password = cipher.decrypt(PSSWDtoken).decode('utf-8')
receiver_email = ["receiver@correo.com.mx"]
bcc_email = [] # con copia para

# Fecha para asunto
fecha_str = hoy.strftime('%d/%m/%Y')
subject = f"Corredores inscritos a la carrera al {fecha_str}"

# Crear el correo
message = MIMEMultipart()
message["Subject"] = subject
message["From"] = sender_email
message["To"] = ', '.join(receiver_email)
message["Bcc"] = ', '.join(bcc_email)

# Agregar el cuerpo HTML al correo
message.attach(MIMEText(cuerpo_html, 'html'))

# Combinar destinatarios
destinatarios = receiver_email + bcc_email

try:
    with smtplib.SMTP_SSL('smtp.zoho.com', 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, destinatarios, message.as_string())
    print("Correo enviado con éxito.")
except Exception as e:
    print(f"Error al enviar el correo: {e}")

exit()
