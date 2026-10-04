import 'package:chewie/chewie.dart';
import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:video_player/video_player.dart';
import 'package:youtube_player_iframe/youtube_player_iframe.dart';

import '../../core/theme/app_colors.dart';

/// Reproductor de YouTube incrustado.
class YoutubeLesson extends StatefulWidget {
  const YoutubeLesson({super.key, required this.videoId});

  final String videoId;

  @override
  State<YoutubeLesson> createState() => _YoutubeLessonState();
}

class _YoutubeLessonState extends State<YoutubeLesson> {
  late final YoutubePlayerController _controller = YoutubePlayerController.fromVideoId(
    videoId: widget.videoId,
    autoPlay: false,
    params: const YoutubePlayerParams(showFullscreenButton: true, strictRelatedVideos: true),
  );

  @override
  void dispose() {
    _controller.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => ClipRRect(
        borderRadius: BorderRadius.circular(16),
        child: YoutubePlayer(controller: _controller, aspectRatio: 16 / 9),
      );
}

/// Reproductor de un archivo de video subido a AcadEMI.
class FileVideoLesson extends StatefulWidget {
  const FileVideoLesson({super.key, required this.url});

  final String url;

  @override
  State<FileVideoLesson> createState() => _FileVideoLessonState();
}

class _FileVideoLessonState extends State<FileVideoLesson> {
  VideoPlayerController? _video;
  ChewieController? _chewie;
  bool _failed = false;

  @override
  void initState() {
    super.initState();
    _init();
  }

  Future<void> _init() async {
    try {
      final video = VideoPlayerController.networkUrl(Uri.parse(widget.url));
      await video.initialize();
      if (!mounted) {
        await video.dispose();
        return;
      }
      setState(() {
        _video = video;
        _chewie = ChewieController(
          videoPlayerController: video,
          aspectRatio: video.value.aspectRatio,
          allowFullScreen: true,
          materialProgressColors: ChewieProgressColors(
            playedColor: AppColors.secondary,
            handleColor: AppColors.secondary,
            bufferedColor: Colors.white38,
            backgroundColor: Colors.white24,
          ),
        );
      });
    } catch (_) {
      if (mounted) setState(() => _failed = true);
    }
  }

  @override
  void dispose() {
    _chewie?.dispose();
    _video?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_failed) {
      return _MediaPlaceholder(
        icon: FontAwesomeIcons.triangleExclamation,
        text: 'No se pudo reproducir el video.',
        actionLabel: 'Abrir en el navegador',
        onAction: () => launchUrl(Uri.parse(widget.url), mode: LaunchMode.externalApplication),
      );
    }
    if (_chewie == null) {
      return const AspectRatio(aspectRatio: 16 / 9, child: Center(child: CircularProgressIndicator()));
    }
    return ClipRRect(
      borderRadius: BorderRadius.circular(16),
      child: AspectRatio(aspectRatio: _video!.value.aspectRatio, child: Chewie(controller: _chewie!)),
    );
  }
}

/// Video con un enlace externo que no es de YouTube.
class ExternalVideoLesson extends StatelessWidget {
  const ExternalVideoLesson({super.key, required this.url});

  final String url;

  @override
  Widget build(BuildContext context) => _MediaPlaceholder(
        icon: FontAwesomeIcons.circlePlay,
        text: 'Este video se ve en una página externa.',
        actionLabel: 'Abrir video',
        onAction: () => launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication),
      );
}

class _MediaPlaceholder extends StatelessWidget {
  const _MediaPlaceholder({required this.icon, required this.text, required this.actionLabel, required this.onAction});

  final FaIconData icon;
  final String text, actionLabel;
  final VoidCallback onAction;

  @override
  Widget build(BuildContext context) {
    return AspectRatio(
      aspectRatio: 16 / 9,
      child: Container(
        decoration: BoxDecoration(gradient: AppColors.heroGradient, borderRadius: BorderRadius.circular(16)),
        child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
          FaIcon(icon, size: 34, color: AppColors.secondary),
          const SizedBox(height: 10),
          Text(text, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
          const SizedBox(height: 12),
          FilledButton(
            style: FilledButton.styleFrom(minimumSize: const Size(0, 42), backgroundColor: AppColors.secondary, foregroundColor: AppColors.primaryDark),
            onPressed: onAction,
            child: Text(actionLabel),
          ),
        ]),
      ),
    );
  }
}

/// Tarjeta para abrir/descargar un documento o recurso.
class FileTile extends StatelessWidget {
  const FileTile({super.key, required this.title, required this.url, this.subtitle, this.icon = FontAwesomeIcons.fileLines});

  final String title;
  final String? url, subtitle;
  final FaIconData icon;

  @override
  Widget build(BuildContext context) {
    final p = context.palette;
    return Card(
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        leading: Container(
          width: 44,
          height: 44,
          decoration: BoxDecoration(color: AppColors.orange.withValues(alpha: 0.14), borderRadius: BorderRadius.circular(12)),
          child: Center(child: FaIcon(icon, size: 19, color: AppColors.orange)),
        ),
        title: Text(title, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w700)),
        subtitle: subtitle == null ? null : Text(subtitle!, style: TextStyle(color: p.inkMuted, fontSize: 12.5)),
        trailing: FaIcon(FontAwesomeIcons.download, size: 16, color: p.primaryText),
        onTap: url == null ? null : () => launchUrl(Uri.parse(url!), mode: LaunchMode.externalApplication),
      ),
    );
  }
}
