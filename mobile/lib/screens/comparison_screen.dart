import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../theme/app_theme.dart';
import '../services/i18n_service.dart';
import '../database/database_helper.dart';
import '../calculations/body_composition.dart';

class ComparisonScreen extends StatefulWidget {
  final int? idA;
  final int? idB;

  const ComparisonScreen({super.key, this.idA, this.idB});

  @override
  State<ComparisonScreen> createState() => _ComparisonScreenState();
}

class _ComparisonScreenState extends State<ComparisonScreen> {
  bool _loading = true;
  Map<String, dynamic>? _mA; // newer
  Map<String, dynamic>? _mB; // older
  Map<String, ClassificationResult> _classA = {};
  Map<String, ClassificationResult> _classB = {};

  static const _compareGroups = {
    'comparison.group_summary': [
      ('weight_kg', 'comparison.weight_kg', false),
      ('bmi', 'comparison.bmi', false),
      ('body_score', 'comparison.body_score', true),
      ('metabolic_age', 'comparison.metabolic_age', false),
    ],
    'comparison.group_fat': [
      ('body_fat', 'comparison.body_fat', false),
      ('fat_mass', 'comparison.fat_mass', false),
      ('visceral_fat', 'comparison.visceral_fat', false),
    ],
    'comparison.group_muscle': [
      ('muscle_mass', 'comparison.muscle_mass', true),
      ('muscle_mass_kg', 'comparison.muscle_mass_kg', true),
      ('smm', 'comparison.smm', true),
      ('ffmi', 'comparison.ffmi', true),
      ('lbm', 'comparison.lbm', true),
    ],
    'comparison.group_composition': [
      ('body_water', 'comparison.body_water', true),
      ('water_mass', 'comparison.water_mass', true),
      ('bone_mass', 'comparison.bone_mass', true),
      ('protein', 'comparison.protein', true),
      ('bmr', 'comparison.bmr', true),
    ],
  };

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    if (widget.idA == null || widget.idB == null) {
      setState(() => _loading = false);
      return;
    }

    final db = DatabaseHelper.instance;
    final user = await db.getActiveUser();
    if (user == null) {
      setState(() => _loading = false);
      return;
    }

    var mA = await db.getMeasurement(widget.idA!);
    var mB = await db.getMeasurement(widget.idB!);

    if (mA == null || mB == null) {
      setState(() => _loading = false);
      return;
    }

    // Ensure mA is newer
    final dtA = DateTime.tryParse(mA['measured_at']?.toString() ?? '') ?? DateTime.now();
    final dtB = DateTime.tryParse(mB['measured_at']?.toString() ?? '') ?? DateTime.now();
    if (dtB.isAfter(dtA)) {
      final temp = mA;
      mA = mB;
      mB = temp;
    }

    final sex = user['sex'] as String;
    final age = (user['age'] as num).toInt();
    final height = (user['height_cm'] as num).toDouble();
    final activity = user['activity_level'] as String? ?? 'sedentary';
    final waist = (user['waist_cm'] as num?)?.toDouble();
    final hip = (user['hip_cm'] as num?)?.toDouble();

    Map<String, ClassificationResult> classA = {};
    Map<String, ClassificationResult> classB = {};

    try {
      final metricsA = getAllMetrics(
        (mA['weight_kg'] as num).toDouble(), height, age, sex,
        impedance: (mA['impedance'] as num?)?.toDouble(),
        activityLevel: activity, waistCm: waist, hipCm: hip,
      );
      classA = getClassifications(metricsA, sex, age, height);
    } catch (_) {}

    try {
      final metricsB = getAllMetrics(
        (mB['weight_kg'] as num).toDouble(), height, age, sex,
        impedance: (mB['impedance'] as num?)?.toDouble(),
        activityLevel: activity, waistCm: waist, hipCm: hip,
      );
      classB = getClassifications(metricsB, sex, age, height);
    } catch (_) {}

