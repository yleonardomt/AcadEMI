#!/usr/bin/env python3
"""Carga idempotente del catálogo de ingeniería orientado a la EMI La Paz.

Uso: .venv/bin/python scripts/load_emi_catalog.py [--archive-legacy] [--no-images]
No elimina cursos, matrículas, pagos ni respuestas existentes.
"""

import argparse
import html
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django  # noqa: E402

django.setup()

import requests  # noqa: E402
from django.conf import settings  # noqa: E402
from django.db import transaction  # noqa: E402
from django.core.files import File  # noqa: E402
from django.core.files.storage import default_storage  # noqa: E402
from django.utils import timezone  # noqa: E402
from academi.models import (  # noqa: E402
    Category, Course, Evaluation, Lesson, Module, QuestionEvaluation,
    QuestionOption, User,
)


# La oferta de carreras de la Unidad Académica La Paz se verificó en:
# https://emi.edu.bo/index.php/universidad/unidades-academicas/lapaz
# AcadEMI es una plataforma independiente: estos cursos no se anuncian como
# asignaturas oficiales ni se atribuyen a docentes de la EMI.
COURSES = [
    dict(title='Cálculo diferencial para ingeniería', area='Ciencias básicas', level='beginner', price=100,
         topic='derivadas, tasas de cambio y optimización', example='Determina la velocidad instantánea de un móvil con s(t)=3t²+2t en t=4 s.',
         answer='26 m/s', video='https://www.youtube.com/watch?v=7K1sB05pE0A', image='mathematics calculus blackboard',
         questions=[('La derivada de x² es', '2x', ['x', 'x²', '2']), ('Si s(t)=3t², la velocidad en t=2 es', '12', ['6', '9', '24']), ('Una derivada positiva indica que la función', 'crece localmente', ['decrece localmente', 'es constante', 'no es continua'])]),
    dict(title='Python aplicado a problemas de ingeniería', area='Ingeniería de Sistemas', level='beginner', price=100,
         topic='variables, estructuras de control y cálculo reproducible', example='Programa una función que calcule el promedio de 20 mediciones y alerte si supera 50.',
         answer='El promedio es suma de mediciones / 20; compara el resultado con 50.', video='https://www.youtube.com/watch?v=nykOeWgQcHM', image='computer programming code screen',
         questions=[('¿Qué estructura almacena una secuencia mutable en Python?', 'list', ['tuple', 'str', 'int']), ('¿Cuál es el promedio de 4, 6 y 8?', '6', ['5', '7', '18']), ('¿Qué instrucción repite una operación sobre una lista?', 'for', ['if', 'return', 'import'])]),
    dict(title='Álgebra lineal y matrices', area='Ciencias básicas', level='beginner', price=100,
         topic='vectores, matrices y sistemas lineales', example='Resuelve el sistema x+y=5; x−y=1 y comprueba ambos resultados.',
         answer='x=3, y=2.', video='https://ocw.mit.edu/courses/18-06sc-linear-algebra-fall-2011/', image='File:Mathematics lecture at the Helsinki University of Technology.jpg',
         questions=[('¿Cuál es la solución de x+y=5; x−y=1?', 'x=3, y=2', ['x=2, y=3', 'x=4, y=1', 'x=5, y=0']), ('La matriz identidad 2×2 tiene diagonal', '1, 1', ['0, 0', '2, 2', '1, 0']), ('Un vector en R³ tiene', '3 componentes', ['2 componentes', '4 componentes', '1 componente'])]),
    dict(title='Mecánica de estructuras y cargas', area='Ingeniería Civil', level='intermediate', price=130,
         topic='equilibrio estático, diagramas de cuerpo libre y cargas', example='Calcula las reacciones verticales de una viga simplemente apoyada de 6 m con carga puntual de 12 kN en el centro.',
         answer='6 kN en cada apoyo.', video='https://edtech.engineering.utoronto.ca/project-catalog/mechanics/beams/', image='File:Construction of Pampanga Delta Bridge & Approaches 06.jpg',
         questions=[('Una viga simplemente apoyada con carga centrada P reparte en cada apoyo', 'P/2', ['P', '2P', '0']), ('La unidad SI de fuerza es', 'newton', ['pascal', 'metro', 'vatio']), ('En equilibrio estático, la suma de fuerzas es', 'cero', ['uno', 'máxima', 'negativa siempre'])]),
    dict(title='Bases de datos y SQL para proyectos', area='Ingeniería de Sistemas', level='intermediate', price=120,
         topic='modelado relacional, consultas y calidad de datos', example='Diseña tablas Sensor(id, zona) y Lectura(id, sensor_id, valor) y consulta el promedio por zona.',
         answer='JOIN por sensor_id, GROUP BY zona y AVG(valor).', video='https://www.youtube.com/watch?v=WXk7yDqsKxs', image='File:Datacenter Server Racks (22370909788).jpg',
         questions=[('¿Qué cláusula agrupa filas para calcular AVG?', 'GROUP BY', ['ORDER BY', 'LIMIT', 'INSERT']), ('Una clave foránea referencia', 'una clave de otra tabla', ['solo texto libre', 'un índice de archivo', 'una vista']), ('¿Qué función SQL calcula el promedio?', 'AVG', ['SUM', 'COUNT', 'MAX'])]),
    dict(title='Procesos y mejora continua', area='Ingeniería Industrial', level='intermediate', price=120,
         topic='diagramas de proceso, capacidad y mejora continua', example='Una línea produce 240 piezas en 8 h. Calcula su tasa horaria y plantea un indicador de defectos.',
         answer='30 piezas/h; tasa de defectos = piezas defectuosas / total × 100.', video='https://ocw.mit.edu/courses/16-660j-introduction-to-lean-six-sigma-methods-january-iap-2012/resources/lecture-videos/', image='File:Industrial production line operating in a large modern factory.jpg',
         questions=[('240 piezas en 8 horas equivalen a', '30 piezas/h', ['20 piezas/h', '40 piezas/h', '80 piezas/h']), ('Un cuello de botella es', 'la etapa con menor capacidad', ['la etapa más cara', 'el último proceso', 'el almacén']), ('El ciclo PHVA termina con', 'Actuar', ['Planear', 'Hacer', 'Verificar'])]),
    dict(title='Circuitos eléctricos fundamentales', area='Ingeniería en Sistemas Electrónicos', level='beginner', price=110,
         topic='ley de Ohm, potencia y circuitos serie-paralelo', example='Para una resistencia de 10 Ω conectada a 20 V, calcula corriente y potencia.',
         answer='I=2 A; P=40 W.', video='https://www.youtube.com/watch?v=AfQxyVuLeCs', image='electronics circuit board engineering',
         questions=[('Con V=20 V y R=10 Ω, la corriente es', '2 A', ['0,5 A', '10 A', '200 A']), ('La potencia eléctrica se calcula con', 'P=VI', ['P=V/I', 'P=R/V', 'P=I/V']), ('En serie, la corriente por dos resistencias es', 'la misma', ['siempre cero', 'doble en la segunda', 'independiente'])]),
    dict(title='Control y sensores para mecatrónica', area='Ingeniería Mecatrónica', level='intermediate', price=150,
         topic='sensores, actuadores y control en lazo cerrado', example='Diseña un control de temperatura: define sensor, consigna, actuador y regla para encender un ventilador.',
         answer='Sensor de temperatura; consigna 30 °C; ventilador se activa al superar la consigna y se desactiva al bajar con histéresis.', video='https://www.youtube.com/watch?v=Z8oMbOj9IWM', image='robot industrial automation factory',
         questions=[('La realimentación usa', 'la salida medida', ['solo el reloj', 'un valor aleatorio', 'la potencia nominal']), ('¿Qué convierte una orden eléctrica en movimiento?', 'actuador', ['sensor', 'resistencia', 'transductor pasivo']), ('Una consigna es', 'el valor deseado', ['el error medido', 'el ruido', 'la frecuencia de muestreo'])]),
    dict(title='Señales y telecomunicaciones', area='Ingeniería en Telecomunicaciones', level='intermediate', price=130,
         topic='señales periódicas, muestreo y transmisión', example='Una señal de 1 kHz se muestrea a 3 kHz. Explica si cumple Nyquist y calcula el período de muestreo.',
         answer='Sí, 3 kHz > 2 kHz; período ≈0,333 ms.', video='https://www.youtube.com/watch?v=KJnAy6hzetw', image='telecommunications antenna tower technology',
         questions=[('La frecuencia mínima de muestreo para 1 kHz es', 'más de 2 kHz', ['menos de 1 kHz', '1 kHz exacto', '500 Hz']), ('El período de una señal de 1 kHz es', '1 ms', ['1 s', '10 ms', '0,1 s']), ('El ruido en un canal puede', 'degradar la señal', ['crear ancho de banda', 'eliminar atenuación', 'garantizar exactitud'])]),
    dict(title='Hidrología y gestión del agua', area='Ingeniería Ambiental', level='intermediate', price=120,
         topic='balance hídrico, escorrentía y calidad de agua', example='En una cuenca entran 100 mm de lluvia; 35 mm infiltran y 20 mm evapotranspiran. Estima la escorrentía.',
         answer='45 mm, si se desprecia la variación de almacenamiento.', video='https://www.youtube.com/watch?v=XHeoQ0F6hYc', image='File:River landscape scenics aerial photography.jpg',
         questions=[('Lluvia 100 mm, infiltración 35 mm y evapotranspiración 20 mm: escorrentía', '45 mm', ['35 mm', '55 mm', '80 mm']), ('El caudal se expresa habitualmente en', 'm³/s', ['m²/s', 'kg/m', 'Pa']), ('La turbidez es un indicador de', 'partículas suspendidas', ['solo temperatura', 'salinidad exacta', 'presión'])]),
    dict(title='Cartografía digital y SIG', area='Ingeniería Geográfica', level='beginner', price=110,
         topic='coordenadas, capas espaciales y análisis territorial', example='Crea un mapa de zonas de riesgo combinando una capa de pendientes y otra de cursos de agua; indica la proyección usada.',
         answer='Definir SRC, superponer capas y justificar umbrales de pendiente y distancia a cauces.', video='https://ocw.mit.edu/courses/introduction-to-r-and-gis-fall-2023/resources/lecture-videos/', image='geographic map satellite earth',
         questions=[('En un SIG, una capa vectorial puede representar', 'puntos, líneas y polígonos', ['solo píxeles', 'únicamente tablas', 'solamente sonido']), ('El SRC define', 'cómo se expresan las coordenadas', ['la resolución de pantalla', 'el color del mapa', 'el peso del archivo']), ('Una escala 1:50 000 significa que 1 cm representa', '500 m', ['50 m', '5 km', '50 km'])]),
    dict(title='Fundamentos de ingeniería petrolera', area='Ingeniería Petrolera', level='beginner', price=130,
         topic='porosidad, permeabilidad y balance de fluidos', example='Una muestra de roca tiene 25 cm³ de poros en 100 cm³ de volumen total. Calcula la porosidad.',
         answer='25 %.', video='https://www.youtube.com/watch?v=8mfBomrw0rs', image='File:Oil platform P-51 (Brazil).jpg',
         questions=[('25 cm³ de poros en 100 cm³ de roca dan porosidad de', '25 %', ['4 %', '40 %', '75 %']), ('La permeabilidad describe', 'facilidad de flujo en la roca', ['volumen total', 'densidad del crudo', 'temperatura']), ('La presión suele medirse en', 'Pa', ['kg', 'm³', 'W'])]),
    dict(title='Matemática financiera aplicada', area='Ingeniería Financiera', level='beginner', price=110,
         topic='interés compuesto, valor presente y evaluación de proyectos', example='Invierte Bs 1.000 al 10 % anual compuesto durante dos años. Calcula el valor futuro.',
         answer='Bs 1.210.', video='https://www.youtube.com/watch?v=Rm6UdfRs3gw', image='File:Calculator-385506 1280.jpg',
         questions=[('Bs 1000 al 10 % compuesto por 2 años valen', 'Bs 1210', ['Bs 1100', 'Bs 1200', 'Bs 1002']), ('El valor presente descuenta', 'flujos futuros', ['solo costos históricos', 'el número de clientes', 'la inflación a cero']), ('Un VAN positivo, bajo supuestos correctos, indica', 'valor añadido', ['pérdida segura', 'tasa cero', 'ausencia de riesgo'])]),
    dict(title='Análisis de mercados y costos', area='Ingeniería Comercial', level='beginner', price=110,
         topic='segmentación, costos y punto de equilibrio', example='Con costo fijo Bs 1.000, precio Bs 20 y costo variable Bs 10 por unidad, calcula el punto de equilibrio.',
         answer='100 unidades.', video='https://www.youtube.com/watch?v=ShzPtU7IOXs', image='File:Business breakfast meeting. (54641476579).jpg',
         questions=[('CF=1000, P=20 y CV=10: equilibrio en unidades', '100', ['50', '200', '1000']), ('El margen de contribución unitario es', 'precio menos costo variable', ['precio más costo fijo', 'ingreso total', 'costo fijo / precio']), ('Segmentar mercado consiste en', 'agrupar clientes con características comunes', ['fijar un precio único', 'eliminar competencia', 'aumentar inventario'])]),
    dict(title='Bases de datos MySQL: consultas y modelado', area='Ingeniería de Sistemas', level='intermediate', price=150,
         topic='consultas SQL, relaciones, filtros y agregaciones en MySQL', example='Consulta las ventas por mes y ordena los meses por ingreso total.',
         answer='Agrupa con YEAR(fecha), MONTH(fecha) y SUM(total), y ordena por periodo.', video='https://www.youtube.com/playlist?list=PLdq5lNsLUFYB79viP4Uc_7NRhdt4UTBlc', image='database server computer code',
         questions=[('¿Qué cláusula filtra grupos agregados?', 'HAVING', ['WHERE', 'ORDER BY', 'LIMIT']), ('¿Qué garantiza una clave primaria?', 'identifica de forma única cada fila', ['ordena todas las filas', 'cifra la tabla', 'permite valores repetidos']), ('¿Qué operación combina filas relacionadas?', 'JOIN', ['DROP', 'ALTER', 'TRUNCATE'])]),
    dict(title='Programación orientada a objetos con Java', area='Ingeniería de Sistemas', level='intermediate', price=120,
         topic='clases, encapsulamiento, herencia e interfaces', example='Modela un sistema de préstamos con las clases Libro, Usuario y Prestamo.',
         answer='Separa entidades, encapsula estado y define operaciones explícitas para prestar y devolver.', video='https://dev.java/learn/', image='java programming laptop',
         questions=[('Una clase describe', 'estado y comportamiento de objetos', ['solo una variable', 'un archivo ejecutable', 'una consulta SQL']), ('Encapsular significa', 'controlar el acceso al estado interno', ['duplicar clases', 'evitar métodos', 'convertir todo en público']), ('Una interfaz define', 'un contrato de operaciones', ['una base de datos', 'un constructor obligatorio siempre', 'un paquete de imágenes'])]),
    dict(title='Redes de computadores y direccionamiento IP', area='Ingeniería de Sistemas', level='beginner', price=110,
         topic='modelo TCP/IP, subredes, DNS y diagnóstico de conectividad', example='Divide 192.168.10.0/24 en cuatro subredes del mismo tamaño.',
         answer='Se necesitan /26; cada subred tiene 64 direcciones (62 hosts utilizables).', video='https://www.cloudflare.com/learning/network-layer/what-is-a-computer-network/', image='network cables server rack',
         questions=[('DNS traduce principalmente', 'nombres de dominio a direcciones IP', ['MAC a voltaje', 'puertos a contraseñas', 'archivos a paquetes']), ('Una máscara /24 contiene', '24 bits de red', ['24 hosts', '24 routers', '24 bytes']), ('TCP ofrece', 'entrega ordenada y control de retransmisión', ['solo difusión local', 'direccionamiento físico', 'cifrado siempre'])]),
    dict(title='Análisis de datos con Python y pandas', area='Ingeniería de Sistemas', level='intermediate', price=120,
         topic='limpieza, transformación, agrupación y visualización de datos', example='Calcula el promedio mensual de mediciones y detecta valores faltantes.',
         answer='Convierte la fecha, agrupa por mes, aplica mean y revisa isna antes del análisis.', video='https://pandas.pydata.org/docs/getting_started/intro_tutorials/', image='data analysis python charts',
         questions=[('pandas representa datos tabulares con', 'DataFrame', ['Socket', 'Thread', 'Canvas']), ('Para agrupar filas por categoría se usa', 'groupby', ['merge_asof solamente', 'astype', 'rename']), ('Un valor faltante se identifica con', 'isna', ['isunique', 'isnumeric', 'isalpha'])]),
    dict(title='Evaluación financiera de proyectos de inversión', area='Ingeniería Financiera', level='intermediate', price=130,
         topic='flujo de caja, VAN, TIR y análisis de sensibilidad', example='Evalúa un proyecto con inversión inicial y flujos anuales descontados a una tasa dada.',
         answer='Calcula VAN con los flujos netos y la tasa de descuento; acepta bajo los supuestos si VAN es positivo.', video='https://www.khanacademy.org/economics-finance-domain/core-finance/interest-tutorial', image='financial analysis investment calculator',
         questions=[('El VAN descuenta', 'flujos futuros a valor presente', ['solo la inversión inicial', 'unidades producidas', 'impuestos a cero']), ('Una TIR es una tasa que hace', 'VAN igual a cero', ['ingresos iguales a unidades', 'costo fijo nulo', 'inflación negativa']), ('El análisis de sensibilidad evalúa', 'cómo cambian resultados al variar supuestos', ['el color del informe', 'solo el costo hundido', 'el número de páginas'])]),
    dict(title='Estadística aplicada a decisiones financieras', area='Ingeniería Financiera', level='intermediate', price=120,
         topic='distribuciones, intervalos, correlación y riesgo', example='Compara el rendimiento promedio y la desviación estándar de dos alternativas.',
         answer='Considera retorno esperado junto con dispersión; una media mayor no implica menor riesgo.', video='https://www.openintro.org/book/os/', image='statistics finance charts',
         questions=[('La desviación estándar mide', 'dispersión respecto a la media', ['tamaño de muestra únicamente', 'sesgo siempre', 'causalidad']), ('Correlación alta demuestra', 'asociación, no causalidad por sí sola', ['causalidad segura', 'igualdad de variables', 'ausencia de datos']), ('Un intervalo de confianza expresa', 'incertidumbre de una estimación', ['un valor exacto garantizado', 'el tamaño del universo siempre', 'una tasa bancaria'])]),
    dict(title='Contabilidad de costos para ingeniería', area='Ingeniería Financiera', level='beginner', price=110,
         topic='costos fijos y variables, costeo unitario y margen de contribución', example='Calcula el costo unitario para una producción dada y separa costos fijos de variables.',
         answer='Suma costos del periodo según el método elegido y divide por unidades equivalentes producidas.', video='https://www.accountingcoach.com/managerial-accounting/explanation', image='accounting cost calculation',
         questions=[('Un costo fijo total', 'no cambia con el volumen en el rango relevante', ['siempre es cero', 'es idéntico al costo variable', 'depende solo del precio']), ('Costo variable unitario suele', 'mantenerse aproximadamente constante en el rango relevante', ['duplicarse cada día', 'ser igual al costo fijo total', 'no existir']), ('Margen de contribución es', 'ventas menos costos variables', ['ventas menos activos', 'inventario más deuda', 'costo fijo por periodo'])]),
    dict(title='Mecánica clásica: cinemática y dinámica', area='Ingeniería Mecánica', level='beginner', price=110,
         topic='movimiento, leyes de Newton, trabajo y energía', example='Determina aceleración de un cuerpo de 10 kg bajo una fuerza neta de 30 N.',
         answer='a=F/m=3 m/s².', video='https://www.khanacademy.org/science/physics/forces-newtons-laws', image='mechanics physics engineering motion',
         questions=[('La segunda ley de Newton relaciona', 'fuerza neta, masa y aceleración', ['presión y temperatura solamente', 'carga y voltaje', 'caudal y área']), ('La unidad SI de energía es', 'joule', ['newton', 'pascal', 'ampere']), ('Si la fuerza neta es cero, la aceleración es', 'cero', ['máxima', 'igual a la masa', 'siempre negativa'])]),
    dict(title='Termodinámica aplicada a sistemas energéticos', area='Ingeniería Mecánica', level='intermediate', price=130,
         topic='primera ley, propiedades, ciclos y balances de energía', example='Formula un balance de energía para un volumen de control en régimen estacionario.',
         answer='Iguala calor y trabajo netos con los cambios de entalpía, energía cinética y potencial.', video='https://www.nptel.ac.in/courses/112/105/112105123/', image='thermodynamics power plant turbine',
         questions=[('La primera ley expresa conservación de', 'energía', ['masa molar', 'temperatura absoluta', 'entropía solamente']), ('En régimen estacionario, la masa dentro del volumen de control', 'no cambia con el tiempo', ['siempre es cero', 'crece sin límite', 'se vuelve energía']), ('La entalpía específica se define como', 'u + Pv', ['u − Pv', 'P/v', 'mgh'])]),
    dict(title='Resistencia de materiales y diseño mecánico', area='Ingeniería Mecánica', level='intermediate', price=130,
         topic='esfuerzo, deformación, flexión y factor de seguridad', example='Calcula el esfuerzo normal promedio de una barra sometida a carga axial.',
         answer='σ=P/A, verificando unidades y comparando con el esfuerzo admisible.', video='https://mechref.engr.illinois.edu/sol/index.html', image='mechanical engineering steel stress testing',
         questions=[('El esfuerzo normal promedio es', 'fuerza axial dividida entre área', ['área por longitud', 'masa por volumen', 'deformación por tiempo']), ('La deformación unitaria es', 'cambio de longitud dividido entre longitud inicial', ['fuerza por área', 'masa por aceleración', 'longitud por fuerza']), ('Un factor de seguridad mayor que uno indica', 'resistencia admisible superior a la solicitación calculada', ['falla inevitable', 'carga nula', 'ausencia de incertidumbre'])]),
    dict(title='Mecánica de fluidos y pérdidas de carga', area='Ingeniería Civil', level='intermediate', price=130,
         topic='continuidad, Bernoulli, régimen de flujo y pérdidas', example='Estima cómo cambia la velocidad al reducir el área de una tubería con caudal constante.',
         answer='Por continuidad, la velocidad aumenta en proporción inversa al área.', video='https://www.nptel.ac.in/courses/112/105/112105171/', image='fluid mechanics water pipe flow',
         questions=[('La ecuación de continuidad representa conservación de', 'masa', ['temperatura', 'presión únicamente', 'potencia eléctrica']), ('Número de Reynolds ayuda a clasificar', 'régimen de flujo', ['dureza del material', 'nivel topográfico', 'voltaje']), ('Una pérdida de carga representa', 'disipación de energía mecánica del flujo', ['creación de masa', 'aumento de caudal siempre', 'cambio de unidades'])]),
    dict(title='Topografía y levantamientos de obra', area='Ingeniería Civil', level='beginner', price=110,
         topic='nivelación, coordenadas, errores y replanteo', example='Calcula la diferencia de nivel entre dos puntos a partir de lecturas de mira.',
         answer='Aplica altura de instrumento menos lectura adelante, conservando el signo y las unidades.', video='https://www.usgs.gov/programs/national-geospatial-program', image='land surveying total station construction',
         questions=[('La nivelación determina principalmente', 'diferencias de altura', ['resistencia eléctrica', 'caudal de diseño', 'costo financiero']), ('Un cierre de nivelación sirve para', 'estimar el error de cierre', ['eliminar observaciones sin criterio', 'medir temperatura', 'definir materiales']), ('El replanteo traslada', 'puntos del diseño al terreno', ['datos del terreno al laboratorio solamente', 'costos a balances', 'una imagen a PDF'])]),
    dict(title='Automatización industrial con PLC', area='Ingeniería Industrial', level='intermediate', price=130,
         topic='entradas y salidas, lógica de control, secuencias y seguridad', example='Diseña una secuencia de arranque-parada con enclavamiento y paro de emergencia.',
         answer='Prioriza el paro de emergencia y evita rearranque automático tras recuperar energía.', video='https://www.plcopen.org/technical-activities/', image='industrial PLC automation control panel',
         questions=[('Una entrada digital suele representar', 'dos estados lógicos', ['cualquier número decimal sin conversión', 'solo temperatura', 'un archivo']), ('El enclavamiento evita', 'estados incompatibles de operación', ['toda medición', 'el mantenimiento', 'la lectura de sensores']), ('Un paro de emergencia debe', 'llevar el proceso a un estado seguro', ['iniciar automáticamente', 'anular protecciones', 'borrar el programa'])]),
    dict(title='Máquinas eléctricas y transformadores', area='Ingeniería en Sistemas Electrónicos', level='intermediate', price=130,
         topic='transformadores, motores, potencia y eficiencia', example='Estima la corriente primaria ideal de un transformador con potencia y tensión conocidas.',
         answer='En el caso monofásico ideal, I=P/V; considera factor de potencia y pérdidas si corresponden.', video='https://www.nptel.ac.in/courses/108/105/108105155/', image='electric motor transformer engineering',
         questions=[('Un transformador ideal cambia', 'niveles de tensión y corriente en CA', ['frecuencia de red', 'potencia activa creando energía', 'corriente continua a mecánica directamente']), ('La eficiencia es', 'potencia útil de salida sobre potencia de entrada', ['pérdidas sobre voltaje', 'corriente por resistencia solamente', 'frecuencia por área']), ('Un motor convierte principalmente', 'energía eléctrica en energía mecánica', ['masa en carga', 'calor en datos', 'presión en tensión eléctrica'])]),
    dict(title='Gestión de proyectos de ingeniería', area='Ingeniería Industrial', level='beginner', price=110,
         topic='alcance, cronograma, riesgos, costos e indicadores', example='Construye una matriz de riesgos con probabilidad, impacto, respuesta y responsable.',
         answer='Prioriza riesgos por probabilidad e impacto, define respuesta y asigna un responsable verificable.', video='https://www.pmi.org/learning/library', image='engineering project planning team',
         questions=[('La ruta crítica identifica', 'actividades que determinan la duración mínima del proyecto', ['todas las tareas opcionales', 'solo gastos indirectos', 'el equipo más grande']), ('Un riesgo debe incluir', 'probabilidad, impacto y respuesta', ['solo un nombre', 'una fecha pasada', 'un costo sin contexto']), ('Un indicador útil debe ser', 'medible y vinculado a un objetivo', ['ambiguo', 'imposible de actualizar', 'distinto cada día'])]),
    dict(title='Seguridad industrial y análisis de riesgos', area='Ingeniería Industrial', level='beginner', price=110,
         topic='identificación de peligros, evaluación de riesgos y controles', example='Analiza una tarea de mantenimiento y propone controles según la jerarquía de control.',
         answer='Prioriza eliminar o sustituir el peligro, luego controles de ingeniería, administrativos y EPP.', video='https://www.osha.gov/safety-management', image='industrial safety equipment engineering',
         questions=[('La jerarquía de controles prioriza primero', 'eliminación del peligro', ['equipo de protección personal', 'señalización solamente', 'capacitación solamente']), ('Un peligro es', 'una fuente o situación con potencial de daño', ['un control instalado', 'un indicador de producción', 'un permiso aprobado']), ('El EPP se considera', 'una barrera final complementaria', ['sustituto universal de controles', 'eliminación del peligro', 'garantía de riesgo cero'])]),
    dict(title='Energías renovables y dimensionamiento fotovoltaico', area='Ingeniería Ambiental', level='beginner', price=120,
         topic='recurso solar, potencia, energía, pérdidas y diseño preliminar', example='Estima energía diaria con potencia pico, horas solares y un factor de rendimiento.',
         answer='Energía diaria aproximada = potencia pico × horas solares × factor de rendimiento.', video='https://www.nrel.gov/research/re-photovoltaics.html', image='solar panels renewable energy engineering',
         questions=[('La potencia pico se expresa normalmente en', 'W o kW', ['kWh exclusivamente', 'amperios-hora solamente', 'metros']), ('La energía generada depende de', 'irradiación, potencia y pérdidas', ['solo el color del panel', 'la latitud sin clima', 'el voltaje nominal aislado']), ('Un inversor convierte', 'corriente continua en corriente alterna', ['energía en masa', 'frecuencia en irradiación', 'potencia en área'])]),
    dict(title='Telecomunicaciones: modulación y ancho de banda', area='Ingeniería en Telecomunicaciones', level='intermediate', price=120,
         topic='señales, modulación, espectro y capacidad de canal', example='Compara ancho de banda requerido y tasa de símbolos para un esquema digital.',
         answer='Distingue tasa de bits, tasa de símbolos, ancho de banda y eficiencia espectral.', video='https://www.nptel.ac.in/courses/108/102/108102096/', image='telecommunications radio antenna signal',
         questions=[('La modulación permite', 'adaptar una señal para su transmisión por un canal', ['eliminar toda interferencia', 'crear ancho de banda infinito', 'evitar codificación']), ('La frecuencia se mide en', 'hertz', ['joule', 'ohm', 'newton']), ('El ancho de banda describe', 'rango de frecuencias ocupado o disponible', ['potencia total siempre', 'distancia física', 'tamaño del archivo'])]),
    dict(title='Economía de operaciones y cadena de suministro', area='Ingeniería Comercial', level='intermediate', price=120,
         topic='inventarios, demanda, costos logísticos e indicadores', example='Compara el costo de mantener inventario con el costo de emitir pedidos.',
         answer='Busca el lote económico bajo supuestos explícitos y verifica sensibilidad a demanda y costos.', video='https://ocw.mit.edu/courses/15-761-introduction-to-operations-management-spring-2004/', image='supply chain warehouse logistics',
         questions=[('El inventario de seguridad busca', 'amortiguar incertidumbre de demanda o reposición', ['aumentar obsolescencia', 'eliminar pronósticos', 'reemplazar calidad']), ('El tiempo de ciclo mide', 'duración de un proceso definido', ['precio unitario', 'tamaño del almacén', 'número de proveedores']), ('Un pronóstico debe evaluarse con', 'error frente a observaciones reales', ['solo intuición', 'margen bruto', 'velocidad del equipo'])]),
]


