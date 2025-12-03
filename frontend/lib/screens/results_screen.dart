import 'dart:async';
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../config/app_config.dart';

class ResultsScreen extends StatefulWidget {
  final String sessionId;

  const ResultsScreen({super.key, required this.sessionId});

  @override
  State<ResultsScreen> createState() => _ResultsScreenState();
}

class _ResultsScreenState extends State<ResultsScreen> with SingleTickerProviderStateMixin {
  final ApiService _apiService = ApiService();
  Timer? _pollingTimer;
  Timer? _countdownTimer;
  Map<String, dynamic>? _userReport;
  Map<String, dynamic>? _hcpReport;
  bool _isLoading = true;
  String _status = 'processing';
  late TabController _tabController;
  int _elapsedSeconds = 0;
  static const int _estimatedSeconds = 240; // 4 minutes estimated time

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _startPolling();
    _startCountdown();
  }

  @override
  void dispose() {
    _pollingTimer?.cancel();
    _countdownTimer?.cancel();
    _tabController.dispose();
    super.dispose();
  }

  void _startPolling() {
    _pollingTimer = Timer.periodic(const Duration(seconds: 3), (_) async {
      await _checkResults();
    });
    _checkResults();
  }

  void _startCountdown() {
    _countdownTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted && _isLoading) {
        setState(() {
          _elapsedSeconds++;
        });
      }
    });
  }

  Future<void> _checkResults() async {
    final results = await _apiService.getAnalysisResults(widget.sessionId);

    if (results != null && mounted) {
      setState(() {
        _status = results['status'] ?? 'processing';
      });

      if (_status == 'completed') {
        _pollingTimer?.cancel();
        await _loadReports();
      } else if (_status == 'failed') {
        _pollingTimer?.cancel();
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _loadReports() async {
    final userReport = await _apiService.getUserReport(widget.sessionId);
    final hcpReport = await _apiService.getHCPReport(widget.sessionId);

    if (mounted) {
      setState(() {
        _userReport = userReport;
        _hcpReport = hcpReport;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Analysis Results'),
        backgroundColor: Theme.of(context).colorScheme.primary,
        foregroundColor: Colors.white,
        bottom: _isLoading || _status != 'completed'
            ? null
            : TabBar(
                controller: _tabController,
                labelColor: Colors.white,
                unselectedLabelColor: Colors.white70,
                indicatorColor: Colors.white,
                tabs: const [
                  Tab(icon: Icon(Icons.person), text: 'Your Report'),
                  Tab(icon: Icon(Icons.local_hospital), text: 'Clinical Report'),
                ],
              ),
      ),
      body: _isLoading || _status != 'completed'
          ? _buildLoadingView()
          : TabBarView(
              controller: _tabController,
              children: [
                _buildUserReportView(),
                _buildHCPReportView(),
              ],
            ),
    );
  }

  Widget _buildLoadingView() {
    final remainingSeconds = _estimatedSeconds - _elapsedSeconds;
    final minutes = (remainingSeconds / 60).floor();
    final seconds = remainingSeconds % 60;
    final progress = _elapsedSeconds / _estimatedSeconds;

    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          if (_status == 'processing') ...[
            // Circular progress indicator with countdown
            SizedBox(
              width: 160,
              height: 160,
              child: Stack(
                alignment: Alignment.center,
                children: [
                  SizedBox(
                    width: 160,
                    height: 160,
                    child: CircularProgressIndicator(
                      value: progress > 1.0 ? null : progress,
                      strokeWidth: 8,
                      backgroundColor: Colors.grey.shade200,
                    ),
                  ),
                  Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      if (remainingSeconds > 0) ...[
                        Text(
                          '$minutes:${seconds.toString().padLeft(2, '0')}',
                          style: Theme.of(context).textTheme.displayMedium?.copyWith(
                                fontWeight: FontWeight.bold,
                                color: Theme.of(context).colorScheme.primary,
                              ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'remaining',
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: Colors.grey.shade600,
                              ),
                        ),
                      ] else ...[
                        Icon(
                          Icons.hourglass_empty,
                          size: 48,
                          color: Theme.of(context).colorScheme.primary,
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Finishing up...',
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: Colors.grey.shade600,
                              ),
                        ),
                      ],
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 32),
            Text(
              'Analyzing your skin condition...',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            Text(
              'AI agents are working together',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Colors.grey.shade600,
                  ),
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                _buildAnalysisStep('CNN', _elapsedSeconds > 10),
                const SizedBox(width: 16),
                _buildAnalysisStep('Vision AI', _elapsedSeconds > 60),
                const SizedBox(width: 16),
                _buildAnalysisStep('EASI', _elapsedSeconds > 120),
              ],
            ),
          ] else if (_status == 'failed') ...[
            Icon(Icons.error_outline, size: 64, color: Colors.red.shade300),
            const SizedBox(height: 24),
            Text(
              'Analysis Failed',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            const Text('Please try again later'),
          ],
        ],
      ),
    );
  }

  Widget _buildAnalysisStep(String label, bool isActive) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: isActive
            ? Theme.of(context).colorScheme.primaryContainer
            : Colors.grey.shade200,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (isActive)
            Icon(
              Icons.check_circle,
              size: 16,
              color: Theme.of(context).colorScheme.primary,
            )
          else
            SizedBox(
              width: 12,
              height: 12,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                color: Colors.grey.shade400,
              ),
            ),
          const SizedBox(width: 6),
          Text(
            label,
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w500,
              color: isActive
                  ? Theme.of(context).colorScheme.primary
                  : Colors.grey.shade600,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildUserReportView() {
    if (_userReport == null) {
      return const Center(child: Text('No report available'));
    }

    final severity = _userReport!['severity'] ?? 'Unknown';
    final summary = _userReport!['summary'] ?? 'No summary available';
    final recommendations = _userReport!['recommendations'] as List? ?? [];
    final aiInsights = _userReport!['ai_insights'] ?? {};

    return SingleChildScrollView(
      padding: const EdgeInsets.all(24.0),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 800),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Severity Card
              Card(
                color: _getSeverityColor(severity),
                child: Padding(
                  padding: const EdgeInsets.all(24.0),
                  child: Column(
                    children: [
                      Icon(
                        _getSeverityIcon(severity),
                        size: 64,
                        color: Colors.white,
                      ),
                      const SizedBox(height: 16),
                      Text(
                        'Severity: $severity',
                        style: const TextStyle(
                          fontSize: 24,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Summary Card
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(Icons.article, color: Theme.of(context).colorScheme.primary),
                          const SizedBox(width: 8),
                          const Text(
                            'Summary',
                            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Text(summary, style: const TextStyle(fontSize: 16)),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // Recommendations Card
              if (recommendations.isNotEmpty)
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(Icons.recommend, color: Theme.of(context).colorScheme.primary),
                            const SizedBox(width: 8),
                            const Text(
                              'Recommendations',
                              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        ...recommendations.map((rec) => Padding(
                              padding: const EdgeInsets.only(bottom: 8.0),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Icon(Icons.check_circle, size: 20, color: Colors.green),
                                  const SizedBox(width: 8),
                                  Expanded(child: Text(rec.toString())),
                                ],
                              ),
                            )),
                      ],
                    ),
                  ),
                ),
              const SizedBox(height: 16),

              // AI Insights Card
              if (aiInsights.isNotEmpty)
                Card(
                  color: Colors.blue.shade50,
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(Icons.psychology, color: Colors.blue.shade700),
                            const SizedBox(width: 8),
                            Text(
                              'AI Analysis',
                              style: TextStyle(
                                fontSize: 20,
                                fontWeight: FontWeight.bold,
                                color: Colors.blue.shade900,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        if (aiInsights['severity_score'] != null)
                          _buildMetric('Severity Score', '${aiInsights['severity_score']}/100'),
                        if (aiInsights['affected_area_pct'] != null)
                          _buildMetric('Affected Area', '${aiInsights['affected_area_pct']}%'),
                        if (aiInsights['flare_status'] != null)
                          _buildMetric('Status', aiInsights['flare_status']),
                      ],
                    ),
                  ),
                ),
              const SizedBox(height: 24),

              // Disclaimer
              Card(
                color: Colors.orange.shade50,
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Row(
                    children: [
                      Icon(Icons.warning_amber, color: Colors.orange.shade700),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          'This is not a medical diagnosis. Please consult a healthcare professional for proper evaluation and treatment.',
                          style: TextStyle(color: Colors.orange.shade900),
                        ),
                      ),
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

  Widget _buildHCPReportView() {
    if (_hcpReport == null) {
      return const Center(child: Text('No clinical report available'));
    }

    final integrated = _hcpReport!['integrated_assessment'] ?? {};
    final easiScore = integrated['easi_score'] ?? 'N/A';
    final severityCategory = integrated['severity_category'] ?? 'N/A';
    final cnnAnalysis = _hcpReport!['cnn_analysis'] ?? {};
    final visionFindings = _hcpReport!['vision_agent_findings'] ?? {};
    final easiBreakdown = _hcpReport!['easi_breakdown'] ?? {};
    final clinicalInterpretation = _hcpReport!['clinical_interpretation'] ?? {};
    final saliencyMapUrl = _hcpReport!['saliency_map_url'];

    return SingleChildScrollView(
      padding: const EdgeInsets.all(24.0),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 800),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // EASI Score Card
              Card(
                color: Theme.of(context).colorScheme.primaryContainer,
                child: Padding(
                  padding: const EdgeInsets.all(24.0),
                  child: Column(
                    children: [
                      const Text(
                        'EASI Score',
                        style: TextStyle(fontSize: 18, fontWeight: FontWeight.w500),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        '$easiScore / 72',
                        style: const TextStyle(
                          fontSize: 48,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Severity: $severityCategory',
                        style: const TextStyle(fontSize: 16),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Integrated Assessment Card
              if (integrated.isNotEmpty)
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Integrated Assessment',
                          style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 12),
                        if (integrated['cnn_severity'] != null)
                          _buildMetric('CNN Severity', '${integrated['cnn_severity']}/100'),
                        if (integrated['agent_consensus'] != null)
                          _buildMetric('Agent Consensus', integrated['agent_consensus'].toString()),
                      ],
                    ),
                  ),
                ),
              const SizedBox(height: 16),

              // Saliency Map
              if (saliencyMapUrl != null && saliencyMapUrl.isNotEmpty)
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(Icons.visibility, color: Theme.of(context).colorScheme.primary),
                            const SizedBox(width: 8),
                            const Text(
                              'AI Attention Map',
                              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        const Text(
                          'Highlighted areas show where the AI focused during analysis:',
                          style: TextStyle(fontSize: 14, color: Colors.grey),
                        ),
                        const SizedBox(height: 12),
                        ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: Image.network(
                            _buildFullUrl(saliencyMapUrl),
                            fit: BoxFit.contain,
                            errorBuilder: (context, error, stackTrace) => const Text('Saliency map not available'),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              const SizedBox(height: 16),

              // EASI Breakdown
              if (easiBreakdown.isNotEmpty)
                _buildClinicalCard('EASI Score Breakdown', easiBreakdown),

              // CNN Analysis
              if (cnnAnalysis.isNotEmpty)
                _buildClinicalCard('CNN Analysis', cnnAnalysis),

              // Vision Agent Findings
              if (visionFindings.isNotEmpty)
                _buildClinicalCard('Vision AI Findings', visionFindings),

              // Clinical Interpretation
              if (clinicalInterpretation.isNotEmpty)
                _buildClinicalCard('Clinical Interpretation', clinicalInterpretation),

              // Treatment Recommendations
              if (_hcpReport!['treatment_recommendations'] != null)
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Treatment Recommendations',
                          style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 12),
                        Text(_hcpReport!['treatment_recommendations'].toString()),
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

  Widget _buildClinicalCard(String title, Map<String, dynamic> data) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            ...data.entries.map((entry) => Padding(
                  padding: const EdgeInsets.only(bottom: 8.0),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      SizedBox(
                        width: 150,
                        child: Text(
                          '${entry.key}:',
                          style: const TextStyle(fontWeight: FontWeight.w500),
                        ),
                      ),
                      Expanded(
                        child: Text(entry.value.toString()),
                      ),
                    ],
                  ),
                )),
          ],
        ),
      ),
    );
  }

  Widget _buildMetric(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontWeight: FontWeight.w500)),
          Text(value, style: const TextStyle(fontSize: 16)),
        ],
      ),
    );
  }

  Color _getSeverityColor(String severity) {
    switch (severity.toLowerCase()) {
      case 'mild':
        return Colors.green;
      case 'moderate':
        return Colors.orange;
      case 'severe':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  IconData _getSeverityIcon(String severity) {
    switch (severity.toLowerCase()) {
      case 'mild':
        return Icons.check_circle;
      case 'moderate':
        return Icons.warning;
      case 'severe':
        return Icons.error;
      default:
        return Icons.help;
    }
  }

  String _buildFullUrl(String relativePath) {
    // Convert relative path to full URL using the backend base URL
    // AppConfig.apiBaseUrl is like "https://...run.app/api/v1"
    // We need to remove "/api/v1" and append the relative path
    final baseUrl = AppConfig.apiBaseUrl.replaceAll('/api/v1', '');
    return '$baseUrl$relativePath';
  }
}
