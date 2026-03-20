import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../services/i18n_service.dart';

/// Visual 4×4 grid with merged cells (colspan/rowspan) matching the reference.
/// Data model stays 4 rows × 3 cols (body_composition.dart).
class BodyTypeGrid extends StatelessWidget {
  final int activeRow; // data row 0-3
  final int activeCol; // data col 0-2
  final String bodyTypeKey;
  final double fatLow;
  final double fatHigh;

  const BodyTypeGrid({
    super.key,
    required this.activeRow,
    required this.activeCol,
    required this.bodyTypeKey,
    required this.fatLow,
    required this.fatHigh,
  });

  static const _cellH = 56.0;
  static const _cols = 4;
  static const _rows = 4;
  static const _r = Radius.circular(10);

  // (vRow, vCol, rowSpan, colSpan, i18nKey, dataRow, dataCol)
  static const _cells = [
    (0, 0, 1, 2, 'athlete_body', 0, 0),
    (0, 2, 1, 1, 'muscular_obesity', 0, 1),
    (0, 3, 1, 1, 'obesity', 0, 2),
    (1, 0, 1, 2, 'muscular', 1, 0),
    (1, 2, 2, 1, 'healthy', 1, 1),
    (1, 3, 1, 1, 'slightly_overweight', 1, 2),
    (2, 0, 1, 1, 'lean_muscular', 2, 0),
    (2, 1, 1, 1, 'lean', 2, 1),
    (2, 3, 2, 1, 'hidden_obesity', 2, 2),
    (3, 0, 1, 1, 'skeletal_lean', 3, 0),
    (3, 1, 1, 2, 'slightly_underweight', 3, 1),
  ];

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // BMI Y-axis
            SizedBox(
              width: 28,
              height: _cellH * _rows,
              child: Column(
                children: [
                  const SizedBox(height: _cellH - 7),
                  _label('24,9'),
                  const SizedBox(height: _cellH * 2 - 7),
                  _label('18,5'),
                ],
              ),
            ),
            // Grid
            Expanded(
              child: LayoutBuilder(
                builder: (context, constraints) {
                  final colW = constraints.maxWidth / _cols;
                  return SizedBox(
                    height: _cellH * _rows,
                    child: Stack(
                      children: [
                        // Outer rounded border
                        Positioned.fill(
                          child: Container(
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.all(_r),
                              border: Border.all(color: AppColors.borderLight),
                            ),
                          ),
                        ),
                        // Cells
                        for (final c in _cells)
                          _posCell(c, colW),
                      ],
                    ),
                  );
                },
              ),
            ),
          ],
        ),

        const SizedBox(height: 6),

        // Bottom X-axis
        Row(
          children: [
            const SizedBox(
              width: 28,
              child: Text('BMI',
                  style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                      color: AppColors.textMuted)),
            ),
            Expanded(
              child: LayoutBuilder(
                builder: (context, constraints) {
                  final colW = constraints.maxWidth / _cols;
                  return SizedBox(
                    height: 16,
                    child: Stack(
                      children: [
                        Positioned(
                          left: 4,
                          top: 0,
                          child: _axisText('Gordura', bold: true),
                        ),
                        Positioned(
                          left: colW * 1 - 8,
                          top: 0,
                          child: _axisText('${fatLow.toStringAsFixed(0)}%'),
                        ),
                        Positioned(
                          left: colW * 3 - 8,
                          top: 0,
                          child: _axisText('${fatHigh.toStringAsFixed(0)}%'),
                        ),
                      ],
                    ),
                  );
                },
              ),
            ),
          ],
        ),

        const SizedBox(height: 16),

        Text(
          I18nService.t('body_type.$bodyTypeKey'),
          style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: AppColors.textPrimary),
        ),
        const SizedBox(height: 6),
        Text(
          I18nService.t('body_type_desc.$bodyTypeKey'),
          style: const TextStyle(
              fontSize: 13, color: AppColors.textSecondary, height: 1.5),
        ),
      ],
    );
  }

  Widget _posCell(
    (int, int, int, int, String, int, int) cell,
    double colW,
  ) {
    final (vRow, vCol, rSpan, cSpan, key, dRow, dCol) = cell;
    final active = dRow == activeRow && dCol == activeCol;

    final left = vCol * colW;
    final top = vRow * _cellH;
    final w = cSpan * colW;
    final h = rSpan * _cellH;

    // Corner radius for cells at grid edges
    final tl = (vRow == 0 && vCol == 0) ? _r : Radius.zero;
    final tr = (vRow == 0 && vCol + cSpan == _cols) ? _r : Radius.zero;
    final bl = (vRow + rSpan == _rows && vCol == 0) ? _r : Radius.zero;
    final br = (vRow + rSpan == _rows && vCol + cSpan == _cols) ? _r : Radius.zero;

    return Positioned(
      left: left,
      top: top,
      width: w,
      height: h,
      child: Container(
        decoration: BoxDecoration(
          color: active ? AppColors.redLight : Colors.transparent,
          borderRadius: active
              ? BorderRadius.circular(8)
              : BorderRadius.only(
                  topLeft: tl, topRight: tr, bottomLeft: bl, bottomRight: br),
          border: active
              ? Border.all(color: AppColors.red, width: 2)
              : Border(
                  right: (vCol + cSpan) < _cols
                      ? BorderSide(color: AppColors.borderLight)
                      : BorderSide.none,
                  bottom: (vRow + rSpan) < _rows
                      ? BorderSide(color: AppColors.borderLight)
                      : BorderSide.none,
                ),
        ),
        child: Center(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 4),
            child: Text(
              I18nService.t('body_type.$key'),
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: active ? 12 : 11,
                fontWeight: active ? FontWeight.w700 : FontWeight.w500,
                color: active ? AppColors.red : AppColors.textPrimary,
                height: 1.3,
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _label(String text) => Text(
        text,
        style: const TextStyle(
            fontSize: 10,
            fontWeight: FontWeight.w500,
            color: AppColors.textMuted),
      );

  Widget _axisText(String text, {bool bold = false}) => Text(
        text,
        style: TextStyle(
            fontSize: 10,
            fontWeight: bold ? FontWeight.w600 : FontWeight.w500,
            color: AppColors.textMuted),
      );
}
