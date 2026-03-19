import 'package:flutter/material.dart';

/// A widget that displays a human body silhouette image with a
/// water-level fill indicator from bottom to top based on [waterPercent].
///
/// Uses pre-rendered PNG silhouettes for male ('M') and female ('F').
class BodySilhouette extends StatelessWidget {
  const BodySilhouette({
    super.key,
    required this.waterPercent,
    this.sex = 'M',
  });

  /// Water percentage (0-100) controlling how high the fill reaches.
  final double waterPercent;

  /// 'M' for male silhouette, 'F' for female silhouette.
  final String sex;

  static const _fillColor = Color(0xFF4A90D9);

  @override
  Widget build(BuildContext context) {
    final assetPath = sex == 'F'
        ? 'assets/images/silhouette_mulher.png'
        : 'assets/images/silhouette_homem.png';

    return LayoutBuilder(
      builder: (context, constraints) {
        return Stack(
          children: [
            // Base silhouette image (full, original colors)
            Positioned.fill(
              child: Image.asset(
                assetPath,
                fit: BoxFit.contain,
              ),
            ),
            // Water fill overlay (clipped from bottom based on waterPercent)
            Positioned.fill(
              child: ClipRect(
                clipper: _WaterLevelClipper(
                  fillFraction: (waterPercent / 100.0).clamp(0.0, 1.0),
                ),
                child: ColorFiltered(
                  colorFilter: ColorFilter.mode(
                    _fillColor.withValues(alpha: 0.35),
                    BlendMode.srcATop,
                  ),
                  child: Image.asset(
                    assetPath,
                    fit: BoxFit.contain,
                  ),
                ),
              ),
            ),
          ],
        );
      },
    );
  }
}

/// Clips from the bottom up to [fillFraction] of the total height.
class _WaterLevelClipper extends CustomClipper<Rect> {
  _WaterLevelClipper({required this.fillFraction});

  final double fillFraction;

  @override
  Rect getClip(Size size) {
    final top = size.height * (1.0 - fillFraction);
    return Rect.fromLTRB(0, top, size.width, size.height);
  }

  @override
  bool shouldReclip(covariant _WaterLevelClipper oldClipper) {
    return oldClipper.fillFraction != fillFraction;
  }
}
