import io

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

PRIMARY = HexColor('#02167f')
SECONDARY = HexColor('#ffd014')
DARK = HexColor('#1a202c')
MUTED = HexColor('#718096')
LINE = HexColor('#e2e8f0')


def render_invoice_pdf(payment):
    """RF-38: comprobante de pago descargable como PDF."""
    items = list(payment.items.select_related('course'))
    buffer = io.BytesIO()
    width, height = A4
    c = canvas.Canvas(buffer, pagesize=A4)
    left, right = 20 * mm, width - 20 * mm

    # Cabecera de marca
    c.setFillColor(PRIMARY)
    c.rect(0, height - 32 * mm, width, 32 * mm, fill=1, stroke=0)
    c.setFillColor(SECONDARY)
    c.setFont('Helvetica-Bold', 22)
    c.drawString(left, height - 20 * mm, 'AcadEMI')
    c.setFillColor(HexColor('#ffffff'))
    c.setFont('Helvetica', 10)
    c.drawString(left, height - 26 * mm, 'Plataforma educativa online')
    c.setFont('Helvetica-Bold', 12)
    c.drawRightString(right, height - 18 * mm, f'Comprobante {payment.invoice_number or payment.id}')
    c.setFont('Helvetica', 10)
    c.drawRightString(right, height - 24 * mm, payment.created_at.strftime('%d/%m/%Y %H:%M'))

    y = height - 46 * mm
    c.setFillColor(MUTED)
    c.setFont('Helvetica-Bold', 8)
    c.drawString(left, y, 'FACTURADO A')
    c.drawString(width / 2 + 5 * mm, y, 'PAGO')
    c.setFillColor(DARK)
    c.setFont('Helvetica-Bold', 11)
    name = payment.billing_name or payment.student.get_full_name() or payment.student.username
    c.drawString(left, y - 6 * mm, name)
    c.drawString(width / 2 + 5 * mm, y - 6 * mm, payment.get_payment_method_display())
    c.setFont('Helvetica', 10)
    c.setFillColor(MUTED)
    c.drawString(left, y - 12 * mm, payment.billing_email or payment.student.email)
    c.drawString(width / 2 + 5 * mm, y - 12 * mm, f'Estado: {payment.get_status_display()}')
    if payment.transaction_id:
        c.drawString(width / 2 + 5 * mm, y - 18 * mm, f'Ref: {payment.transaction_id}')
    last4 = (payment.payment_details or {}).get('card_last_four')
    if last4:
        c.drawString(left, y - 18 * mm, f'Tarjeta terminada en {last4}')

    # Tabla de cursos
    y -= 34 * mm
    c.setFillColor(PRIMARY)
    c.rect(left, y - 2 * mm, right - left, 9 * mm, fill=1, stroke=0)
    c.setFillColor(HexColor('#ffffff'))
    c.setFont('Helvetica-Bold', 9)
    c.drawString(left + 3 * mm, y + 1 * mm, 'CURSO')
    c.drawRightString(right - 3 * mm, y + 1 * mm, 'TOTAL (Bs.)')
    y -= 10 * mm
    c.setFont('Helvetica', 10)
    for item in items:
        c.setFillColor(DARK)
        c.drawString(left + 3 * mm, y, item.course.title[:70])
        c.drawRightString(right - 3 * mm, y, f'{item.price:.2f}')
        c.setStrokeColor(LINE)
        c.line(left, y - 3 * mm, right, y - 3 * mm)
        y -= 9 * mm

    # Totales
    y -= 4 * mm
    c.setFillColor(MUTED)
    c.drawRightString(right - 40 * mm, y, 'Subtotal')
    c.setFillColor(DARK)
    c.drawRightString(right - 3 * mm, y, f'Bs. {payment.amount:.2f}')
    if payment.discount_applied:
        y -= 7 * mm
        c.setFillColor(MUTED)
        c.drawRightString(right - 40 * mm, y, payment.notes or 'Descuento')
        c.setFillColor(HexColor('#10b981'))
        c.drawRightString(right - 3 * mm, y, f'- Bs. {payment.discount_applied:.2f}')
    y -= 10 * mm
    c.setFillColor(PRIMARY)
    c.setFont('Helvetica-Bold', 13)
    c.drawRightString(right - 40 * mm, y, 'TOTAL')
    c.drawRightString(right - 3 * mm, y, f'Bs. {payment.final_amount:.2f}')

    c.setFillColor(MUTED)
    c.setFont('Helvetica', 8)
    c.drawCentredString(width / 2, 15 * mm, 'AcadEMI · Escuela Militar de Ingeniería · Gracias por tu compra')
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
