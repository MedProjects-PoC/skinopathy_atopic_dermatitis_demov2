import 'package:flutter/material.dart';
import 'screens/device_selection_screen.dart';
import 'config/app_config.dart';

void main() {
  runApp(const SkinopathyADApp());
}

class SkinopathyADApp extends StatelessWidget {
  const SkinopathyADApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Skinopathy AD Assessment - ${AppConfig.environment}',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF2196F3),
          brightness: Brightness.light,
        ),
        useMaterial3: true,
        cardTheme: CardThemeData(
          elevation: 2,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
      ),
      home: const DeviceSelectionScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}
