<table>
<tr>
<td><h1>Proyecto fwi.com.ar</h1></td>
<td align="right"><img src="images/fire.png" alt="Logo" width="100"></td>
</tr>
</table>


## 👀 ¿Qué es y para qué sirve? 
Este proyecto tiene como objetivo procesar datos meteorológicos proporcionados por el [Servicio Meteorológico Nacional](https://www.smn.gob.ar/) , para calcular índices relacionados con el Fire Weather Index `(FWI)`. Estos índices son esenciales para evaluar las condiciones de `riesgo de incendios forestales`, facilitando la toma de decisiones en `prevención` y `respuesta a emergencias`.

## ¿Para quién es? 
En este proyecto se busca crear una `herramienta gratuita` para profesionales como `bomberos` o `brigadas`, `estudiantes`, `aficionados` por la meteorología, y personas en general.

## 💡 Beneficios clave para el usuario 
* `Información`: La pagina brinda de manera intuitiva datos como: FWI, Temperatura, Humedad, Precipitaciones, Viento.    
* `Eficiencia`: Automatiza tareas repetitivas y permite enfocarse en el análisis de resultados.
* `Precisión`: Utiliza fórmulas estándar para garantizar la calidad de los índices calculados.
* `Confiabilidad`: Los datos se guardan de manera incremental. Asegurando el registro historico en el los calculos de cada día
* `Estadísticas`: Los datos historicos están disponibles para ser consultados

## 🔥 Indice FWI 
El `Fire Weather Index` (FWI) es un sistema internacionalmente reconocido para evaluar el riesgo de incendios forestales, basado en condiciones meteorológicas. Este índice combina factores claves como la temperatura, la humedad, el viento y las precipitaciones recientes, junto con una serie de cálculos que simulan el comportamiento del fuego en distintas condiciones.

El FWI no solo mide el riesgo de que ocurra un incendio, sino también su `intensidad` y `rapidez de propagación`, `disponibilidad de combustible fino y grueso`, proporcionando información esencial para la planificación, prevención y respuesta a emergencias relacionadas con incendios forestales.

Todos los calculos utilizados se basan en las formulas matemáticas que se utilizan internacionalmente.

## Explicación de los componentes del FWI

* `FFMC` (Código de Humedad del Combustible Fino): Representa el contenido de humedad de hojas secas y combustibles ligeros. Un valor bajo indica mayor humedad y menos riesgo de ignición, mientras que un valor alto sugiere que estos combustibles son más propensos a encenderse y propagarse rápidamente.
![Incendio de combustible fino](/images/IF_Merlo_comb_fino.jpg)

    ---

* `DMC` (Código de Humedad): Indica el contenido de humedad en combustibles medios.
<img src="images/IF_Merlo_comb_mediano.jpg" alt="Incendio de combustible mediano" width="350">

    ---

* `DC` (Código de Sequía): Evalúa la humedad de capas profundas y compactas de suelo orgánico y troncos grandes. Este indicador refleja los efectos acumulativos de la sequía y ayuda a estimar la cantidad de combustión latente en materiales más densos.
![Incendio de combustible grueso](/images/IF_com_grueso.jpg)

    ---
* `ISI` (Índice de Propagación Inicial): Predice qué tan rápido podría propagarse un incendio, basado en la velocidad del viento y el FFMC. Este índice no considera el tipo de vegetación, por lo que la velocidad real de propagación puede variar dependiendo del entorno.

    ---
* `BUI` (Índice de Acumulación de Combustible): Evalúa la cantidad de material combustible disponible para quemarse, combinando los datos del DMC y el DC. Indica si el incendio podría mantenerse en capas más profundas de combustible.

    ---
* `FWI` (Índice Meteorológico de Incendios): Es un indicador de la intensidad del incendio. Se calcula usando el ISI y el BUI, y proporciona un panorama general del peligro de incendios en áreas forestales.

---

## ⚙ Características principales del proyecto 
* Actualización diaria: Los datos meteorológicos se actualizan automáticamente todos los días a las `12hs Arg`.
* Consulta interactiva: Muestra estadísticas históricas y predicciones basadas en cálculos.
* Mapa visual: Los resultados se pueden visualizar en un mapa para facilitar la interpretación.

## Página Web
[Ir a la página](https://fwi.com.ar)

### Inicio:
* Al abrir la pagina, te encontrarás con un `mapa interactivo` y un menú de barras para más información en la parte superior.
    ![Inicio](/images/pag_home.png)

    ---

### Escala: 
* En la parte `inferior izquierda` encontramos la escala utilizada para interpretar el fwi, relacionando su valor con una palabra del tipo de riesgo. Y también la `fecha` de la cual se están visualizando los datos.
Tener en cuenta que se los resultados se pueden interpretar distinto según la región, por ejemplo `en la Patagonia no significa lo mismo 20 de fwi que en Misiones`. Entonces la escala en relación a el riesgo (bajo, moderado, alto, muy alto y extremo) `varía según la provincia`.
    ![Escala](/images/pag_escala.png)

    `Escala relativa de cada provincia:`
    | Provincia | Bajo | Moderado | Alto | Muy Alto | Extremo | 
    |---------- | ----- | ------- | --- | ------- | -------- |  
    |Buenos Aires | 0.00-4.10 | 4.11-12.40 | 12.41-25.50 | 25.51-42.60 | >
    |Tierra del Fuego | 0.00-0.80 | 0.81-3.70 | 3.71-9.20 | 9.21-17.60 | >
    |Santa Cruz | 0.00-12.00 | 12.01-24.40 | 24.41-42.30 | 42.31-63.90 | >
    |Chubut | 0.00-7.90 | 7.91-16.50 | 16.51-34.20 | 34.21-50.20 | >
    |Rio Negro | 0.00-7.50 | 7.51-19.50 | 19.51-37.20 | 37.21-56.40 | >
    |Neuquén | 0.00-8.30 | 8.31-20.80 | 20.81-39.40 | 39.41-59.80 | >
    |La Pampa | 0.00-4.10 | 4.11-12.40 | 12.41-25.50 | 25.51-42.60 | >
    |Mendoza | 0.00-8.30 | 8.31-20.80 | 20.81-39.40 | 39.41-59.80 | >
    |San Luis | 0.00-4.10 | 4.11-12.40 | 12.41-25.50 | 25.51-42.60 | >
    |Córdoba | 0.00-6.00 | 6.01-15.00 | 15.01-28.00 | 28.01-46.00 | >
    |Santa Fe | 0.00-1.90 | 1.91-6.70 | 6.71-13.40 | 13.41-22.40 | >
    |Entre Ríos | 0.00-1.90 | 1.91-6.70 | 6.71-13.40 | 13.41-22.40 | >
    |San Juan | 0.00-23.80 | 23.81-36.00 | 36.01-53.50 | 53.51-77.50 | >
    |La Rioja | 0.00-7.40 | 7.41-15.90 | 15.91-26.90 | 26.91-37.10 | >
    |Catamarca | 0.00-13.40 | 13.41-26.10 | 26.11-44.30 | 44.31-75.30 | >
    |Santiago Del Estero | 0.00-6.20 | 6.21-15.40 | 15.41-28.50 | 28.51-42.40 | >
    |Corrientes | 0.00-2.10 | 2.11-8.60 | 8.61-18.00 | 18.01-30.10 | >
    |Misiones | 0.00-2.10 | 2.11-8.60 | 8.61-18.00 | 18.01-30.10 | >
    |Chaco | 0.00-1.90 | 1.91-7.80 | 7.81-16.10 | 16.11-26.10 | >
    |Tucumán | 0.00-1.40 | 1.41-7.10 | 7.11-15.70 | 15.71-27.80 | >
    |Salta | 0.00-1.90 | 1.91-7.30 | 7.31-17.60 | 17.61-28.40 | >
    |Jujuy | 0.00-2.30 | 2.31-9.60 | 9.61-22.40 | 22.41-35.90 | >
    |Formosa | 0.00-2.10 | 2.11-8.60 | 8.61-18.00 | 18.01-30.10 | >


    ---

### 🔝 Ranking FWI: 
* En la parte `inferior derecha`, encontramos un `ranking` de las provincias con mayor indice FWI, tener en cuenta que se toma el valor maximo por provincia para este calculo. Recordar mirar la fecha de los datos en la parte inferior izquierda.
    ![Ranking](/images/pag_ranking.png)

    ---

### Cuadrantes:
* Se divide al territorio argentino por `cuadrantes de 15km`, tomando el punto central al cuadrado para la medición meteorologica. Cada uno de estos se `colorea automaticamente` en base a su escala FWI. Y al hacerle click nos muestra su información. (Al hacer click en "Más Info" nos redirigirá a un dashboard interactivo de ese punto con datos historicos y modelos predictivos).
    ![Cuadrantes](/images/pag_cuadrante.png)

---

### Dashboard: 
* Aquí podremos `visualizar e interpretar` distintos graficos sobre la información historica de cada punto.
    ![Dashboard](/images/pag_dashboard.png)

---

### Escalabilidad:
* Los datos tratados abarcan toda la zona del mapa, pero se colorea y publica solo la zona de Argentina, de todos modos se puede tratar los países limitrofes con el mismo metodo internacional.
    ![Escalabilidad](/images/cobertura_smn.png)

___

## 📃 Descargo de responsabilidad: 

* `fwi.com.ar` no es un medio de información oficial, sino un proyecto independiente desarrollado por bomberos voluntarios.
* Los resultados deben utilizarse como una referencia complementaria y no como una fuente única para la toma de decisiones.
* El equipo de desarrollo no se responsabiliza por errores en los cálculos ni por el uso indebido de la información proporcionada.
### Recomendación:
Se sugiere contrastar los datos con fuentes oficiales y otros modelos meteorológicos antes de utilizarlos en la toma de decisiones relacionadas con la prevención o respuesta a incendios forestales.


---

## 🛠 &nbsp;Stack Tecnológico
![Ubuntu](https://img.shields.io/badge/-Ubuntu-E95422?style=flat&logo=python&logoColor=white)
![Python](https://img.shields.io/badge/-Python-3776AB?style=flat&logo=python&logoColor=white)
![SQL](https://img.shields.io/badge/-SQL-4479A1?style=flat&logo=mysql&logoColor=white)
![Git](https://img.shields.io/badge/-Git-F05032?style=flat&logo=git&logoColor=white)
![HTML](https://shields.io/badge/HTML-f06529?logo=html5&logoColor=white&labelColor=f06529)
![CSS](https://img.shields.io/badge/CSS-239120?&style=flat&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/-Pandas-333333?style=flat&logo=pandas)
![GeoPandas](https://img.shields.io/static/v1?style=for-the-badge&message=GeoPandas&color=139C5A&style=flatlogo=GeoPandas&logoColor=FFFFFF&label=)

### Repositorio del código y base de datos: ![Click Aquí](https://github.com/matiasoviedo28/FWI_CODE)

---

## Fuentes:
- [Servicio Meteorológico Nacional](https://www.smn.gob.ar/)
- [Canadá](https://cwfis.cfs.nrcan.gc.ca/background/summary/fwi)
- [Structure of the Canadian Forest Fire Weather Index, by
C. E. Van Wagner](https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=6eb255d878bc0cead1cac0b96304ed8980349042)
- [Food and Agriculture Organization of the United Nations (FAO)](https://www.fao.org/4/XII/0738-B3.htm)
- [Manual Ministerio de Ambiente Arg.](https://drive.google.com/file/d/115Ob64dnTYDipzYPPfd-J_sI5cE6y8qt/view?usp=sharing)

## Proyecto realizado por:
* `Data Scientist y Full-Stack Developer:` [Matias Oviedo](https://github.com/matiasoviedo28), 👨‍🚒 Bombero Voluntario de Merlo, San Luis, Arg
* `Asesor:` [Alexis Lezcano](https://www.instagram.com/alexis.lezcano.794?igsh=Z3RrcWdnaTYxZHBo), 👨‍🚒 Bombero Voluntario de Merlo, San Luis, Arg

___

## 💖 Apoya este proeycto:
Gracias a personas como vos, fwi.com.ar sigue siendo gratuito para todos. Si te gusta lo que hacemos, podés ayudarnos a seguir creciendo:

[![Invitame un café en cafecito](https://cdn.cafecito.app/imgs/buttons/button_1.svg)](https://cafecito.app/fwi)