def download_image(query, slug):
    """Usa miniaturas Wikimedia con licencia explícita y guarda atribución."""
    target = Path(settings.MEDIA_ROOT) / 'courses' / f'emi-{slug}.jpg'
    if target.exists() and target.stat().st_size > 5000:
        return f'courses/{target.name}', None
    api = 'https://commons.wikimedia.org/w/api.php'
    params = {'action': 'query', 'prop': 'imageinfo',
              'iiprop': 'url|size|extmetadata', 'iiurlwidth': 1100, 'format': 'json'}
    if query.startswith('File:'):
        params['titles'] = query
    else:
        params.update({'generator': 'search', 'gsrsearch': query + ' filetype:bitmap',
                       'gsrnamespace': 6, 'gsrlimit': 12})
    headers = {'User-Agent': 'AcadEMI-Catalog/1.0 (educational catalog; info@academi.bo)'}
    data = requests.get(api, params=params, headers=headers, timeout=20).json()
    pages = sorted(data.get('query', {}).get('pages', {}).values(), key=lambda p: p.get('index', 99))
    for page in pages:
        if not page['title'].lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            continue
        info = page.get('imageinfo', [{}])[0]
        meta = info.get('extmetadata', {})
        license_name = html.unescape(re.sub('<[^>]+>', '', meta.get('LicenseShortName', {}).get('value', '')))
        if not (license_name.startswith('CC BY') or license_name in {'CC0', 'Public domain'}):
            continue
        if info.get('width', 0) < 700 or info.get('height', 0) < 400 or info.get('width', 0) < info.get('height', 0) * 1.15:
            continue
        url = info.get('thumburl')
        if not url:
            continue
        try:
            response = requests.get(url, headers=headers, timeout=25)
            response.raise_for_status()
            if not response.headers.get('content-type', '').startswith('image/') or len(response.content) < 5000:
                continue
            from PIL import Image
            from io import BytesIO
            image = Image.open(BytesIO(response.content)).convert('RGB')
            image.thumbnail((1100, 750))
            target.parent.mkdir(parents=True, exist_ok=True)
            image.save(target, 'JPEG', quality=84, optimize=True)
            author = ' '.join(html.unescape(re.sub('<[^>]+>', '', meta.get('Artist', {}).get('value', 'Autor no indicado'))).split())
            source = info.get('descriptionurl', '')
            return f'courses/{target.name}', f'{target.name} | {page["title"]} | {author} | {license_name} | {source}'
        except (requests.RequestException, OSError):
            continue
    return None, None


