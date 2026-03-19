import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../services/i18n_service.dart';

class BmiBar extends StatelessWidget {
  final double bmi;

  const BmiBar({super.key, required this.bmi});

  double _position() {
    if (bmi < 15) return 0;
    if (bmi > 40) return 1;
    return (bmi - 15) / 25;
  }

  String _statusLabel() {
    if (bmi < 18.5) return I18nService.t('bmi.underweight');
    if (bmi < 25) return I18nService.t('bmi.normal');
    if (bmi < 30) return I18nService.t('bmi.overweight');
    return I18nService.t('bmi.obese');
  }

  Color _statusColor() {
    if (bmi < 18.5) return AppColors.blue;
    if (bmi < 25) return AppColors.green;
    if (bmi < 30) return AppColors.yellow;
    return AppColors.red;
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Labels
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            _label(I18nService.t('bmi.low')),
            _label(I18nService.t('bmi.ideal')),
            _label(I18nService.t('bmi.high')),
            _label(I18nService.t('bmi.obese_short')),
          ],
        ),
        const SizedBox(height: 4),
        // Bar
        LayoutBuilder(
          builder: (context, constraints) {
            final width = constraints.maxWidth;
            final pos = _position() * width;
            return Stack(
              clipBehavior: Clip.none,
              children: [
                Container(
                  height: 8,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(4),
                    gradient: const LinearGradient(
                      colors: [
                        AppColors.blue,
                        AppColors.green,
                        AppColors.yellow,
                        AppColors.red,
                      ],
                      stops: [0.0, 0.14, 0.40, 0.60],
                    ),
                  ),
                ),
                Positioned(
                  left: pos.clamp(6, width - 6) - 6,
                  top: -2,
                  child: Container(
                    width: 12,
                    height: 12,
                    decoration: BoxDecoration(
                      color: Colors.white,
                      shape: BoxShape.circle,
                      border: Border.all(color: AppColors.textPrimary, width: 2.5),
                    ),
                  ),
                ),
              ],
            );
          },
        ),
        const SizedBox(height: 6),
        Text(
          _statusLabel(),
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w600,
            color: _statusColor(),
          ),
        ),
      ],
    );
  }

  Widget _label(String text) {
    return Text(
      text.toUpperCase(),
      style: const TextStyle(
        fontSize: 8,
        fontWeight: FontWeight.w600,
        color: AppColors.textMuted,
        letterSpacing: 0.3,
      ),
    );
  }
}
