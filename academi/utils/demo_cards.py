"""Tarjetas de prueba del checkout académico; no se conectan a una pasarela."""

DEMO_CARDS = {
    'visa_debit': {'number': '4000056655665556', 'brand': 'Visa', 'last4': '5556'},
    'mastercard_debit': {'number': '5200828282828210', 'brand': 'Mastercard', 'last4': '8210'},
}


def card_payment_details(test_card):
    card = DEMO_CARDS.get(test_card) if isinstance(test_card, str) else None
    if not card:
        return None
    return {'mode': 'demo', 'method': 'debit_card', 'card_brand': card['brand'],
            'card_last_four': card['last4']}