def upsert_lesson(module, order, title, kind, content='', video='', is_free=False, duration=15):
    lesson, _ = Lesson.objects.update_or_create(module=module, title=title, defaults={
        'order': order, 'lesson_type': kind, 'content': content, 'description': content[:180],
        'video_url': video or None, 'is_free': is_free, 'is_published': True,
        'duration_minutes': duration,
    })
    return lesson


def sync_bundled_images():
    """Conserva las fotos del catálogo si se activa S3 después del primer deploy."""
    if settings.STORAGES['default']['BACKEND'] == 'django.core.files.storage.FileSystemStorage':
        return
    for image_file in (ROOT / 'media' / 'courses').glob('emi-*.jpg'):
        image_path = f'courses/{image_file.name}'
        if not default_storage.exists(image_path):
            with image_file.open('rb') as source:
                default_storage.save(image_path, File(source))


def sync_mysql_playlist():
    """Un video público por lección; conserva progresos y títulos editados fuera de este curso."""
    course = Course.objects.filter(title='Bases de datos MySQL: consultas y modelado').first()
    if not course:
        return
    data = json.loads((ROOT / 'scripts/data/mysql_playlist.json').read_text())
    labels = ['Introducción y creación de bases de datos', 'Consultas y operadores',
              'Agrupación, índices y JOIN', 'UNION y subconsultas',
              'Subconsultas y vistas', 'Vistas y procedimientos almacenados',
              'Funciones y ALTER TABLE', 'Actualización, administración y complementos']
    with transaction.atomic():
        if course.is_free:
            price = next(item['price'] for item in COURSES if item['title'] == course.title)
            Course.objects.filter(pk=course.pk).update(is_free=False, price=price)
        course.modules.filter(title='Fundamentos').update(order=0)
        course.modules.filter(title='Aplicación y evaluación').update(order=9)
        Lesson.objects.filter(module__course=course, video_url__contains='playlist?list=PLdq5lNsLUFYB79viP4Uc_7NRhdt4UTBlc').update(
            lesson_type='text', video_url=None, is_published=True, title='Fuentes del curso MySQL',
            content=f'Videos de {data["author"]}: {data["channel"]}. Cada clase del playlist MYSQL está disponible como una lección individual en los módulos siguientes.')
        for index, video in enumerate(data['videos']):
            block = index // 10
            module, _ = Module.objects.update_or_create(course=course,
                order=block + 1, defaults={
                    'title': f'{block + 1:02d}. {labels[block]}', 'description': f'Videos {block * 10 + 1} a {min((block + 1) * 10, len(data["videos"]))} del playlist MYSQL de {data["author"]}.'})
            author = video.get('author', data['author'])
            note = f'Clase de {author}. Fuente: https://www.youtube.com/watch?v={video["id"]}. Reproduce el video y practica sus consultas en tu propia base de datos.'
            if 'MD5' in video['title']:
                note += ' Nota de actualización: MD5 y SHA sin un esquema especializado no son adecuados para almacenar contraseñas; utiliza algoritmos modernos como Argon2id.'
            Lesson.objects.update_or_create(module=module,
                video_url=f'https://www.youtube.com/watch?v={video["id"]}', defaults={
                    'title': video['title'][:200], 'description': f'Clase {index + 1} de {len(data["videos"])} · {author}',
                    'content': note, 'lesson_type': 'video', 'order': index % 10 + 1,
                    'is_free': index == 0, 'is_published': True, 'duration_minutes': video['duration_minutes']})
    print(f'MySQL: {len(data["videos"])} videos cargados como lecciones individuales.')


