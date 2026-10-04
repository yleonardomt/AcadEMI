import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/format.dart';
import '../../models/social.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/common.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  Key _key = UniqueKey();

  (FaIconData, Color) _style(String type) => switch (type) {
        'course' => (FontAwesomeIcons.bookOpen, AppColors.primaryLight),
        'evaluation' => (FontAwesomeIcons.listCheck, AppColors.purple),
        'purchase' => (FontAwesomeIcons.bagShopping, AppColors.success),
        'certificate' => (FontAwesomeIcons.award, AppColors.secondaryDark),
        'comment' => (FontAwesomeIcons.comment, AppColors.teal),
        'question' => (FontAwesomeIcons.circleQuestion, AppColors.orange),
        'answer' => (FontAwesomeIcons.commentDots, AppColors.info),
        _ => (FontAwesomeIcons.bell, AppColors.primaryLight),
      };

  @override
  Widget build(BuildContext context) {
    final auth = context.read<AuthProvider>();
    final p = context.palette;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Notificaciones'),
        actions: [
          TextButton.icon(
            onPressed: () async {
              try {
                await auth.api.markAllNotificationsRead();
                auth.setUnread(0);
                setState(() => _key = UniqueKey());
              } catch (e) {
                if (mounted) showToast(context, errorText(e), error: true);
              }
            },
            icon: const FaIcon(FontAwesomeIcons.checkDouble, size: 14),
            label: const Text('Marcar todas'),
          ),
        ],
      ),
      body: AsyncBody<(List<AppNotification>, int)>(
        key: _key,
        load: auth.api.notifications,
        builder: (context, data, reload) {
          final (list, unread) = data;
          WidgetsBinding.instance.addPostFrameCallback((_) {
            if (auth.unreadNotifications != unread) auth.setUnread(unread);
          });
          if (list.isEmpty) {
            return ListView(children: [
              SizedBox(
                height: MediaQuery.of(context).size.height * 0.6,
                child: const EmptyState(icon: FontAwesomeIcons.bellSlash, title: 'Sin notificaciones', message: 'Aquí verás avisos de tus cursos, compras y respuestas.'),
              ),
            ]);
          }
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: list.length,
            separatorBuilder: (_, _) => const SizedBox(height: 10),
            itemBuilder: (context, i) {
              final n = list[i];
              final (icon, color) = _style(n.type);
              return InkWell(
                borderRadius: BorderRadius.circular(16),
                onTap: n.isRead
                    ? null
                    : () async {
                        try {
                          await auth.api.markNotificationRead(n.id);
                          await reload();
                        } catch (_) {}
                      },
                child: Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: n.isRead ? p.surface : color.withValues(alpha: p.isDark ? 0.16 : 0.07),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: n.isRead ? p.border : color.withValues(alpha: 0.4)),
                  ),
                  child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Container(
                      width: 42,
                      height: 42,
                      decoration: BoxDecoration(color: color.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(13)),
                      child: Center(child: FaIcon(icon, size: 17, color: color)),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Row(children: [
                          Expanded(child: Text(n.title, style: TextStyle(fontWeight: n.isRead ? FontWeight.w700 : FontWeight.w800))),
                          if (!n.isRead) Container(width: 9, height: 9, decoration: const BoxDecoration(color: AppColors.danger, shape: BoxShape.circle)),
                        ]),
                        const SizedBox(height: 3),
                        Text(n.message, style: TextStyle(color: p.inkMuted, height: 1.4, fontSize: 13.5)),
                        const SizedBox(height: 6),
                        Text(Fmt.ago(n.createdAt), style: TextStyle(color: p.inkMuted, fontSize: 12)),
                      ]),
                    ),
                  ]),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
