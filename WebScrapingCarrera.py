from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import os

# Iniciar navegador
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# Ir al login
driver.get("https://admon.marcate.network/admin/")
time.sleep(1)

# Ingresar credenciales
driver.find_element(By.NAME, "usuario").send_keys("HYDROLIT2024")
driver.find_element(By.NAME, "pass").send_keys("HYDROLIT2024" + Keys.RETURN)
time.sleep(1)

# Ir a la página de inscritos
driver.get("https://admon.marcate.network/admin/inscritos")
time.sleep(1)

dropdown = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, ".select2-choice"))
)
dropdown.click()

# Esperar que aparezca la lista de opciones 
options = WebDriverWait(driver, 10).until(
    EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".select2-results li.select2-result"))
)

# Seleccionar la primera opcion
if options:
    options[1].click()
else:
    print("No se encontraron opciones")

msg_element = WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located((By.ID, "msgInscripcionesTotal"))
)

# Obtener el numero de corredores sin donativo inscritos
msg_text = msg_element.text

# Imprimir en consola
print("Inscripciones:", msg_text)
driver.save_screenshot("inscritos.png")

time.sleep(10)


dropdown = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, ".select2-choice"))
)
dropdown.click()

# Esperar que aparezca la lista de opciones, otra vez
options2 = WebDriverWait(driver, 10).until(
    EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".select2-results li.select2-result"))
)

# Seleccionar la segunda opcion
if options2:
    options2[2].click()
else:
    print("No se encontraron opciones")
time.sleep(10)
msg_element2 = WebDriverWait(driver, 5).until(
    EC.visibility_of_element_located((By.ID, "msgInscripcionesTotal"))
)

# Obtener el numero de corredores con donativo inscritos
msg_text2 = msg_element2.text
driver.save_screenshot("inscritosDonativo.png")
# Imprimir en consola
print("Inscripciones con Donativo:", msg_text2)
# Cierra el navegador al final
driver.quit()

hoy = datetime.now()
texto_fecha_hora = hoy.strftime("%Y-%m-%d %H:%M:%S")
# Configuración del correo
sender_email = "fernando.cisneros@farmaciazamora.com.mx"
receiver_email = "fernando.cisneros@farmaciazamora.com.mx"
password = "&6petniE"
subject = "Corredores inscritos a la carrera al "+texto_fecha_hora
body = "Corredores inscritos: \n"+msg_text+"\n "+msg_text2

# Crear el mensaje
message = MIMEMultipart()
message.attach(MIMEText(body,'plain'))
with open(r"inscritos.png", 'rb') as f:
    img = MIMEImage(f.read())
    img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(r"inscritos.png"))
    message.attach(img)
with open(r"inscritosDonativo.png", 'rb') as f:
    img2 = MIMEImage(f.read())
    img2.add_header('Content-Disposition', 'attachment', filename=os.path.basename(r"inscritosDonativo.png"))
    message.attach(img2)
message["Subject"] = subject
message["From"] = sender_email
message["To"] = receiver_email

# Conectarse al servidor SMTP de Zoho)
try:
    with smtplib.SMTP_SSL('smtp.zoho.com', 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
    print("Correo electrónico enviado con éxito.")
except Exception as e:
    print(f"Error al enviar el correo: {e}")
    
exit()