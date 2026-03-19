import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../services/i18n_service.dart';

class GoalCard extends StatelessWidget {
  final Map<String, dynamic> goal;
  final double currentWeight;

  const GoalCard({
    super.key,
    required this.goal,
    required this.currentWeight,
  });

  @override
  Widget build(BuildContext context) {
    final targetWeight = (goal['target_value'] as num).toDouble();
    final diff = (currentWeight - targetWeight).abs();
    final isLoss = targetWeight < currentWeight;
    final totalRange = isLoss ? currentWeight - targetWeight : targetWeight - currentWeight;
    final progress = totalRange > 0 ? (diff / totalRange).clamp(0.0, 1.0) : 1.0;
    final isReached = diff < 0.5;

    String statusText;
    if (isReached) {
      statusText = I18nService.t('overview.goal_reached');
    } else if (isLoss) {
      statusText = I18nService.t('overview.goal_remain').replaceAll('{diff}', diff.toStringAsFixed(1));
    } else {
      statusText = I18nService.t('overview.goal_gain').replaceAll('{diff}', diff.toStringAsFixed(1));
    }

    return Container(
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
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                I18nService.t('overview.goal_title'),
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                  color: AppColors.textPrimary,
                ),
              ),
              Text(
                statusText,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: isReached ? AppColors.green : AppColors.blue,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          // Progress bar
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: 1.0 - progress,
              minHeight: 8,
              backgroundColor: AppColors.borderLight,
              color: isReached ? AppColors.green : AppColors.blue,
            ),
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _label(I18nService.t('overview.goal_current'), '${currentWeight.toStringAsFixed(1)} kg'),
              _label(I18nService.t('overview.goal_target'), '${targetWeight.toStringAsFixed(1)} kg'),
            ],
          ),
        ],
      ),
    );
  }

  Widget _label(String title, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(
            fontSize: 9,
            fontWeight: FontWeight.w600,
            color: AppColors.textMuted,
            letterSpacing: 0.5,
          ),
        ),
        Text(
          value,
          style: const TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w700,
            color: AppColors.textPrimary,
          ),
        ),
      ],
    );
  }
}
