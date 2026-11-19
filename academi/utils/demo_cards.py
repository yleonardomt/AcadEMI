"""Tarjetas de prueba del checkout académico; no se conectan a una pasarela."""

import re

DEMO_CARDS = {
    'visa_debit': {'number': '4000056655665556', 'brand': 'Visa', 'last4': '5556'},
    'mastercard_debit': {'number': '5200828282828210', 'brand': 'Mastercard', 'last4': '8210'},
}


def card_payment_details(test_card, last_four=None):
    if test_card == 'debit_card':
        if not isinstance(last_four, str) or not re.fullmatch(r'[0-9]{4}', last_four):
            return None
        return {'mode': 'demo', 'method': 'debit_card', 'card_last_four': last_four}
    # Compatibilidad con formularios abiertos antes de actualizar el checkout.
    card = DEMO_CARDS.get(test_card) if isinstance(test_card, str) else None
    if not card:
        return None
    return {'mode': 'demo', 'method': 'debit_card', 'card_brand': card['brand'],
            'card_last_four': card['last4']}
