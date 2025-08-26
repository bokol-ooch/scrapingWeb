# scrapingWeb
Empleamos selenium para realizar un scraping web en una pagina que emplea mucho javascipt

Este programa abre la pagina principal, introduce las credenciales, luego va a la pestaña de inscripciones y selecciona la primer categoria de carrera, toma una captura de pantalla y extrae la informacion de corredores inscritos, luego selecciona la segunda categoria de carrera toma una captura de pantalla y extrae la información de corredores inscritos a esta carrera, al finalizar esto cierra el navegador.

Lanza a pantalla la información sobre el numero de participantes a cada carrera, finalmente redacta un correo con esta información, adjunta las capturas de pantalla y lo envia.

![Correo](https://github.com/bokol-ooch/scrapingWeb/blob/main/Captura%20de%20pantalla%202025-07-30%20114516.png "Correo enviado de forma automatica")

![Inscritos](https://github.com/bokol-ooch/scrapingWeb/blob/main/inscritos.png "Captura de pantalla corredores inscritos")

![InscritosConDonativo](https://github.com/bokol-ooch/scrapingWeb/blob/main/inscritosDonativo.png "Captura de pantalla corredores inscritos con donativo")

Se ha realizado una modificacion donde ya no se toma captura de pantalla, se extrae la información del numero de corredores y la fecha de inscripcion para generar una tabla comparativa con el año pasado y con el dia anterior y se envia la tabla por correo.

![Tablas](https://github.com/bokol-ooch/scrapingWeb/blob/main/Captura%20de%20pantalla%202025-08-25%20182443.png "Captura de pantalla tabla resumen")

Para poder realizar la comparación se cargan archivos csv que resumen la información de años pasados.