    setState(() {
      _mA = mA;
      _mB = mB;
      _classA = classA;
      _classB = classB;
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(
        backgroundColor: AppColors.bgMain,
        body: Center(child: CircularProgressIndicator(color: AppColors.blue)),
      );
    }

    if (_mA == null || _mB == null) {
      return Scaffold(
        backgroundColor: AppColors.bgMain,
        body: SafeArea(
          child: Column(
            children: [
              _buildHeader(),
              Expanded(
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        I18nService.t('comparison.select_prompt'),
                        textAlign: TextAlign.center,
                        style: const TextStyle(color: AppColors.textSecondary),
                      ),
                      const SizedBox(height: 16),
                      TextButton(
                        onPressed: () => context.push('/history'),
                        child: Text(
                          I18nService.t('comparison.back_history'),
                          style: const TextStyle(color: AppColors.blue, fontWeight: FontWeight.w600),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      );
    }

    final dtA = DateTime.tryParse(_mA!['measured_at']?.toString() ?? '') ?? DateTime.now();
    final dtB = DateTime.tryParse(_mB!['measured_at']?.toString() ?? '') ?? DateTime.now();
    final daysDiff = dtA.difference(dtB).inDays.abs();

    String badgeText;
    if (daysDiff == 0) {
      badgeText = I18nService.t('comparison.same_day');
    } else if (daysDiff == 1) {
      badgeText = I18nService.t('comparison.one_day');
    } else {
      badgeText = I18nService.t('comparison.days').replaceAll('{n}', daysDiff.toString());
    }

    // Summary deltas
    final wDiff = ((_mA!['weight_kg'] as num) - (_mB!['weight_kg'] as num)).toDouble();
    final bmiA = _classA['bmi']?.value ?? 0;
    final bmiB = _classB['bmi']?.value ?? 0;
    final bmiDiff = bmiA - bmiB;
    final bfA = _classA['body_fat']?.value ?? 0;
    final bfB = _classB['body_fat']?.value ?? 0;
    final bfDiff = bfA - bfB;

    return Scaffold(
      backgroundColor: AppColors.bgMain,
      body: SafeArea(
        child: SingleChildScrollView(
          child: Column(
            children: [
              _buildHeader(),
              // Main card
              Container(
                margin: const EdgeInsets.symmetric(horizontal: 16),
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
                  children: [
                    // Time badge
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.symmetric(vertical: 10),
                      decoration: BoxDecoration(
                        color: AppColors.blueLight,
                        borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text(
                            I18nService.t('comparison.within'),
                            style: const TextStyle(color: AppColors.blue, fontSize: 12),
                          ),
                          Text(
                            badgeText,
                            style: const TextStyle(
                              color: AppColors.blue,
                              fontSize: 12,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                        ],
                      ),
                    ),
                    // Summary cards
                    Padding(
                      padding: const EdgeInsets.all(16),
                      child: Row(
                        children: [
                          _summaryCard('⚖️', wDiff, 'PESO (KG)', false),
                          _summaryCard('📊', bmiDiff, 'IMC', false),
                          _summaryCard('⚡', bfDiff, 'FAT %', false),
                        ],
                      ),
                    ),
                    // Tabs
                    Row(
                      children: [
                        Expanded(
                          child: Container(
                            padding: const EdgeInsets.symmetric(vertical: 10),
                            decoration: const BoxDecoration(
                              border: Border(bottom: BorderSide(color: AppColors.blue, width: 2)),
                            ),
                            child: Text(
                              I18nService.t('comparison.before'),
                              textAlign: TextAlign.center,
                              style: const TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w700,
                                color: AppColors.blue,
                              ),
                            ),
                          ),
                        ),
                        Expanded(
                          child: Container(
                            padding: const EdgeInsets.symmetric(vertical: 10),
                            decoration: const BoxDecoration(
                              border: Border(bottom: BorderSide(color: AppColors.green, width: 2)),
                            ),
                            child: Text(
                              I18nService.t('comparison.after'),
                              textAlign: TextAlign.center,
                              style: const TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w700,
                                color: AppColors.green,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                    // Metric rows by group
                    ..._buildMetricGroups(),
                    const SizedBox(height: 8),
                  ],
                ),
              ),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.arrow_back_ios, size: 20),
            onPressed: () => context.push('/history'),
            color: AppColors.textPrimary,
          ),
          Text(
            I18nService.t('comparison.title'),
            style: const TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w800,
              color: AppColors.textPrimary,
            ),
          ),
        ],
      ),
    );
  }

  Widget _summaryCard(String icon, double value, String label, bool higherIsBetter) {
    String valStr;
    Color color;
    if (value == 0) {
      valStr = '=';
      color = AppColors.textMuted;
    } else {
      valStr = '${value > 0 ? '+' : ''}${value.toStringAsFixed(1)}';
      final improved = higherIsBetter ? value > 0 : value < 0;
      color = improved ? AppColors.green : AppColors.red;
    }

    return Expanded(
      child: Column(
        children: [
          Text(icon, style: const TextStyle(fontSize: 20)),
          const SizedBox(height: 4),
          Text(valStr, style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: color)),
          Text(label, textAlign: TextAlign.center, style: const TextStyle(fontSize: 9, color: AppColors.textMuted, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }

  List<Widget> _buildMetricGroups() {
    final widgets = <Widget>[];
    var gi = 0;

    for (final entry in _compareGroups.entries) {
      final groupRows = <Widget>[];

      for (final (key, nameKey, higherIsBetter) in entry.value) {
        double? va, vb;

        if (key == 'weight_kg') {
          va = (_mA!['weight_kg'] as num?)?.toDouble();
          vb = (_mB!['weight_kg'] as num?)?.toDouble();
        } else {
          va = _classA[key]?.value;
          vb = _classB[key]?.value;
        }

        if (va == null && vb == null) continue;

        final diff = ((va ?? 0) - (vb ?? 0));
        final dc = _deltaColor(diff, higherIsBetter);

        groupRows.add(
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    _formatVal(vb, key),
                    textAlign: TextAlign.center,
                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.textPrimary),
                  ),
                ),
                Expanded(
                  flex: 2,
                  child: Column(
                    children: [
                      Text(
                        I18nService.t(nameKey),
                        textAlign: TextAlign.center,
                        style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
                      ),
                      Text(
                        _formatDiff(diff, key),
                        style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: dc),
                      ),
                    ],
                  ),
                ),
                Expanded(
                  child: Text(
                    _formatVal(va, key),
                    textAlign: TextAlign.center,
                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.textPrimary),
                  ),
                ),
              ],
            ),
          ),
        );
      }

      if (groupRows.isNotEmpty) {
        if (gi > 0) {
          widgets.add(Divider(height: 1, color: AppColors.borderLight));
        }
        widgets.add(Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
          child: Text(
            I18nService.t(entry.key).toUpperCase(),
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              color: AppColors.textMuted,
              letterSpacing: 0.8,
            ),
          ),
        ));
        widgets.addAll(groupRows);
      }
      gi++;
    }
    return widgets;
  }

  Color _deltaColor(double diff, bool higherIsBetter) {
    if (diff == 0) return AppColors.textMuted;
    final improved = higherIsBetter ? diff > 0 : diff < 0;
    return improved ? AppColors.green : AppColors.red;
  }

  String _formatVal(double? v, String key) {
    if (v == null) return '--';
    if (['metabolic_age', 'body_score', 'visceral_fat'].contains(key)) {
      return v.toStringAsFixed(0);
    }
    return v.toStringAsFixed(1);
  }

  String _formatDiff(double diff, String key) {
    if (diff == 0) return '=';
    final sign = diff > 0 ? '+' : '';
    if (['metabolic_age', 'body_score', 'visceral_fat'].contains(key)) {
      return '$sign${diff.toStringAsFixed(0)}';
    }
    return '$sign${diff.toStringAsFixed(1)}';
  }
}