def run(archive_legacy=False, no_images=False, only_if_empty=False):
    sync_bundled_images()
    existing_titles = set()
    if only_if_empty:
        existing_titles = set(Course.objects.filter(
            title__in=[item['title'] for item in COURSES],
        ).values_list('title', flat=True))
        if len(existing_titles) == len(COURSES):
            sync_mysql_playlist()
            print('El catálogo inicial ya está completo; no se modifica.')
            return
    teacher, _ = User.objects.get_or_create(username='equipo_academi', defaults={
        'email': 'equipo@academi.local', 'first_name': 'Equipo', 'last_name': 'AcadEMI',
        'role': 'teacher', 'is_active': True, 'email_verified': True,
        'teacher_full_name': 'Equipo AcadEMI', 'specialty': 'Material académico de ingeniería',
        'institution': 'AcadEMI',
    })
    if not teacher.has_usable_password():
        pass
    else:
        teacher.set_unusable_password()
        teacher.save(update_fields=['password'])
    archive_titles = {item['title'] for item in COURSES}
    if archive_legacy:
        changed = Course.objects.filter(status='published').exclude(title__in=archive_titles).update(status='archived', is_featured=False)
        print(f'Cursos anteriores archivados: {changed}')
    attribution = []
    for index, item in enumerate(COURSES):
        if item['title'] in existing_titles:
            continue
        area, _ = Category.objects.get_or_create(name=item['area'], defaults={
            'description': f'Cursos aplicados a {item["area"].lower()} para estudiantes de ingeniería.'})
        slug = re.sub(r'[^a-z0-9]+', '-', item['title'].lower().translate(str.maketrans('áéíóúñ', 'aeioun'))).strip('-')
        image_path = None
        bundled_image = ROOT / 'media' / 'courses' / f'emi-{slug}.jpg'
        if bundled_image.is_file():
            image_path = f'courses/{bundled_image.name}'
        elif not no_images:
            try:
                image_path, credit = download_image(item['image'], slug)
                if credit:
                    attribution.append(credit)
            except (requests.RequestException, ValueError) as exc:
                print(f'Imagen pendiente para {item["title"]}: {exc}')
        if not image_path:
            # Fotos existentes del mismo ámbito, reutilizadas con su atribución.
            fallback = {
                'Ingeniería de Sistemas': 'bases-de-datos-y-sql-para-proyectos',
                'Ingeniería Financiera': 'matematica-financiera-aplicada',
                'Ingeniería Mecánica': 'control-y-sensores-para-mecatronica',
                'Ingeniería Civil': 'mecanica-de-estructuras-y-cargas',
                'Ingeniería Industrial': 'procesos-y-mejora-continua',
                'Ingeniería en Sistemas Electrónicos': 'circuitos-electricos-fundamentales',
                'Ingeniería Ambiental': 'hidrologia-y-gestion-del-agua',
                'Ingeniería en Telecomunicaciones': 'senales-y-telecomunicaciones',
                'Ingeniería Comercial': 'analisis-de-mercados-y-costos',
            }.get(item['area'])
            if fallback and (ROOT / 'media/courses' / f'emi-{fallback}.jpg').is_file():
                image_path = f'courses/emi-{fallback}.jpg'
        with transaction.atomic():
            defaults = {'description': (
                f'Aprende {item["topic"]} con casos de ingeniería, ejercicios resueltos y una evaluación final. '
                'Incluye un proyecto práctico con criterios de entrega y retroalimentación en la plataforma.'),
                'category': area, 'teacher': teacher, 'level': item['level'], 'price': item['price'],
                'is_free': item['price'] == 0, 'is_featured': index < 6, 'status': 'published',
                'published_at': timezone.now(), 'approved_at': timezone.now(), 'approved_by': User.objects.filter(is_superuser=True).first(),
            }
            if image_path:
                defaults['image'] = image_path
            course, _ = Course.objects.update_or_create(title=item['title'], teacher=teacher, defaults=defaults)
            intro, _ = Module.objects.update_or_create(course=course, title='Fundamentos', defaults={
                'order': 1, 'description': f'Conceptos básicos de {item["topic"]}.'})
            applied, _ = Module.objects.update_or_create(course=course, title='Aplicación y evaluación', defaults={
                'order': 2, 'description': 'Resuelve un caso aplicado y comprueba lo aprendido.'})
            upsert_lesson(intro, 1, 'Guía de aprendizaje', 'text',
                f'Objetivo: comprender {item["topic"]}.\n\nAntes de comenzar, identifica las unidades de cada variable y anota los supuestos de tu modelo. '
                'Después de cada ejercicio, verifica el resultado sustituyéndolo en el planteamiento original.\n\n'
                f'Caso de referencia: {item["example"]}\nResultado esperado: {item["answer"]}', is_free=True, duration=20)
            if item['video'] and 'playlist?list=' not in item['video']:
                upsert_lesson(intro, 2, 'Video complementario: fundamentos', 'video',
                    'Material audiovisual de fuente abierta. Revisa la fuente original enlazada y toma notas de los conceptos aplicables al caso del curso.',
                    video=item['video'], is_free=True, duration=40)
            upsert_lesson(intro, 3, 'Ejercicio resuelto paso a paso', 'text',
                f'Enunciado: {item["example"]}\n\nProcedimiento: 1) Identifica datos y unidades. 2) Selecciona la ecuación o método pertinente. '
                f'3) Sustituye y calcula. 4) Verifica magnitud y unidades.\n\nComprobación: {item["answer"]}', duration=25)
            upsert_lesson(applied, 1, 'Práctica aplicada', 'assignment',
                f'Problema: {item["example"]}\n\nEntrega un PDF de 1 a 3 páginas con: datos, procedimiento, resultado y una breve interpretación. '
                'Incluye una comprobación independiente y cita cualquier recurso externo.\n\n'
                f'Referencia para autoevaluación: {item["answer"]}\n\nRúbrica: planteamiento 25 %, procedimiento 35 %, resultado 25 %, explicación 15 %.', duration=60)
            exam = upsert_lesson(applied, 2, 'Examen de aplicación', 'exam',
                'Responde las preguntas de aplicación. Puedes revisar las lecciones antes de iniciar.', duration=25)
            evaluation, _ = Evaluation.objects.update_or_create(lesson=exam, defaults={
                'title': f'Examen: {item["title"]}', 'evaluation_type': 'exam', 'time_limit_minutes': 25,
                'passing_score': 66, 'max_attempts': 3, 'is_active': True,
            })
            for number, (prompt, correct, incorrect) in enumerate(item['questions'], 1):
                question, _ = QuestionEvaluation.objects.update_or_create(evaluation=evaluation, order=number,
                    defaults={'text': prompt, 'question_type': 'single', 'points': 1})
                # Si alguien ya respondió, no borramos opciones; solo corregimos las existentes.
                for value in [correct, *incorrect]:
                    QuestionOption.objects.update_or_create(question=question, text=value,
                        defaults={'is_correct': value == correct})
        print(f'✓ {course.title} ({course.get_price_display()})')
    if attribution:
        credits = ROOT / 'docs' / 'FUENTES_CATALOGO.md'
        credits.parent.mkdir(exist_ok=True)
        existing = credits.read_text() if credits.exists() else '# Fuentes de imágenes del catálogo\n\nImágenes de Wikimedia Commons. Consultar la licencia de cada archivo antes de redistribuir.\n\n'
        known = {line.split(' | ')[0] for line in existing.splitlines()}
        with credits.open('a') as f:
            for credit in attribution:
                if credit.split(' | ')[0] not in known:
                    f.write(credit + '\n')
    sync_mysql_playlist()
    print(f'Catálogo actualizado: {len(COURSES)} cursos, {Course.objects.filter(status="published").count()} publicados.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive-legacy', action='store_true', help='Archiva cursos publicados anteriores, sin borrar datos históricos')
    parser.add_argument('--no-images', action='store_true', help='Omite descarga de imágenes')
    parser.add_argument('--only-if-empty', action='store_true', help='Solo crea el catálogo si aún no hay cursos')
    arguments = parser.parse_args()
    run(arguments.archive_legacy, arguments.no_images, arguments.only_if_empty)
