import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../services/i18n_service.dart';
import 'bmi_bar.dart';

class WeightHeroCard extends StatelessWidget {
  final double weightKg;
  final double? deltaWeight;
  final double? bmi;
  final VoidCallback? onTap;

  const WeightHeroCard({
    super.key,
    required this.weightKg,
    this.deltaWeight,
    this.bmi,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: AppColors.bgCard,
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.06),
              blurRadius: 12,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              I18nService.t('overview.current_weight'),
              style: const TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                color: AppColors.textLabel,
                letterSpacing: 0.8,
              ),
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.baseline,
                  textBaseline: TextBaseline.alphabetic,
                  children: [
                    Text(
                      weightKg.toStringAsFixed(2),
                      style: const TextStyle(
                        fontSize: 42,
                        fontWeight: FontWeight.w800,
                        color: AppColors.textPrimary,
                        height: 1,
                      ),
                    ),
                    const SizedBox(width: 4),
                    const Text(
                      'kg',
                      style: TextStyle(
                        fontSize: 16,
                        color: AppColors.textMuted,
                      ),
                    ),
                  ],
                ),
                if (deltaWeight != null) _buildDelta(),
              ],
            ),
            if (bmi != null) ...[
              const SizedBox(height: 16),
              BmiBar(bmi: bmi!),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildDelta() {
    if (deltaWeight == null || deltaWeight == 0) {
      return Text(
        '= ${I18nService.t('overview.same_weight')}',
        style: const TextStyle(
          fontSize: 14,
          color: AppColors.textMuted,
          fontWeight: FontWeight.w600,
        ),
      );
    }

    final isGain = deltaWeight! > 0;
    final color = isGain ? AppColors.red : AppColors.green;
    final sign = isGain ? '+' : '';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Text(
          I18nService.t('overview.previous'),
          style: const TextStyle(
            fontSize: 10,
            color: AppColors.textMuted,
          ),
        ),
        Text(
          '$sign${deltaWeight!.toStringAsFixed(1)}',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.w800,
            color: color,
          ),
        ),
      ],
    );
  }
}
