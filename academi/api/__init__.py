"""API JSON (v1) que consume la app móvil de AcadEMI (carpeta MOVIL/).

Está separada de las vistas HTML: autenticación por token Bearer (sin
sesión ni CSRF, porque la app móvil no es un navegador) y respuestas
siempre en JSON. Reutiliza los mismos modelos y reglas de negocio que
el sitio web (inscripciones, cupones, descuento EMI, certificados...).
"""
