import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/format.dart';
import '../../core/utils/nav.dart';
import '../../providers/cart_provider.dart';
import '../../providers/shell_nav.dart';
import '../../widgets/common.dart';
import '../../widgets/course_card.dart';
import '../catalog/course_detail_screen.dart';
import 'checkout_screen.dart';

class CartScreen extends StatefulWidget {
  const CartScreen({super.key});

  @override
  State<CartScreen> createState() => _CartScreenState();
}

class _CartScreenState extends State<CartScreen> {
  final _coupon = TextEditingController();
  bool _applying = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => context.read<CartProvider>().load());
  }

  @override
  void dispose() {
    _coupon.dispose();
    super.dispose();
  }

  Future<void> _apply() async {
    final code = _coupon.text.trim();
    if (code.isEmpty) return;
    setState(() => _applying = true);
    try {
      final (message, applied) = await context.read<CartProvider>().applyCoupon(code);
      if (mounted) showToast(context, message, success: applied);
    } catch (e) {
      if (mounted) showToast(context, errorText(e), error: true);
    }
    if (mounted) setState(() => _applying = false);
  }

  Future<void> _remove(int id) async {
    try {
      await context.read<CartProvider>().remove(id);
    } catch (e) {
      if (mounted) showToast(context, errorText(e), error: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final cart = context.watch<CartProvider>();
    final data = cart.data;
    final p = context.palette;

    return Scaffold(
      appBar: AppBar(title: const Text('Mi carrito')),
      body: cart.loading && data.items.isEmpty
          ? const Center(child: CircularProgressIndicator())
          : data.items.isEmpty
              ? EmptyState(
                  icon: FontAwesomeIcons.cartShopping,
                  title: 'Tu carrito está vacío',
                  message: 'Agrega cursos desde el catálogo para comprarlos.',
                  actionLabel: 'Explorar cursos',
                  onAction: () {
                    Navigator.of(context).popUntil((r) => r.isFirst);
                    context.read<ShellNav>().openCatalog(1);
                  },
                )
              : Column(children: [
                  Expanded(
                    child: RefreshIndicator(
                      onRefresh: cart.load,
                      child: ListView(padding: const EdgeInsets.all(16), children: [
                        for (final item in data.items)
                          Padding(
                            padding: const EdgeInsets.only(bottom: 12),
                            child: Card(
                              clipBehavior: Clip.antiAlias,
                              child: InkWell(
                                onTap: () => push(context, CourseDetailScreen(courseId: item.courseId)),
                                child: Padding(
                                  padding: const EdgeInsets.all(12),
                                  child: Row(children: [
                                    ClipRRect(
                                      borderRadius: BorderRadius.circular(12),
                                      child: SizedBox(width: 82, height: 82, child: CourseImage(url: item.image, category: item.category)),
                                    ),
                                    const SizedBox(width: 12),
                                    Expanded(
                                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                                        Text(item.title, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w800, height: 1.25)),
                                        const SizedBox(height: 3),
                                        Text(item.teacher, style: TextStyle(color: p.inkMuted, fontSize: 12.5)),
                                        const SizedBox(height: 6),
                                        Text(item.isFree ? 'Gratis' : Fmt.amount(item.price),
                                            style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16, color: item.isFree ? AppColors.success : p.primaryText)),
                                      ]),
                                    ),
                                    IconButton(
                                      tooltip: 'Quitar',
                                      onPressed: () => _remove(item.courseId),
                                      icon: const FaIcon(FontAwesomeIcons.trashCan, size: 17, color: AppColors.danger),
                                    ),
                                  ]),
                                ),
                              ),
                            ),
                          ),
                        const SizedBox(height: 4),
                        Text('¿Tienes un cupón?', style: const TextStyle(fontWeight: FontWeight.w800)),
                        const SizedBox(height: 8),
                        Row(children: [
                          Expanded(
                            child: TextField(
                              controller: _coupon,
                              textCapitalization: TextCapitalization.characters,
                              decoration: InputDecoration(
                                hintText: 'Código de cupón',
                                prefixIcon: Padding(padding: const EdgeInsets.all(14), child: FaIcon(FontAwesomeIcons.ticket, size: 16, color: p.inkMuted)),
                                prefixIconConstraints: const BoxConstraints(minWidth: 44),
                              ),
                            ),
                          ),
                          const SizedBox(width: 10),
                          SizedBox(
                            height: 50,
                            child: FilledButton(
                              onPressed: _applying ? null : _apply,
                              style: FilledButton.styleFrom(minimumSize: const Size(96, 50)),
                              child: _applying
                                  ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2.2, color: Colors.white))
                                  : const Text('Aplicar'),
                            ),
                          ),
                        ]),
                        if (data.emiDiscount != null) ...[
                          const SizedBox(height: 14),
                          Container(
                            padding: const EdgeInsets.all(14),
                            decoration: BoxDecoration(color: AppColors.secondary.withValues(alpha: 0.2), borderRadius: BorderRadius.circular(14)),
                            child: Row(children: [
                              const FaIcon(FontAwesomeIcons.percent, size: 16, color: AppColors.secondaryDark),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Text('Tienes ${data.emiDiscount!.toStringAsFixed(0)}% de descuento EMI en esta compra (se aplica automáticamente).',
                                    style: const TextStyle(fontWeight: FontWeight.w600, height: 1.4)),
                              ),
                            ]),
                          ),
                        ],
                      ]),
                    ),
                  ),
                  Container(
                    padding: EdgeInsets.fromLTRB(20, 16, 20, MediaQuery.of(context).padding.bottom + 16),
                    decoration: BoxDecoration(color: p.surface, border: Border(top: BorderSide(color: p.border))),
                    child: Column(mainAxisSize: MainAxisSize.min, children: [
                      _line('Subtotal', Fmt.amount(data.subtotal)),
                      if (data.discount > 0) ...[
                        const SizedBox(height: 6),
                        _line(data.discountLabel ?? 'Descuento', '- ${Fmt.amount(data.discount)}', color: AppColors.success),
                      ],
                      const Divider(height: 22),
                      _line('Total', data.total == 0 ? 'Gratis' : Fmt.amount(data.total), big: true),
                      const SizedBox(height: 14),
                      LoadingButton(
                        label: 'Continuar al pago',
                        icon: FontAwesomeIcons.lock,
                        accent: true,
                        onPressed: () => push(context, const CheckoutScreen()),
                      ),
                    ]),
                  ),
                ]),
    );
  }

  Widget _line(String label, String value, {bool big = false, Color? color}) => Row(children: [
        Expanded(child: Text(label, style: TextStyle(fontSize: big ? 17 : 14.5, fontWeight: big ? FontWeight.w800 : FontWeight.w500))),
        Text(value, style: TextStyle(fontSize: big ? 21 : 14.5, fontWeight: FontWeight.w800, color: color)),
      ]);
}
