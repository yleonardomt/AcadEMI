import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/format.dart';
import '../../providers/auth_provider.dart';
import '../../providers/cart_provider.dart';
import '../../providers/shell_nav.dart';
import '../../widgets/app_text_field.dart';
import '../../widgets/common.dart';

/// Pago: datos de facturación, método (QR o tarjeta) y confirmación.
class CheckoutScreen extends StatefulWidget {
  const CheckoutScreen({super.key});

  @override
  State<CheckoutScreen> createState() => _CheckoutScreenState();
}

class _CheckoutScreenState extends State<CheckoutScreen> {
  final _form = GlobalKey<FormState>();
  late final _name = TextEditingController(text: context.read<AuthProvider>().user!.name);
  late final _email = TextEditingController(text: context.read<AuthProvider>().user!.email);
  late final _phone = TextEditingController(text: context.read<AuthProvider>().user!.phone);
  final _address = TextEditingController();
  final _card = TextEditingController();
  final _expiry = TextEditingController();
  final _cvc = TextEditingController();

  String _method = 'qr';
  bool _loading = false;
  Map<String, dynamic>? _done;

  @override
  void dispose() {
    for (final c in [_name, _email, _phone, _address, _card, _expiry, _cvc]) {
      c.dispose();
    }
    super.dispose();
  }

  bool _luhn(String number) {
    var sum = 0;
    var alt = false;
    for (var i = number.length - 1; i >= 0; i--) {
      var n = int.parse(number[i]);
      if (alt) {
        n *= 2;
        if (n > 9) n -= 9;
      }
      sum += n;
      alt = !alt;
    }
    return sum % 10 == 0;
  }

  Future<void> _pay() async {
    if (!_form.currentState!.validate()) return;
    final cart = context.read<CartProvider>();
    setState(() => _loading = true);
    try {
      final digits = _card.text.replaceAll(' ', '');
      final result = await context.read<AuthProvider>().api.checkout({
        'full_name': _name.text.trim(),
        'email': _email.text.trim(),
        'phone': _phone.text.trim(),
        'address': _address.text.trim(),
        'payment_method': _method,
        'coupon_code': cart.data.couponCode,
        // El número completo de la tarjeta nunca sale del teléfono.
        if (_method == 'card') 'card_last_four': digits.substring(digits.length - 4),
      });
      cart.clear();
      if (mounted) setState(() => _done = result);
    } catch (e) {
      if (mounted) showToast(context, errorText(e), error: true);
    }
    if (mounted) setState(() => _loading = false);
  }

