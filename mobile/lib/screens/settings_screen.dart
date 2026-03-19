import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:share_plus/share_plus.dart';
import '../theme/app_theme.dart';
import '../services/i18n_service.dart';
import '../database/database_helper.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  String? _message;
  bool _isSuccess = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bgMain,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Row(
                children: [
                  IconButton(
                    icon: const Icon(Icons.arrow_back_ios, size: 20),
                    onPressed: () => context.go('/'),
                    color: AppColors.textPrimary,
                  ),
                  Text(
                    I18nService.t('settings.title'),
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w800,
                      color: AppColors.textPrimary,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // Language
              _sectionLabel(I18nService.t('settings.language')),
              _buildCard([
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: I18nService.languages.entries.map((entry) {
                    final isActive = entry.key == I18nService.currentLanguage;
                    return GestureDetector(
                      onTap: () async {
                        I18nService.setLanguage(entry.key);
                        final db = DatabaseHelper.instance;
                        final user = await db.getActiveUser();
                        if (user != null) {
                          await db.updateUser(user['id'] as int, {'language': entry.key});
                        }
                        setState(() {});
                      },
                      child: Container(
                        margin: const EdgeInsets.symmetric(horizontal: 6),
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(
                            color: isActive ? AppColors.blue : AppColors.borderLight,
                            width: 2,
                          ),
                          color: isActive ? AppColors.blueLight : Colors.transparent,
                        ),
                        child: Column(
                          children: [
                            Text(entry.value['flag']!, style: const TextStyle(fontSize: 24)),
                            const SizedBox(height: 4),
                            Text(
                              entry.value['name']!,
                              style: TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.w600,
                                color: isActive ? AppColors.blue : AppColors.textMuted,
                              ),
                            ),
                          ],
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ]),
              const SizedBox(height: 20),

              // Data Management
              _sectionLabel(I18nService.t('settings.manage_data')),
              _buildCard([
                _actionButton(
                  I18nService.t('settings.export_csv'),
                  Icons.description_outlined,
                  _exportCsv,
                ),
                const Divider(height: 1),
                _actionButton(
                  I18nService.t('settings.clear_history'),
                  Icons.delete_sweep_outlined,
                  _clearHistory,
                  color: AppColors.yellow,
                ),
              ]),
              const SizedBox(height: 20),

              // Privacy
              _sectionLabel(I18nService.t('settings.privacy')),
              _buildCard([
                Text(
                  I18nService.t('settings.privacy_text'),
                  style: const TextStyle(
                    fontSize: 12,
                    color: AppColors.textSecondary,
                    height: 1.5,
                  ),
                ),
                const SizedBox(height: 12),
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton(
                    onPressed: _deleteAllData,
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppColors.red,
                      side: const BorderSide(color: AppColors.red),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: Text(I18nService.t('settings.delete_all_btn')),
                  ),
                ),
              ]),
              const SizedBox(height: 20),

              // About
              _sectionLabel(I18nService.t('settings.about')),
              _buildCard([
                const Text(
                  'BioScale v1.0.0',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  I18nService.t('settings.about_desc'),
                  style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                ),
                const SizedBox(height: 4),
                Text(
                  I18nService.t('settings.about_copyright'),
                  style: const TextStyle(fontSize: 11, color: AppColors.textMuted),
                ),
              ]),

              // Message
              if (_message != null) ...[
                const SizedBox(height: 16),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: _isSuccess ? AppColors.greenLight : AppColors.redLight,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    _message!,
                    style: TextStyle(
                      color: _isSuccess ? AppColors.green : AppColors.red,
                      fontWeight: FontWeight.w600,
                      fontSize: 13,
                    ),
                  ),
                ),
              ],
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }

  Widget _sectionLabel(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(
        text.toUpperCase(),
        style: const TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w700,
          color: AppColors.textMuted,
          letterSpacing: 0.8,
        ),
      ),
    );
  }

  Widget _buildCard(List<Widget> children) {
    return Container(
      width: double.infinity,
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
        children: children,
      ),
    );
  }

  Widget _actionButton(String text, IconData icon, VoidCallback onTap, {Color? color}) {
    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 12),
        child: Row(
          children: [
            Icon(icon, size: 20, color: color ?? AppColors.blue),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                text,
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: color ?? AppColors.textPrimary,
                ),
              ),
            ),
            Icon(Icons.chevron_right, size: 20, color: AppColors.textMuted),
          ],
        ),
      ),
    );
  }

  Future<void> _exportCsv() async {
    final db = DatabaseHelper.instance;
    final user = await db.getActiveUser();
    if (user == null) {
      _showMessage(I18nService.t('settings.no_active_profile'), false);
      return;
    }
    final path = await db.exportCsv(user['id'] as int);
    await Share.shareXFiles([XFile(path)]);
    _showMessage(I18nService.t('settings.csv_exported').replaceAll('{path}', path), true);
  }

  Future<void> _clearHistory() async {
    final confirmed = await _confirmDialog(
      I18nService.t('history.delete_title'),
      I18nService.t('history.delete_confirm'),
    );
    if (confirmed != true) return;
    final db = DatabaseHelper.instance;
    final user = await db.getActiveUser();
    if (user != null) {
      await db.clearHistory(user['id'] as int);
      _showMessage(I18nService.t('settings.history_cleared'), true);
    }
  }

  Future<void> _deleteAllData() async {
    final confirmed = await _confirmDialog(
      I18nService.t('settings.delete_all_title'),
      '${I18nService.t('settings.delete_all_confirm')}\n\n${I18nService.t('settings.delete_all_warning')}',
      destructive: true,
    );
    if (confirmed != true) return;
    await DatabaseHelper.instance.deleteAllData();
    _showMessage(I18nService.t('settings.all_deleted'), true);
  }

  Future<bool?> _confirmDialog(String title, String content, {bool destructive = false}) {
    return showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(title),
        content: Text(content),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text(I18nService.t('common.cancel')),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: destructive ? TextButton.styleFrom(foregroundColor: AppColors.red) : null,
            child: Text(destructive
                ? I18nService.t('settings.delete_all_btn_confirm')
                : I18nService.t('common.delete')),
          ),
        ],
      ),
    );
  }

  void _showMessage(String msg, bool success) {
    setState(() {
      _message = msg;
      _isSuccess = success;
    });
    Future.delayed(const Duration(seconds: 4), () {
      if (mounted) setState(() => _message = null);
    });
  }
}
