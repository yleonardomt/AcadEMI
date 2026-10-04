import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/format.dart';
import '../../core/utils/nav.dart';
import '../../models/commerce.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/common.dart';

class PurchasesScreen extends StatelessWidget {
  const PurchasesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final api = context.read<AuthProvider>().api;
    final p = context.palette;
    return Scaffold(
      appBar: AppBar(title: const Text('Historial de compras')),
      body: AsyncBody<(List<PaymentSummary>, double)>(
        load: api.purchases,
        builder: (context, data, reload) {
          final (payments, total) = data;
          if (payments.isEmpty) {
            return ListView(children: [
              SizedBox(
                height: MediaQuery.of(context).size.height * 0.6,
                child: const EmptyState(icon: FontAwesomeIcons.receipt, title: 'Sin compras todavía', message: 'Cuando compres un curso, tu comprobante aparecerá aquí.'),
              ),
            ]);
          }
          return ListView(padding: const EdgeInsets.all(16), children: [
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(gradient: AppColors.heroGradient, borderRadius: BorderRadius.circular(20)),
              child: Row(children: [
                Expanded(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text('Total invertido', style: TextStyle(color: Colors.white.withValues(alpha: 0.8))),
                    const SizedBox(height: 4),
                    Text(Fmt.amount(total), style: const TextStyle(color: Colors.white, fontSize: 28, fontWeight: FontWeight.w800)),
                  ]),
                ),
                Column(children: [
                  Text('${payments.length}', style: const TextStyle(color: AppColors.secondary, fontSize: 26, fontWeight: FontWeight.w800)),
                  Text('compras', style: TextStyle(color: Colors.white.withValues(alpha: 0.8), fontSize: 12)),
                ]),
              ]),
            ),
            const SizedBox(height: 16),
            for (final pay in payments)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Card(
                  child: ListTile(
                    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                    onTap: () => push(context, InvoiceScreen(paymentId: pay.id)),
                    leading: Container(
                      width: 46,
                      height: 46,
                      decoration: BoxDecoration(color: AppColors.primaryLight.withValues(alpha: 0.14), borderRadius: BorderRadius.circular(14)),
                      child: Center(child: FaIcon(pay.method == 'card' ? FontAwesomeIcons.creditCard : FontAwesomeIcons.qrcode, size: 19, color: p.primaryText)),
                    ),
                    title: Text(pay.invoiceNumber ?? 'Compra #${pay.id}', style: const TextStyle(fontWeight: FontWeight.w800)),
                    subtitle: Text('${Fmt.date(pay.createdAt)} · ${pay.coursesCount} ${pay.coursesCount == 1 ? 'curso' : 'cursos'}', style: TextStyle(color: p.inkMuted, fontSize: 12.5)),
                    trailing: Column(mainAxisAlignment: MainAxisAlignment.center, crossAxisAlignment: CrossAxisAlignment.end, children: [
                      Text(Fmt.amount(pay.total), style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
                      const SizedBox(height: 4),
                      SoftTag(label: pay.statusLabel, color: pay.status == 'completed' ? AppColors.success : AppColors.warning),
                    ]),
                  ),
                ),
              ),
          ]);
        },
      ),
    );
  }
}

class InvoiceScreen extends StatelessWidget {
  const InvoiceScreen({super.key, required this.paymentId});

  final int paymentId;

  @override
  Widget build(BuildContext context) {
    final api = context.read<AuthProvider>().api;
    final p = context.palette;
    return Scaffold(
      appBar: AppBar(title: const Text('Factura')),
      body: AsyncBody<PaymentSummary>(
        load: () => api.purchaseDetail(paymentId),
        builder: (context, pay, _) => ListView(padding: const EdgeInsets.all(16), children: [
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(color: p.surface, borderRadius: BorderRadius.circular(20), border: Border.all(color: p.border), boxShadow: p.shadow),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                const BrandLogo(),
                const Spacer(),
                SoftTag(label: pay.statusLabel, color: pay.status == 'completed' ? AppColors.success : AppColors.warning),
              ]),
              const SizedBox(height: 18),
              Text(pay.invoiceNumber ?? 'Compra #${pay.id}', style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),
              const SizedBox(height: 4),
              Text(Fmt.dateTime(pay.createdAt), style: TextStyle(color: p.inkMuted)),
              const Divider(height: 30),
              _kv('Facturado a', pay.billingName),
              _kv('Correo', pay.billingEmail),
              if (pay.billingPhone.isNotEmpty) _kv('Teléfono', pay.billingPhone),
              if (pay.billingAddress.isNotEmpty) _kv('Dirección', pay.billingAddress),
              _kv('Método de pago', pay.methodLabel + (pay.cardLastFour != null ? ' ····${pay.cardLastFour}' : '')),
              if (pay.transactionId != null) _kv('Transacción', pay.transactionId!),
              const Divider(height: 30),
              const Text('Detalle', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
              const SizedBox(height: 12),
              for (final i in pay.items)
                Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: Row(children: [
                    Expanded(child: Text(i.title, style: const TextStyle(fontWeight: FontWeight.w600))),
                    const SizedBox(width: 12),
                    Text(i.price == 0 ? 'Gratis' : Fmt.amount(i.price), style: const TextStyle(fontWeight: FontWeight.w700)),
                  ]),
                ),
              const Divider(height: 26),
              _kv('Subtotal', Fmt.amount(pay.amount)),
              if (pay.discount > 0) _kv(pay.notes.isNotEmpty ? pay.notes : 'Descuento', '- ${Fmt.amount(pay.discount)}', color: AppColors.success),
              const SizedBox(height: 6),
              Row(children: [
                const Text('Total', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800)),
                const Spacer(),
                Text(Fmt.amount(pay.total), style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800)),
              ]),
            ]),
          ),
          if (pay.pdfUrl != null) ...[
            const SizedBox(height: 16),
            LoadingButton(
              label: 'Descargar comprobante PDF',
              icon: FontAwesomeIcons.filePdf,
              accent: true,
              onPressed: () => launchUrl(Uri.parse(pay.pdfUrl!), mode: LaunchMode.externalApplication),
            ),
          ],
        ]),
      ),
    );
  }

  Widget _kv(String k, String v, {Color? color}) => Padding(
        padding: const EdgeInsets.only(bottom: 8),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          SizedBox(width: 120, child: Text(k, style: const TextStyle(color: Color(0xFF718096)))),
          Expanded(child: Text(v, textAlign: TextAlign.right, style: TextStyle(fontWeight: FontWeight.w700, color: color))),
        ]),
      );
}
