/// Application configuration for Skinopathy AD Demo
class AppConfig {
  // Environment settings
  static const String environment = 'DEMO';
  static const String version = '2.0';

  // Auto-detect environment based on hostname
  // This prevents manual config changes between dev and production
  static bool get isDevelopment {
    try {
      final hostname = Uri.base.host;
      // Check if running locally
      final isLocal = hostname == 'localhost' ||
                     hostname == '127.0.0.1';

      // Check if hostname is empty (Flutter desktop/mobile builds)
      // or if it's a Cloud Run production URL
      final isProduction = hostname.contains('run.app') ||
                          hostname.contains('cloudrun.app');

      // Return true only if explicitly local, false for production or empty
      return isLocal && !isProduction;
    } catch (e) {
      // Fallback to production (false) if Uri.base is unavailable
      return false;
    }
  }

  static bool get isProduction => !isDevelopment;

  // API Configuration - Auto-selected based on environment
  static String get apiBaseUrl => isDevelopment
      ? 'http://localhost:8000/api/v1'
      : 'https://skinopathy-atopic-dermatitis-demo2-api-oxp54sxycq-uc.a.run.app/api/v1';

  // Feature flags for demo
  static const bool enableDeviceSelection = true;
  static const bool showDevBanner = true;
  static const bool enableAnalytics = false; // Disabled for demo

  // UI Configuration
  static const double mobileMaxWidth = 400.0;
  static const double tabletMaxWidth = 700.0;
  static const double desktopMaxWidth = 1200.0;

  // Timeouts
  static const Duration apiTimeout = Duration(seconds: 30);
  static const Duration pollingInterval = Duration(seconds: 3);

  // Display names
  static String get appName => 'Skinopathy AD';
  static String get appSubtitle => 'Atopic Dermatitis Assessment';
  static String get appFullName => '$appName - $environment v$version';

  // Environment badge
  static String get environmentBadge {
    if (isDevelopment) return 'DEV';
    if (environment == 'DEMO') return 'DEMO';
    return 'PROD';
  }

  // API endpoints
  static String get uploadEndpoint => '$apiBaseUrl/upload/';
  static String analysisEndpoint(String sessionId) =>
      '$apiBaseUrl/analysis/$sessionId';
  static String userReportEndpoint(String sessionId) =>
      '$apiBaseUrl/reports/user/$sessionId';
  static String hcpReportEndpoint(String sessionId) =>
      '$apiBaseUrl/reports/hcp/$sessionId';
}