  @override
  Widget build(BuildContext context) {
    if (_done != null) return _Success(result: _done!);
    final cart = context.watch<CartProvider>().data;
    final p = context.palette;

    return Scaffold(
      appBar: AppBar(title: const Text('Finalizar compra')),
      bottomNavigationBar: Container(
        padding: EdgeInsets.fromLTRB(20, 12, 20, MediaQuery.of(context).padding.bottom + 12),
        decoration: BoxDecoration(color: p.surface, border: Border(top: BorderSide(color: p.border))),
        child: Row(children: [
          Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Total a pagar', style: TextStyle(color: p.inkMuted, fontSize: 12)),
            Text(cart.total == 0 ? 'Gratis' : Fmt.amount(cart.total), style: const TextStyle(fontSize: 21, fontWeight: FontWeight.w800)),
          ]),
          const SizedBox(width: 20),
          Expanded(child: LoadingButton(label: 'Confirmar pago', icon: FontAwesomeIcons.lock, accent: true, loading: _loading, onPressed: _pay)),
        ]),
      ),
      body: GestureDetector(
        onTap: () => FocusScope.of(context).unfocus(),
        child: Form(
          key: _form,
          child: ListView(padding: const EdgeInsets.all(16), children: [
            FormCard(
              title: 'Resumen',
              icon: FontAwesomeIcons.receipt,
              child: Column(children: [
                for (final i in cart.items)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Row(children: [
                      Expanded(child: Text(i.title, maxLines: 1, overflow: TextOverflow.ellipsis)),
                      const SizedBox(width: 10),
                      Text(i.isFree ? 'Gratis' : Fmt.amount(i.price), style: const TextStyle(fontWeight: FontWeight.w700)),
                    ]),
                  ),
                if (cart.discount > 0)
                  Row(children: [
                    Expanded(child: Text(cart.discountLabel ?? 'Descuento', style: const TextStyle(color: AppColors.success, fontWeight: FontWeight.w600))),
                    Text('- ${Fmt.amount(cart.discount)}', style: const TextStyle(color: AppColors.success, fontWeight: FontWeight.w800)),
                  ]),
              ]),
            ),
            const SizedBox(height: 14),
            FormCard(
              title: 'Datos de facturación',
              icon: FontAwesomeIcons.fileInvoice,
              child: Column(children: [
                AppTextField(
                  controller: _name,
                  label: 'Nombre completo',
                  icon: FontAwesomeIcons.user,
                  textInputAction: TextInputAction.next,
                  validator: (v) => (v ?? '').trim().isEmpty ? 'El nombre completo es obligatorio' : null,
                ),
                const SizedBox(height: 14),
                AppTextField(
                  controller: _email,
                  label: 'Correo electrónico',
                  icon: FontAwesomeIcons.envelope,
                  keyboardType: TextInputType.emailAddress,
                  textInputAction: TextInputAction.next,
                  validator: (v) => RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch((v ?? '').trim()) ? null : 'Ingresa un correo válido',
                ),
                const SizedBox(height: 14),
                AppTextField(controller: _phone, label: 'Teléfono (opcional)', icon: FontAwesomeIcons.phone, keyboardType: TextInputType.phone, textInputAction: TextInputAction.next),
                const SizedBox(height: 14),
                AppTextField(controller: _address, label: 'Dirección (opcional)', icon: FontAwesomeIcons.locationDot, textInputAction: TextInputAction.done),
              ]),
            ),
            const SizedBox(height: 14),
            FormCard(
              title: 'Método de pago',
              icon: FontAwesomeIcons.wallet,
              child: Column(children: [
                Row(children: [
                  Expanded(child: _methodTile('qr', 'Pago QR', FontAwesomeIcons.qrcode)),
                  const SizedBox(width: 12),
                  Expanded(child: _methodTile('card', 'Tarjeta', FontAwesomeIcons.creditCard)),
                ]),
                const SizedBox(height: 16),
                if (_method == 'qr')
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(color: p.surfaceSoft, borderRadius: BorderRadius.circular(14)),
                    child: Row(children: [
                      const FaIcon(FontAwesomeIcons.qrcode, size: 34, color: AppColors.primaryLight),
                      const SizedBox(width: 14),
                      Expanded(child: Text('Confirma el pago para registrar tu compra e inscribirte de inmediato.', style: TextStyle(color: p.inkMuted, height: 1.45))),
                    ]),
                  )
                else
                  Column(children: [
                    AppTextField(
                      controller: _card,
                      label: 'Número de tarjeta',
                      icon: FontAwesomeIcons.creditCard,
                      hint: '0000 0000 0000 0000',
                      keyboardType: TextInputType.number,
                      inputFormatters: [FilteringTextInputFormatter.digitsOnly, LengthLimitingTextInputFormatter(16), _GroupFormatter()],
                      validator: (v) {
                        final d = (v ?? '').replaceAll(' ', '');
                        if (d.length != 16 || !_luhn(d)) return 'Número de tarjeta inválido';
                        return null;
                      },
                    ),
                    const SizedBox(height: 14),
                    Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Expanded(
                        child: AppTextField(
                          controller: _expiry,
                          label: 'Vencimiento',
                          hint: 'MM/AA',
                          keyboardType: TextInputType.number,
                          inputFormatters: [FilteringTextInputFormatter.digitsOnly, LengthLimitingTextInputFormatter(4), _ExpiryFormatter()],
                          validator: (v) {
                            if ((v ?? '').length != 5) return 'Fecha inválida';
                            final month = int.tryParse(v!.substring(0, 2)) ?? 0;
                            return month >= 1 && month <= 12 ? null : 'Mes inválido';
                          },
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: AppTextField(
                          controller: _cvc,
                          label: 'CVC',
                          hint: '123',
                          obscure: true,
                          keyboardType: TextInputType.number,
                          inputFormatters: [FilteringTextInputFormatter.digitsOnly, LengthLimitingTextInputFormatter(4)],
                          validator: (v) => (v ?? '').length < 3 ? 'CVC inválido' : null,
                        ),
                      ),
                    ]),
                    const SizedBox(height: 10),
                    Row(children: [
                      FaIcon(FontAwesomeIcons.shieldHalved, size: 13, color: p.inkMuted),
                      const SizedBox(width: 8),
                      Expanded(child: Text('Solo se envían los últimos 4 dígitos al servidor.', style: TextStyle(color: p.inkMuted, fontSize: 12))),
                    ]),
                  ]),
              ]),
            ),
            const SizedBox(height: 24),
          ]),
        ),
      ),
    );
  }

  Widget _methodTile(String value, String label, FaIconData icon) {
    final p = context.palette;
    final selected = _method == value;
    return InkWell(
      borderRadius: BorderRadius.circular(14),
      onTap: () => setState(() => _method = value),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 16),
        decoration: BoxDecoration(
          color: selected ? AppColors.primaryLight.withValues(alpha: p.isDark ? 0.28 : 0.10) : Colors.transparent,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: selected ? p.primaryText : p.border, width: selected ? 2 : 1),
        ),
        child: Column(children: [
          FaIcon(icon, size: 24, color: selected ? p.primaryText : p.inkMuted),
          const SizedBox(height: 8),
          Text(label, style: TextStyle(fontWeight: FontWeight.w800, color: selected ? p.primaryText : null)),
        ]),
      ),
    );
  }
}

