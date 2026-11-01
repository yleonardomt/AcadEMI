import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/format.dart';
import '../../providers/auth_provider.dart';
import '../../providers/cart_provider.dart';
import '../../providers/shell_nav.dart';
import '../../widgets/app_text_field.dart';
import '../../widgets/common.dart';

/// Inscripción gratuita y compras de demostración cuando el servidor lo permite.
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
  bool _loading = false;
  Map<String, dynamic>? _done;

  @override
  void dispose() {
    for (final c in [_name, _email, _phone, _address]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _pay() async {
    if (!_form.currentState!.validate()) return;
    final cart = context.read<CartProvider>();
    if (cart.data.subtotal > 0 && !cart.data.demoMode) {
      showToast(context, 'Las compras de cursos pagos aún no están habilitadas.', error: true);
      return;
    }
    setState(() => _loading = true);
    try {
      final result = await context.read<AuthProvider>().api.checkout({
        'full_name': _name.text.trim(),
        'email': _email.text.trim(),
        'phone': _phone.text.trim(),
        'address': _address.text.trim(),
        'payment_method': cart.data.subtotal > 0 ? 'demo' : 'free',
        'coupon_code': cart.data.couponCode,
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
      appBar: AppBar(title: const Text('Inscripción')),
      bottomNavigationBar: Container(
        padding: EdgeInsets.fromLTRB(20, 12, 20, MediaQuery.of(context).padding.bottom + 12),
        decoration: BoxDecoration(color: p.surface, border: Border(top: BorderSide(color: p.border))),
        child: Row(children: [
          Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Total', style: TextStyle(color: p.inkMuted, fontSize: 12)),
            Text(cart.total == 0 ? 'Gratis' : Fmt.amount(cart.total), style: const TextStyle(fontSize: 21, fontWeight: FontWeight.w800)),
          ]),
          const SizedBox(width: 20),
          Expanded(child: LoadingButton(label: cart.subtotal > 0 && cart.demoMode ? 'Finalizar compra' : 'Inscribirme gratis', icon: FontAwesomeIcons.bookOpen, accent: true, loading: _loading, onPressed: cart.subtotal > 0 && !cart.demoMode ? null : _pay)),
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
            if (cart.subtotal > 0 && !cart.demoMode)
              const Card(child: Padding(
                padding: EdgeInsets.all(16),
                child: Text('Las compras de cursos pagos aún no están habilitadas. Puedes inscribirte en cursos gratuitos.'),
              )),
            const SizedBox(height: 24),
          ]),
        ),
      ),
    );
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
            const Text('¡Inscripción exitosa!', style: TextStyle(fontSize: 26, fontWeight: FontWeight.w800, letterSpacing: -0.5)),
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
                  Text('Total', style: TextStyle(color: p.inkMuted)),
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
