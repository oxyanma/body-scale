import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'theme/app_theme.dart';
import 'screens/home_screen.dart';
import 'screens/composition_screen.dart';
import 'screens/history_screen.dart';
import 'screens/comparison_screen.dart';
import 'screens/profile_screen.dart';
import 'screens/settings_screen.dart';

final _router = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(path: '/', builder: (_, __) => const HomeScreen()),
    GoRoute(
      path: '/composition',
      builder: (_, state) {
        final id = state.uri.queryParameters['id'];
        return CompositionScreen(
            measurementId: id != null ? int.tryParse(id) : null);
      },
    ),
    GoRoute(path: '/history', builder: (_, __) => const HistoryScreen()),
    GoRoute(
      path: '/comparison',
      builder: (_, state) {
        final a = state.uri.queryParameters['a'];
        final b = state.uri.queryParameters['b'];
        return ComparisonScreen(
          idA: a != null ? int.tryParse(a) : null,
          idB: b != null ? int.tryParse(b) : null,
        );
      },
    ),
    GoRoute(path: '/profile', builder: (_, __) => const ProfileScreen()),
    GoRoute(path: '/settings', builder: (_, __) => const SettingsScreen()),
  ],
);

class BioScaleApp extends StatelessWidget {
  const BioScaleApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'BioScale',
      theme: AppTheme.lightTheme,
      routerConfig: _router,
      debugShowCheckedModeBanner: false,
    );
  }
}