class _GroupFormatter extends TextInputFormatter {
  @override
  TextEditingValue formatEditUpdate(TextEditingValue oldValue, TextEditingValue newValue) {
    final digits = newValue.text.replaceAll(' ', '');
    final out = StringBuffer();
    for (var i = 0; i < digits.length; i++) {
      if (i > 0 && i % 4 == 0) out.write(' ');
      out.write(digits[i]);
    }
    final text = out.toString();
    return TextEditingValue(text: text, selection: TextSelection.collapsed(offset: text.length));
  }
}

class _ExpiryFormatter extends TextInputFormatter {
  @override
  TextEditingValue formatEditUpdate(TextEditingValue oldValue, TextEditingValue newValue) {
    final digits = newValue.text.replaceAll('/', '');
    final text = digits.length > 2 ? '${digits.substring(0, 2)}/${digits.substring(2)}' : digits;
    return TextEditingValue(text: text, selection: TextSelection.collapsed(offset: text.length));
  }
}

class _Success extends StatelessWidget {
  const _Success({required this.result});

  final Map<String, dynamic> result;

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    final courses = (result['courses'] as List?)?.cast<String>() ?? [];
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
            Container(
              width: 112,
              height: 112,
              decoration: BoxDecoration(color: AppColors.success.withValues(alpha: 0.14), shape: BoxShape.circle),
              child: const Center(child: FaIcon(FontAwesomeIcons.circleCheck, size: 52, color: AppColors.success)),
            ),
            const SizedBox(height: 22),
            const Text('¡Compra exitosa!', style: TextStyle(fontSize: 26, fontWeight: FontWeight.w800, letterSpacing: -0.5)),
            const SizedBox(height: 8),
            Text('${result['message'] ?? ''}', textAlign: TextAlign.center, style: TextStyle(color: p.inkMuted, height: 1.5)),
            const SizedBox(height: 22),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(color: p.surface, borderRadius: BorderRadius.circular(16), border: Border.all(color: p.border), boxShadow: p.shadow),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Row(children: [
                  Text('Factura', style: TextStyle(color: p.inkMuted)),
                  const Spacer(),
                  Text('${result['invoice_number'] ?? ''}', style: const TextStyle(fontWeight: FontWeight.w800)),
                ]),
                const SizedBox(height: 8),
                Row(children: [
                  Text('Total pagado', style: TextStyle(color: p.inkMuted)),
                  const Spacer(),
                  Text(Fmt.amount((result['total'] as num?) ?? 0), style: const TextStyle(fontWeight: FontWeight.w800)),
                ]),
                const Divider(height: 24),
                for (final c in courses)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 6),
                    child: Row(children: [
                      const FaIcon(FontAwesomeIcons.check, size: 13, color: AppColors.success),
                      const SizedBox(width: 10),
                      Expanded(child: Text(c, style: const TextStyle(fontWeight: FontWeight.w600))),
                    ]),
                  ),
              ]),
            ),
            const Spacer(),
            LoadingButton(
              label: 'Ir a mis cursos',
              icon: FontAwesomeIcons.bookOpenReader,
              accent: true,
              onPressed: () {
                Navigator.of(context).popUntil((r) => r.isFirst);
                context.read<ShellNav>().setTab(2);
              },
            ),
          ]),
        ),
      ),
    );
  }
}
