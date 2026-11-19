# Checkout académico con tarjeta de débito

El carrito web incluye titular, número, vencimiento MM/AA y CVC de tres dígitos cuando el importe final es mayor que cero y `DEMO_CHECKOUT=True`. La fecha admite el mes actual y meses futuros. Los cursos gratuitos y pedidos con descuento del 100% no requieren tarjeta.

## Tarjetas para la presentación

| Identificador | Número de prueba | Marca |
| --- | --- | --- |
| visa_debit | 4000 0566 5566 5556 | Visa débito |
| mastercard_debit | 5200 8282 8282 8210 | Mastercard débito |

Usar una fecha futura, por ejemplo `12/30`, y CVC `123`. Solo admite los números de prueba indicados. No hay comunicación con bancos ni una pasarela de pagos. Los datos de prueba se documentan aquí; el formulario no muestra el aviso de la presentación.

## Registro y privacidad de los datos

El navegador valida los datos y envía únicamente `payment_method=debit_card` y el identificador público `test_card`, junto con los datos de facturación y el cupón. No envía el número completo, el vencimiento, el titular de la tarjeta ni el CVC. No guarda esos datos en almacenamiento del navegador. Los campos se vacían después de una compra correcta.

El servidor usa metadatos propios para registrar marca y cuatro últimos dígitos en `Payment.payment_details`. La operación mantiene el tipo interno `demo`, conserva las reglas de descuentos, inscripción, estadísticas académicas y exclusión de ingresos reales. Historial web, comprobante HTML/PDF y etiquetas de la API muestran el método de débito y los cuatro últimos dígitos. Con `DEMO_CHECKOUT=False`, una tarjeta de prueba no habilita compras reales.

Los descuentos se redondean a centavos antes de generar el pedido y repartir las líneas: Bs.120,50 con descuento de 25% registra Bs.30,13 de descuento y Bs.90,37 de total. El importe del carrito coincide con el comprobante.

## Verificación

El 18 de noviembre de 2026 pasaron 98 pruebas Django, incluidas nueve del checkout con tarjeta: compra e inscripción, metadatos sin número completo/CVC, tarjeta desconocida, método ausente, Mastercard, correo inválido, pedido gratuito, repetición del envío, funcionamiento sin modo académico, JSON inválido y redondeo de descuentos.

En Chromium, nueve comprobaciones del recorrido completo confirmaron formato del número, rechazo de tarjetas ajenas a la presentación, vencimiento, mes inválido, CVC incompleto, compra con cupón sin envío de datos completos de tarjeta, acceso al curso, historial/comprobante y pedidos gratuitos o con descuento del 100%. Diez combinaciones de ancho (320/390/768/1024/1440 px) y tema claro/oscuro no mostraron desbordamiento horizontal ni fallos de contraste en los controles analizados. Estas compras se realizaron en SQLite aislado, sin añadir operaciones a Neon.

La integración de un cobro real sigue pendiente de una pasarela. Los formularios de tarjeta de la aplicación móvil no forman parte de este cambio del carrito web; la API móvil conserva su flujo de compra actual.
