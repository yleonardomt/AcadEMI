import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../core/theme/app_colors.dart';
import '../core/utils/nav.dart';
import '../providers/auth_provider.dart';
import '../providers/cart_provider.dart';
import '../screens/commerce/cart_screen.dart';
import '../screens/profile/notifications_screen.dart';

/// Ícono con insignia numérica.
class BadgeIcon extends StatelessWidget {
  const BadgeIcon({super.key, required this.icon, required this.count, this.color, this.size = 20});

  final FaIconData icon;
  final int count;
  final Color? color;
  final double size;

  @override
  Widget build(BuildContext context) => Stack(clipBehavior: Clip.none, children: [
        FaIcon(icon, size: size, color: color),
        if (count > 0)
          Positioned(
            right: -8,
            top: -7,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
              constraints: const BoxConstraints(minWidth: 17),
              decoration: BoxDecoration(color: AppColors.danger, borderRadius: BorderRadius.circular(9)),
              child: Text(count > 9 ? '9+' : '$count',
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.w800)),
            ),
          ),
      ]);
}

/// Campana de notificaciones y carrito (solo estudiantes) para las barras superiores.
class HeaderActions extends StatelessWidget {
  const HeaderActions({super.key, this.color});

  final Color? color;

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final cart = context.watch<CartProvider>();
    return Row(mainAxisSize: MainAxisSize.min, children: [
      IconButton(
        tooltip: 'Notificaciones',
        onPressed: () => push(context, const NotificationsScreen()),
        icon: BadgeIcon(icon: FontAwesomeIcons.bell, count: auth.unreadNotifications, color: color),
      ),
      if (auth.user?.isStudent ?? false)
        IconButton(
          tooltip: 'Carrito',
          onPressed: () => push(context, const CartScreen()),
          icon: BadgeIcon(icon: FontAwesomeIcons.cartShopping, count: cart.count, color: color),
        ),
      const SizedBox(width: 4),
    ]);
  }
}
