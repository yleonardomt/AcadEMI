import io

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

PRIMARY = HexColor('#0033a0')
SECONDARY = HexColor('#f7c600')
DARK = HexColor('#1a202c')
MUTED = HexColor('#718096')


def render_certificate_pdf(certificate):
    """RF-65: genera el PDF descargable de un certificado de finalización."""
    enrollment = certificate.enrollment
    student = enrollment.student
    course = enrollment.course

    buffer = io.BytesIO()
    page_size = landscape(A4)
    width, height = page_size
    c = canvas.Canvas(buffer, pagesize=page_size)
    center_x = width / 2

    # Bordes decorativos (doble marco, como un diploma real)
    margin = 16 * mm
    c.setStrokeColor(PRIMARY)
    c.setLineWidth(3)
    c.rect(margin, margin, width - 2 * margin, height - 2 * margin, fill=0, stroke=1)

    inner_margin = margin + 4 * mm
    c.setStrokeColor(SECONDARY)
    c.setLineWidth(1.2)
    c.rect(inner_margin, inner_margin, width - 2 * inner_margin, height - 2 * inner_margin, fill=0, stroke=1)

    # Marca
    c.setFillColor(PRIMARY)
    c.setFont('Helvetica-Bold', 24)
    c.drawCentredString(center_x, height - 42 * mm, 'AcadEMI')

    c.setFillColor(MUTED)
    c.setFont('Helvetica', 11)
    c.drawCentredString(center_x, height - 50 * mm, 'CERTIFICADO DE FINALIZACIÓN')

    c.setFillColor(DARK)
    c.setFont('Helvetica', 13)
    c.drawCentredString(center_x, height - 70 * mm, 'Otorgado a')

    student_name = student.get_full_name() or student.username
    c.setFillColor(PRIMARY)
    c.setFont('Helvetica-Bold', 30)
    c.drawCentredString(center_x, height - 85 * mm, student_name)

    c.setFillColor(DARK)
    c.setFont('Helvetica', 13)
    c.drawCentredString(center_x, height - 100 * mm, 'por haber completado satisfactoriamente el curso')

    c.setFillColor(DARK)
    c.setFont('Helvetica-Bold', 18)
    course_title = course.title if len(course.title) <= 60 else course.title[:57] + '...'
    c.drawCentredString(center_x, height - 112 * mm, course_title)

    # Metadatos en 3 columnas
    meta_y = margin + 22 * mm
    col_width = (width - 2 * inner_margin) / 3

    def meta_column(index, value, label):
        x = inner_margin + col_width * index + col_width / 2
        c.setFont('Helvetica-Bold', 11)
        c.setFillColor(DARK)
        c.drawCentredString(x, meta_y + 6 * mm, str(value))
        c.setFont('Helvetica', 8)
        c.setFillColor(MUTED)
        c.drawCentredString(x, meta_y, label)

    meta_column(0, certificate.issued_at.strftime('%d/%m/%Y'), 'FECHA DE EMISIÓN')
    meta_column(1, f'{course.total_duration} min', 'DURACIÓN DEL CURSO')
    meta_column(2, certificate.certificate_code, 'CÓDIGO DE VERIFICACIÓN')

    c.setFont('Helvetica', 8)
    c.setFillColor(MUTED)
    c.drawCentredString(
        center_x, margin + 6 * mm,
        'Verifica la autenticidad de este certificado en AcadEMI con el código de verificación.'
    )

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
