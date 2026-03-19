import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:screenshot/screenshot.dart';
import 'package:share_plus/share_plus.dart';
import 'package:path_provider/path_provider.dart';
import '../theme/app_theme.dart';
import '../services/i18n_service.dart';
import '../database/database_helper.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  final _screenshotController = ScreenshotController();
  List<Map<String, dynamic>> _measurements = [];
  Map<String, dynamic>? _user;
  bool _loading = true;
  final Set<int> _selectedIds = {};

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    final db = DatabaseHelper.instance;
    final user = await db.getActiveUser();
    if (user == null) {
      setState(() => _loading = false);
      return;
    }
    final measurements = await db.getMeasurements(user['id'] as int);
    setState(() {
      _user = user;
      _measurements = measurements;
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

    return Scaffold(
      backgroundColor: AppColors.bgMain,
      body: SafeArea(
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildHeader(),
              if (_measurements.isEmpty)
                _buildEmpty()
              else
                Screenshot(
                  controller: _screenshotController,
                  child: Container(
                    color: AppColors.bgMain,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _buildTrendCard(),
                        _buildCompareBar(),
                        _buildRecords(),
                        const SizedBox(height: 24),
                      ],
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _shareAsImage() async {
    try {
      final Uint8List? imageBytes = await _screenshotController.capture(
        delay: const Duration(milliseconds: 100),
        pixelRatio: 2.0,
      );
      if (imageBytes == null) return;

      final dir = await getTemporaryDirectory();
      final file = File('${dir.path}/bioscale_history.png');
      await file.writeAsBytes(imageBytes);

      await Share.shareXFiles(
        [XFile(file.path)],
        text: 'BioScale - ${I18nService.t('history.title')}',
      );
    } catch (e) {
      debugPrint('Share error: $e');
    }
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.arrow_back_ios, size: 20),
            onPressed: () {
              if (context.canPop()) {
                context.pop();
              } else {
                context.go('/');
              }
            },
            color: AppColors.textPrimary,
          ),
          Expanded(
            child: Text(
              I18nService.t('history.title'),
              style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.w800,
                color: AppColors.textPrimary,
              ),
            ),
          ),
          if (_measurements.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.share_outlined, size: 22),
              onPressed: _shareAsImage,
              color: AppColors.blue,
            ),
        ],
      ),
    );
  }

  Widget _buildEmpty() {
    return Padding(
      padding: const EdgeInsets.all(32),
      child: Center(
        child: Column(
          children: [
            Text(
              I18nService.t('history.no_measurements'),
              style: const TextStyle(color: AppColors.textSecondary),
            ),
            const SizedBox(height: 16),
            TextButton(
              onPressed: () => context.go('/'),
              child: Text(I18nService.t('common.weigh_now'),
                  style: const TextStyle(color: AppColors.blue, fontWeight: FontWeight.w600)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTrendCard() {
    final weights = _measurements.map((m) => (m['weight_kg'] as num).toDouble()).toList();
    final avg = weights.reduce((a, b) => a + b) / weights.length;
    final maxW = weights.reduce((a, b) => a > b ? a : b);
    final minW = weights.reduce((a, b) => a < b ? a : b);

    double delta30d = 0;
    if (_measurements.length > 1) {
      final cutoff = DateTime.now().subtract(const Duration(days: 30));
      final first = _measurements.first;
      final older = _measurements.where((m) {
        final dt = DateTime.tryParse(m['measured_at']?.toString() ?? '');
        return dt != null && dt.isBefore(cutoff);
      }).toList();
      if (older.isNotEmpty) {
        delta30d = (first['weight_kg'] as num).toDouble() -
            (older.first['weight_kg'] as num).toDouble();
      } else {
        delta30d = (first['weight_kg'] as num).toDouble() -
            (_measurements.last['weight_kg'] as num).toDouble();
      }
    }

    // Chart data (reversed for chronological order)
    final reversed = _measurements.reversed.toList();
    final spots = <FlSpot>[];
    for (var i = 0; i < reversed.length; i++) {
      spots.add(FlSpot(i.toDouble(), (reversed[i]['weight_kg'] as num).toDouble()));
    }

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16),
      padding: const EdgeInsets.all(16),
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
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    I18nService.t('history.weight_trend'),
                    style: const TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: AppColors.textMuted,
                      letterSpacing: 0.5,
                    ),
                  ),
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.baseline,
                    textBaseline: TextBaseline.alphabetic,
                    children: [
                      Text(
                        avg.toStringAsFixed(2),
                        style: const TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.w800,
                          color: AppColors.textPrimary,
                        ),
                      ),
                      Text(
                        ' ${I18nService.t('history.average')}',
                        style: const TextStyle(fontSize: 11, color: AppColors.textMuted),
                      ),
                    ],
                  ),
                ],
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    '${delta30d <= 0 ? '↓' : '↑'} ${delta30d.abs().toStringAsFixed(2)} kg',
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w700,
                      color: delta30d <= 0 ? AppColors.green : AppColors.red,
                    ),
                  ),
                  Text(
                    I18nService.t('history.variation_30d'),
                    style: const TextStyle(fontSize: 10, color: AppColors.textMuted),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 16),
          SizedBox(
            height: 160,
            child: spots.length > 1
                ? LineChart(
                    LineChartData(
                      gridData: FlGridData(
                        show: true,
                        drawVerticalLine: false,
                        horizontalInterval: 5,
                        getDrawingHorizontalLine: (value) => FlLine(
                          color: AppColors.borderLight,
                          strokeWidth: 1,
                        ),
                      ),
                      titlesData: const FlTitlesData(show: false),
                      borderData: FlBorderData(show: false),
                      lineBarsData: [
                        LineChartBarData(
                          spots: spots,
                          color: AppColors.blue,
                          barWidth: 2.5,
                          isStrokeCapRound: true,
                          dotData: FlDotData(
                            show: true,
                            getDotPainter: (s, d, b, i) => FlDotCirclePainter(
                              radius: 3,
                              color: AppColors.blue,
                              strokeWidth: 0,
                            ),
                          ),
                          belowBarData: BarAreaData(
                            show: true,
                            color: AppColors.blue.withValues(alpha: 0.08),
                          ),
                        ),
                      ],
                    ),
                  )
                : const Center(child: Text('📊', style: TextStyle(fontSize: 40))),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              _statBox(I18nService.t('history.max'), '${maxW.toStringAsFixed(2)} kg'),
              const SizedBox(width: 12),
              _statBox(I18nService.t('history.min'), '${minW.toStringAsFixed(2)} kg'),
            ],
          ),
        ],
      ),
    );
  }

  Widget _statBox(String label, String value) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: AppColors.bgMain,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(
          children: [
            Text(label, style: const TextStyle(fontSize: 10, color: AppColors.textMuted, fontWeight: FontWeight.w600)),
            const SizedBox(height: 2),
            Text(value, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
          ],
        ),
      ),
    );
  }

  Widget _buildCompareBar() {
    String text = I18nService.t('history.compare_select');
    bool canCompare = _selectedIds.length == 2;

    if (_selectedIds.length == 1) {
      text = I18nService.t('history.compare_1of2');
    } else if (_selectedIds.length == 2) {
      text = I18nService.t('history.compare_2of2');
    } else if (_selectedIds.length > 2) {
      text = I18nService.t('history.compare_only2');
    }

    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        gradient: const LinearGradient(
          colors: [Color(0xFF4A90D9), Color(0xFF6C5CE7)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        boxShadow: [
          BoxShadow(
            color: AppColors.blue.withValues(alpha: 0.3),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Row(
        children: [
          const Text('📊', style: TextStyle(fontSize: 20)),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  I18nService.t('history.compare_title'),
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w700,
                    fontSize: 14,
                  ),
                ),
                Text(
                  text,
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.85),
                    fontSize: 11,
                  ),
                ),
              ],
            ),
          ),
          if (canCompare)
            ElevatedButton(
              onPressed: () {
                final ids = _selectedIds.toList();
                context.push('/comparison?a=${ids[0]}&b=${ids[1]}');
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.white,
                foregroundColor: AppColors.blue,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(20),
                ),
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
              ),
              child: Text(
                I18nService.t('history.compare_btn'),
                style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 12),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildRecords() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            I18nService.t('history.records'),
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              color: AppColors.textMuted,
              letterSpacing: 0.8,
            ),
          ),
          const SizedBox(height: 8),
          Container(
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
                for (var i = 0; i < _measurements.length && i < 30; i++)
                  _recordRow(i),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _recordRow(int index) {
    final m = _measurements[index];
    final id = m['id'] as int;
    final weight = (m['weight_kg'] as num).toDouble();
    final bmi = (m['bmi'] as num?)?.toDouble();
    final bf = (m['body_fat_percent'] as num?)?.toDouble();
    final isSelected = _selectedIds.contains(id);

    // BMI status
    String bmiLabel = '';
    Color bmiColor = AppColors.textMuted;
    Color bmiBg = AppColors.bgMain;
    if (bmi != null) {
      if (bmi < 18.5) {
        bmiLabel = I18nService.t('bmi.below');
        bmiColor = AppColors.blue;
        bmiBg = AppColors.blueLight;
      } else if (bmi < 25) {
        bmiLabel = I18nService.t('bmi.normal');
        bmiColor = AppColors.green;
        bmiBg = AppColors.greenLight;
      } else if (bmi < 30) {
        bmiLabel = I18nService.t('bmi.overweight');
        bmiColor = AppColors.yellow;
        bmiBg = AppColors.yellowLight;
      } else {
        bmiLabel = I18nService.t('bmi.obese');
        bmiColor = AppColors.red;
        bmiBg = AppColors.redLight;
      }
    }

    // Delta
    String delta = '';
    Color deltaColor = AppColors.textMuted;
    if (index + 1 < _measurements.length) {
      final d = weight - (_measurements[index + 1]['weight_kg'] as num).toDouble();
      if (d != 0) {
        delta = '${d > 0 ? '↑' : '↓'} ${d.abs().toStringAsFixed(1)}';
        deltaColor = d > 0 ? AppColors.red : AppColors.green;
      }
    }

    final dateStr = _formatDate(m['measured_at']);

    return InkWell(
      onTap: () => context.push('/composition?id=$id'),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        decoration: BoxDecoration(
          border: index > 0
              ? const Border(top: BorderSide(color: AppColors.borderLight, width: 0.5))
              : null,
        ),
        child: Row(
          children: [
            // Checkbox
            GestureDetector(
              onTap: () {
                setState(() {
                  if (isSelected) {
                    _selectedIds.remove(id);
                  } else {
                    _selectedIds.add(id);
                  }
                });
              },
              child: Container(
                width: 22,
                height: 22,
                margin: const EdgeInsets.only(right: 10),
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: isSelected ? AppColors.blue : AppColors.borderLight,
                    width: 2,
                  ),
                  color: isSelected ? AppColors.blue : Colors.transparent,
                ),
                child: isSelected
                    ? const Icon(Icons.check, size: 14, color: Colors.white)
                    : null,
              ),
            ),
            // Weight + date
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '${weight.toStringAsFixed(2)} kg',
                    style: const TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w700,
                      color: AppColors.textPrimary,
                    ),
                  ),
                  Text(
                    dateStr,
                    style: const TextStyle(fontSize: 11, color: AppColors.textMuted),
                  ),
                ],
              ),
            ),
            // BMI badge
            if (bmiLabel.isNotEmpty)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                margin: const EdgeInsets.only(right: 6),
                decoration: BoxDecoration(
                  color: bmiBg,
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  bmiLabel,
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w600,
                    color: bmiColor,
                  ),
                ),
              ),
            // Body fat
            if (bf != null)
              Text(
                '${bf.toStringAsFixed(0)}%',
                style: const TextStyle(fontSize: 11, color: AppColors.textMuted),
              ),
            const SizedBox(width: 6),
            // Delta
            if (delta.isNotEmpty)
              Text(
                delta,
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: deltaColor,
                ),
              ),
            // Delete
            IconButton(
              icon: const Icon(Icons.delete_outline, size: 18, color: AppColors.textMuted),
              onPressed: () => _confirmDelete(id),
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _confirmDelete(int id) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(I18nService.t('history.delete_title')),
        content: Text(I18nService.t('history.delete_confirm')),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text(I18nService.t('common.cancel')),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: TextButton.styleFrom(foregroundColor: AppColors.red),
            child: Text(I18nService.t('common.delete')),
          ),
        ],
      ),
    );
    if (confirmed == true) {
      await DatabaseHelper.instance.deleteMeasurement(id);
      _selectedIds.remove(id);
      await _loadData();
    }
  }

  String _formatDate(dynamic dt) {
    if (dt == null) return '--';
    DateTime date;
    if (dt is String) {
      date = DateTime.tryParse(dt) ?? DateTime.now();
    } else {
      date = dt as DateTime;
    }
    final months = [
      '', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ];
    final monthKey = 'month_short.${date.month}';
    final monthStr = I18nService.t(monthKey);
    final fallback = monthStr == monthKey ? months[date.month] : monthStr;
    return '${date.day.toString().padLeft(2, '0')} $fallback, ${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';
  }
}
