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
  final Set<String> _expandedGroups = {};
  bool _compareMode = false;

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

    // Expand current month by default
    final now = DateTime.now();
    _expandedGroups.add('${now.year}/${now.month.toString().padLeft(2, '0')}');

    setState(() {
      _user = user;
      _measurements = measurements;
      _loading = false;
    });
  }

  /// Groups measurements by year/month key (e.g. "2026/03").
  Map<String, List<Map<String, dynamic>>> _groupByMonth() {
    final groups = <String, List<Map<String, dynamic>>>{};
    for (final m in _measurements) {
      final dt = DateTime.tryParse(m['measured_at']?.toString() ?? '');
      if (dt == null) continue;
      final key = '${dt.year}/${dt.month.toString().padLeft(2, '0')}';
      groups.putIfAbsent(key, () => []).add(m);
    }
    return groups;
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
                        const SizedBox(height: 16),
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
      bottomNavigationBar: _measurements.isNotEmpty ? _buildBottomBar() : null,
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
                : Center(
                    child: Icon(Icons.bar_chart_rounded, size: 40, color: AppColors.textMuted),
                  ),
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

  // ─── Column headers ───
  Widget _buildColumnHeaders() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        children: [
          SizedBox(
            width: 70,
            child: Text(
              I18nService.t('history.col_time'),
              style: const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: AppColors.textMuted,
              ),
            ),
          ),
          Expanded(
            child: Text(
              I18nService.t('history.col_weight'),
              style: const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: AppColors.textMuted,
              ),
            ),
          ),
          Expanded(
            child: Text(
              I18nService.t('history.col_fat'),
              style: const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: AppColors.textMuted,
              ),
            ),
          ),
          const SizedBox(width: 30),
        ],
      ),
    );
  }

  // ─── Group header (year/month) ───
  Widget _buildGroupHeader(String groupKey, List<Map<String, dynamic>> items) {
    final isExpanded = _expandedGroups.contains(groupKey);

    // Calculate monthly deltas (first - last in group)
    final firstWeight = (items.first['weight_kg'] as num).toDouble();
    final lastWeight = (items.last['weight_kg'] as num).toDouble();
    final weightDelta = items.length > 1 ? firstWeight - lastWeight : 0.0;

    final firstFat = (items.first['body_fat_percent'] as num?)?.toDouble();
    final lastFat = (items.last['body_fat_percent'] as num?)?.toDouble();
    final fatDelta = (firstFat != null && lastFat != null && items.length > 1)
        ? firstFat - lastFat
        : null;

    const orange = Color(0xFFE67E22);

    return GestureDetector(
      onTap: () {
        setState(() {
          if (isExpanded) {
            _expandedGroups.remove(groupKey);
          } else {
            _expandedGroups.add(groupKey);
          }
        });
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        decoration: BoxDecoration(
          color: AppColors.bgCard,
          borderRadius: BorderRadius.circular(12),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.03),
              blurRadius: 6,
              offset: const Offset(0, 1),
            ),
          ],
        ),
        child: Row(
          children: [
            // Orange vertical bar
            Container(
              width: 3,
              height: 24,
              margin: const EdgeInsets.only(right: 10),
              decoration: BoxDecoration(
                color: orange,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            // Year/Month
            SizedBox(
              width: 62,
              child: Text(
                groupKey,
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: orange,
                ),
              ),
            ),
            // Weight delta
            Expanded(
              child: Text(
                _formatGroupDelta(weightDelta),
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                  color: orange,
                ),
              ),
            ),
            // Fat delta
            Expanded(
              child: Text(
                fatDelta != null ? _formatGroupDelta(fatDelta) : '--',
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                  color: orange,
                ),
              ),
            ),
            // Toggle chevron
            Icon(
              isExpanded ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down,
              color: orange,
              size: 22,
            ),
          ],
        ),
      ),
    );
  }

  String _formatGroupDelta(double delta) {
    if (delta.abs() < 0.05) return '--';
    final sign = delta > 0 ? '+' : '';
    return '$sign${delta.toStringAsFixed(1)}';
  }

  // ─── Measurement row ───
  Widget _buildMeasurementRow(Map<String, dynamic> m, Map<String, dynamic>? prev) {
    final id = m['id'] as int;
    final weight = (m['weight_kg'] as num).toDouble();
    final fat = (m['body_fat_percent'] as num?)?.toDouble();
    final dt = DateTime.tryParse(m['measured_at']?.toString() ?? '');
    final isSelected = _selectedIds.contains(id);

    final prevWeight = prev != null ? (prev['weight_kg'] as num).toDouble() : null;
    final prevFat = prev != null ? (prev['body_fat_percent'] as num?)?.toDouble() : null;

    final weightDelta = prevWeight != null ? weight - prevWeight : null;
    final fatDelta = (fat != null && prevFat != null) ? fat - prevFat : null;

    return GestureDetector(
      onTap: () {
        if (_compareMode) {
          setState(() {
            if (isSelected) {
              _selectedIds.remove(id);
            } else {
              _selectedIds.add(id);
            }
          });
        } else {
          context.push('/composition?id=$id');
        }
      },
      onLongPress: () => _confirmDelete(id),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 2),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.blueLight : AppColors.bgCard,
          borderRadius: BorderRadius.circular(12),
          border: isSelected
              ? Border.all(color: AppColors.blue, width: 1.5)
              : null,
        ),
        child: Row(
          children: [
            // Checkbox (only in compare mode)
            if (_compareMode) ...[
              Container(
                width: 20,
                height: 20,
                margin: const EdgeInsets.only(right: 8),
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: isSelected ? AppColors.blue : AppColors.borderLight,
                    width: 2,
                  ),
                  color: isSelected ? AppColors.blue : Colors.transparent,
                ),
                child: isSelected
                    ? const Icon(Icons.check, size: 12, color: Colors.white)
                    : null,
              ),
            ],
            // Date/time
            SizedBox(
              width: 55,
              child: Text(
                dt != null
                    ? '${dt.month.toString().padLeft(2, '0')}/${dt.day.toString().padLeft(2, '0')}\n${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}'
                    : '--',
                style: const TextStyle(
                  fontSize: 12,
                  color: AppColors.textMuted,
                  height: 1.4,
                ),
              ),
            ),
            const SizedBox(width: 8),
            // Weight + delta
            Expanded(
              child: Row(
                children: [
                  Text(
                    weight.toStringAsFixed(2),
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w800,
                      color: AppColors.textPrimary,
                    ),
                  ),
                  const SizedBox(width: 4),
                  Text(
                    weightDelta != null
                        ? '${weightDelta >= 0 ? "+" : ""}${weightDelta.toStringAsFixed(1)}'
                        : '--',
                    style: const TextStyle(fontSize: 12, color: AppColors.textMuted),
                  ),
                ],
              ),
            ),
            // Fat + delta
            Expanded(
              child: Row(
                children: [
                  Text(
                    fat?.toStringAsFixed(1) ?? '--',
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w800,
                      color: AppColors.textPrimary,
                    ),
                  ),
                  const SizedBox(width: 4),
                  Text(
                    fatDelta != null
                        ? '${fatDelta >= 0 ? "+" : ""}${fatDelta.toStringAsFixed(1)}'
                        : '--',
                    style: const TextStyle(fontSize: 12, color: AppColors.textMuted),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ─── Records section with grouped layout ───
  Widget _buildRecords() {
    final groups = _groupByMonth();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildColumnHeaders(),
        for (final entry in groups.entries) ...[
          _buildGroupHeader(entry.key, entry.value),
          if (_expandedGroups.contains(entry.key))
            for (var i = 0; i < entry.value.length; i++)
              _buildMeasurementRow(
                entry.value[i],
                i + 1 < entry.value.length ? entry.value[i + 1] : null,
              ),
        ],
      ],
    );
  }

  // ─── Bottom bar with Comparison + Export buttons ───
  Widget _buildBottomBar() {
    final bool canCompare = _selectedIds.length == 2;

    return Container(
      padding: EdgeInsets.fromLTRB(16, 12, 16, MediaQuery.of(context).padding.bottom + 12),
      decoration: BoxDecoration(
        color: AppColors.bgCard,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.08),
            blurRadius: 8,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: Row(
        children: [
          Expanded(
            child: _buildGradientButton(
              icon: Icons.compare_arrows_rounded,
              label: I18nService.t('history.comparison_btn'),
              colors: _compareMode
                  ? [const Color(0xFFE67E22), const Color(0xFFF39C12)]
                  : [const Color(0xFFE67E22), const Color(0xFFF39C12)],
              onPressed: () {
                if (_compareMode && canCompare) {
                  final ids = _selectedIds.toList();
                  context.push('/comparison?a=${ids[0]}&b=${ids[1]}');
                } else {
                  setState(() {
                    _compareMode = !_compareMode;
                    if (!_compareMode) _selectedIds.clear();
                  });
                }
              },
              badge: _compareMode
                  ? '${_selectedIds.length}/2'
                  : null,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: _buildGradientButton(
              icon: Icons.ios_share_rounded,
              label: I18nService.t('history.export_btn'),
              colors: [const Color(0xFF4A90D9), const Color(0xFF6C5CE7)],
              onPressed: _shareAsImage,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildGradientButton({
    required IconData icon,
    required String label,
    required List<Color> colors,
    required VoidCallback onPressed,
    String? badge,
  }) {
    return Material(
      borderRadius: BorderRadius.circular(14),
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(14),
        child: Ink(
          padding: const EdgeInsets.symmetric(vertical: 14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(14),
            gradient: LinearGradient(
              colors: colors,
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, color: Colors.white, size: 18),
              const SizedBox(width: 8),
              Text(
                label,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w700,
                  fontSize: 14,
                ),
              ),
              if (badge != null) ...[
                const SizedBox(width: 6),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.3),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    badge,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ],
            ],
          ),
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
}
