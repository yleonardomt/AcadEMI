"""Actualiza los precios de catálogo; conserva compras y matrículas anteriores."""
from django.db import migrations

PRICES = {'Cálculo diferencial para ingeniería': 100,
 'Python aplicado a problemas de ingeniería': 100,
 'Álgebra lineal y matrices': 100,
 'Mecánica de estructuras y cargas': 130,
 'Bases de datos y SQL para proyectos': 120,
 'Procesos y mejora continua': 120,
 'Circuitos eléctricos fundamentales': 110,
 'Control y sensores para mecatrónica': 150,
 'Señales y telecomunicaciones': 130,
 'Hidrología y gestión del agua': 120,
 'Cartografía digital y SIG': 110,
 'Fundamentos de ingeniería petrolera': 130,
 'Matemática financiera aplicada': 110,
 'Análisis de mercados y costos': 110,
 'Bases de datos MySQL: consultas y modelado': 150,
 'Programación orientada a objetos con Java': 120,
 'Redes de computadores y direccionamiento IP': 110,
 'Análisis de datos con Python y pandas': 120,
 'Evaluación financiera de proyectos de inversión': 130,
 'Estadística aplicada a decisiones financieras': 120,
 'Contabilidad de costos para ingeniería': 110,
 'Mecánica clásica: cinemática y dinámica': 110,
 'Termodinámica aplicada a sistemas energéticos': 130,
 'Resistencia de materiales y diseño mecánico': 130,
 'Mecánica de fluidos y pérdidas de carga': 130,
 'Topografía y levantamientos de obra': 110,
 'Automatización industrial con PLC': 130,
 'Máquinas eléctricas y transformadores': 130,
 'Gestión de proyectos de ingeniería': 110,
 'Seguridad industrial y análisis de riesgos': 110,
 'Energías renovables y dimensionamiento fotovoltaico': 120,
 'Telecomunicaciones: modulación y ancho de banda': 120,
 'Economía de operaciones y cadena de suministro': 120}

def update_prices(apps, schema_editor):
    Course = apps.get_model("academi", "Course")
    for title, price in PRICES.items():
        Course.objects.using(schema_editor.connection.alias).filter(title=title).update(price=price, is_free=False)

class Migration(migrations.Migration):
    dependencies = [("academi", "0012_coupon_demo_used_count")]
    operations = [migrations.RunPython(update_prices, migrations.RunPython.noop)]
