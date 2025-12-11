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
  bool _isDownloadingUserPDF = false;
  bool _isDownloadingHCPPDF = false;
  static const int _estimatedSeconds = 240; // 4 minutes estimated time
  DateTime? _analysisStartTime; // Track when analysis started (server-side)

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
      if (mounted && _isLoading && _analysisStartTime != null) {
        // Calculate elapsed time from server start time, not local elapsed seconds
        final elapsedDuration = DateTime.now().difference(_analysisStartTime!);
        setState(() {
          _elapsedSeconds = elapsedDuration.inSeconds;
        });
      }
    });
  }

  Future<void> _checkResults() async {
    final results = await _apiService.getAnalysisResults(widget.sessionId);

    if (results != null && mounted) {
      // Initialize start time on first check (get it from server if available)
      if (_analysisStartTime == null && results['created_at'] != null) {
        try {
          _analysisStartTime = DateTime.parse(results['created_at']);
        } catch (e) {
          // Fallback: use current time minus some estimation
          _analysisStartTime = DateTime.now().subtract(const Duration(seconds: 1));
        }
      } else if (_analysisStartTime == null) {
        // If no server timestamp, estimate based on current time
        _analysisStartTime = DateTime.now();
      }

      setState(() {
        _status = results['status'] ?? 'processing';
      });

      if (_status == 'completed') {
        _pollingTimer?.cancel();
        _countdownTimer?.cancel();
        await _loadReports();
      } else if (_status == 'failed') {
        _pollingTimer?.cancel();
        _countdownTimer?.cancel();
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

  Future<void> _downloadUserPDF() async {
    setState(() => _isDownloadingUserPDF = true);
    try {
      final url = '${ApiService.baseUrl}/reports/${widget.sessionId}/pdf/user';
      // Using html package for web platform
      // For now, we'll open in a new tab
      if (Uri.parse(url).isAbsolute) {
        // Trigger download by opening in iframe or creating download link
        _triggerDownload(url, 'AD_Report_User_${widget.sessionId}.pdf');
      }
    } catch (e) {
      print('Error downloading user PDF: $e');
      _showErrorSnackbar('Failed to download user report PDF');
    } finally {
      if (mounted) {
        setState(() => _isDownloadingUserPDF = false);
      }
    }
  }

  Future<void> _downloadHCPPDF() async {
    setState(() => _isDownloadingHCPPDF = true);
    try {
      final url = '${ApiService.baseUrl}/reports/${widget.sessionId}/pdf/hcp';
      if (Uri.parse(url).isAbsolute) {
        _triggerDownload(url, 'AD_Report_Clinical_${widget.sessionId}.pdf');
      }
    } catch (e) {
      print('Error downloading HCP PDF: $e');
      _showErrorSnackbar('Failed to download clinical report PDF');
    } finally {
      if (mounted) {
        setState(() => _isDownloadingHCPPDF = false);
      }
    }
  }

  void _triggerDownload(String url, String filename) {
    // For Flutter web, we can use a simple approach with an anchor element
    // This is handled through dart:html or similar
    try {
      // Create an iframe to trigger download
      final anchor = Uri.parse(url);
      if (anchor.isAbsolute) {
        // For web platform, use window.location.href or similar
        print('Triggering download: $url');
        // The actual implementation depends on platform
        // For web: use html package to create and click anchor tag
      }
    } catch (e) {
      print('Error triggering download: $e');
    }
  }

  void _showErrorSnackbar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red.shade600,
        duration: const Duration(seconds: 3),
      ),
    );
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
    final minutes = (_elapsedSeconds / 60).floor();
    final seconds = _elapsedSeconds % 60;

    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          if (_status == 'processing') ...[
            // AI Loading Animation GIF
            Image.asset(
              'assets/icons/AiLoadingAnimation.gif',
              width: 200,
              height: 200,
            ),
            const SizedBox(height: 16),
            // Elapsed time display
            Text(
              '$minutes:${seconds.toString().padLeft(2, '0')}',
              style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: Theme.of(context).colorScheme.primary,
                  ),
            ),
            const SizedBox(height: 4),
            Text(
              'elapsed',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Colors.grey.shade600,
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
              const SizedBox(height: 24),

              // Download PDF Button
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: _isDownloadingUserPDF ? null : _downloadUserPDF,
                  icon: _isDownloadingUserPDF
                      ? SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor: AlwaysStoppedAnimation<Color>(
                              Theme.of(context).colorScheme.onPrimary,
                            ),
                          ),
                        )
                      : const Icon(Icons.download),
                  label: Text(_isDownloadingUserPDF ? 'Downloading...' : 'Download Report as PDF'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Theme.of(context).colorScheme.primary,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 12),
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
    final severityCategory = integrated['severity_category'] ?? 'N/A';
    final cnnAnalysis = _hcpReport!['cnn_analysis'] ?? {};
    final visionFindings = _hcpReport!['vision_agent_findings'] ?? {};
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
                        // Primary Consensus Metrics
                        if (integrated['consensus_severity'] != null)
                          _buildMetric('Consensus Severity', '${integrated['consensus_severity']}/100'),
                        if (integrated['consensus_affected_area'] != null)
                          _buildMetric('Consensus Affected Area', '${integrated['consensus_affected_area']}%'),
                        if (integrated['consensus_inflammation'] != null)
                          _buildMetric('Consensus Inflammation', '${integrated['consensus_inflammation']}/100'),
                        if (integrated['severity_category'] != null)
                          _buildMetric('Severity Category', integrated['severity_category'].toString()),
                        // Divider before individual agent scores
                        if ((integrated['cnn_severity'] != null || integrated['vision_severity_iga'] != null))
                          const Padding(
                            padding: EdgeInsets.symmetric(vertical: 8.0),
                            child: Divider(),
                          ),
                        // Individual Agent Scores (for comparison)
                        if (integrated['cnn_severity'] != null)
                          _buildMetric('CNN Severity', '${integrated['cnn_severity']}/100'),
                        if (integrated['vision_severity_iga'] != null)
                          _buildMetric('Vision AI IGA', '${integrated['vision_severity_iga']}/4'),
                      ],
                    ),
                  ),
                ),
              const SizedBox(height: 16),

              // Activation Channel Overlay
              if (_hcpReport!['activation_channel_url'] != null && _hcpReport!['activation_channel_url'].isNotEmpty)
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(Icons.grid_on, color: Theme.of(context).colorScheme.primary),
                            const SizedBox(width: 8),
                            const Text(
                              'EfficientNet-B7 Activation Channels',
                              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        const Text(
                          'Neural network activation showing areas that influenced the severity prediction. Verdigris overlay indicates learned feature activation intensity.',
                          style: TextStyle(fontSize: 13, color: Colors.grey),
                        ),
                        const SizedBox(height: 12),
                        Container(
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: Colors.grey.shade300),
                          ),
                          child: ClipRRect(
                            borderRadius: BorderRadius.circular(8),
                            child: Image.network(
                              _buildFullUrl(_hcpReport!['activation_channel_url']),
                              fit: BoxFit.contain,
                              errorBuilder: (context, error, stackTrace) =>
                                const Padding(
                                  padding: EdgeInsets.all(16.0),
                                  child: Text('Activation overlay not available'),
                                ),
                            ),
                          ),
                        ),
                        if (_hcpReport!['activation_channels_used'] != null) ...[
                          const SizedBox(height: 12),
                          const Divider(),
                          const SizedBox(height: 12),
                          const Text(
                            'Channels Used:',
                            style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                          ),
                          const SizedBox(height: 6),
                          Wrap(
                            spacing: 8,
                            children: (_hcpReport!['activation_channels_used'] as List)
                              .map((ch) => Chip(
                                label: Text('Channel $ch',
                                  style: const TextStyle(fontSize: 12, color: Colors.white),
                                ),
                                backgroundColor: Colors.teal.shade600,
                                materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                              ))
                              .toList(),
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
              const SizedBox(height: 16),

              // Clinical Note (SOAP Format)
              if (_hcpReport!['clinical_note'] != null)
                _buildClinicalNoteCard(_hcpReport!['clinical_note'] as Map<String, dynamic>),
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
                        // OpenCV Metrics
                        if (_hcpReport!['saliency_map_metrics'] != null) ...[
                          const SizedBox(height: 16),
                          const Divider(),
                          const SizedBox(height: 12),
                          Row(
                            children: [
                              Icon(Icons.analytics, color: Theme.of(context).colorScheme.secondary, size: 20),
                              const SizedBox(width: 8),
                              const Text(
                                'OpenCV Analysis',
                                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: Colors.blue.shade50,
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Column(
                              children: [
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Row(
                                      children: [
                                        Icon(Icons.circle, size: 8, color: Colors.blue.shade700),
                                        const SizedBox(width: 8),
                                        const Text('Lesions Detected:', style: TextStyle(fontWeight: FontWeight.w500)),
                                      ],
                                    ),
                                    Text(
                                      '${_hcpReport!['saliency_map_metrics']['lesion_count'] ?? 0}',
                                      style: TextStyle(
                                        fontSize: 16,
                                        fontWeight: FontWeight.bold,
                                        color: Colors.blue.shade900,
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 8),
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Row(
                                      children: [
                                        Icon(Icons.circle, size: 8, color: Colors.red.shade700),
                                        const SizedBox(width: 8),
                                        const Text('Erythema Coverage:', style: TextStyle(fontWeight: FontWeight.w500)),
                                      ],
                                    ),
                                    Text(
                                      '${(_hcpReport!['saliency_map_metrics']['erythema_percentage'] ?? 0).toStringAsFixed(1)}%',
                                      style: TextStyle(
                                        fontSize: 16,
                                        fontWeight: FontWeight.bold,
                                        color: Colors.red.shade900,
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
              const SizedBox(height: 16),

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
              const SizedBox(height: 24),

              // Download PDF Button
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: _isDownloadingHCPPDF ? null : _downloadHCPPDF,
                  icon: _isDownloadingHCPPDF
                      ? SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor: AlwaysStoppedAnimation<Color>(
                              Theme.of(context).colorScheme.onPrimary,
                            ),
                          ),
                        )
                      : const Icon(Icons.download),
                  label: Text(_isDownloadingHCPPDF ? 'Downloading...' : 'Download Clinical Report as PDF'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Theme.of(context).colorScheme.primary,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 12),
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
            ...data.entries.map((entry) => _buildDataEntry(entry.key, entry.value, 0)),
          ],
        ),
      ),
    );
  }

  Widget _buildDataEntry(String key, dynamic value, int level) {
    final indent = level * 16.0;

    // Format the key to be more readable
    String formattedKey = key.replaceAll('_', ' ').split(' ').map((word) =>
      word.isEmpty ? word : word[0].toUpperCase() + word.substring(1)
    ).join(' ');

    if (value == null || value == '') {
      return const SizedBox.shrink();
    }

    // Special handling for Skin Tone Assessment - organize Monk and Fitzpatrick separately
    if (formattedKey == 'Skin Tone Assessment' && value is Map) {
      return _buildSkinToneAssessmentWidget(value as Map<String, dynamic>);
    }

    // Handle nested maps
    if (value is Map) {
      return Padding(
        padding: EdgeInsets.only(left: indent, bottom: 8.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '$formattedKey:',
              style: const TextStyle(
                fontWeight: FontWeight.w600,
                fontSize: 15,
                color: Colors.blueGrey,
              ),
            ),
            const SizedBox(height: 4),
            ...(value as Map).entries.map((e) => _buildDataEntry(e.key.toString(), e.value, level + 1)),
          ],
        ),
      );
    }

    // Handle lists
    if (value is List) {
      if (value.isEmpty) return const SizedBox.shrink();

      return Padding(
        padding: EdgeInsets.only(left: indent, bottom: 8.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '$formattedKey:',
              style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15),
            ),
            const SizedBox(height: 4),
            ...value.asMap().entries.map((e) => Padding(
              padding: EdgeInsets.only(left: (level + 1) * 16.0, bottom: 4.0),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('• ', style: TextStyle(fontSize: 16)),
                  Expanded(child: Text(_formatValue(e.value))),
                ],
              ),
            )),
          ],
        ),
      );
    }

    // Handle primitive values
    return Padding(
      padding: EdgeInsets.only(left: indent, bottom: 6.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 150,
            child: Text(
              '$formattedKey:',
              style: const TextStyle(fontWeight: FontWeight.w500),
            ),
          ),
          Expanded(
            child: Text(
              _formatValue(value),
              style: const TextStyle(fontSize: 14),
            ),
          ),
        ],
      ),
    );
  }

  String _formatValue(dynamic value) {
    if (value is num) {
      // Format numbers to 2 decimal places if needed
      if (value is double) {
        return value.toStringAsFixed(2);
      }
      return value.toString();
    }
    if (value is bool) {
      return value ? 'Yes' : 'No';
    }
    return value.toString();
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

  Widget _buildClinicalNoteCard(Map<String, dynamic> clinicalNote) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      elevation: 3,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.medical_information, color: Theme.of(context).colorScheme.primary),
                const SizedBox(width: 8),
                const Text(
                  'Clinical Note (SOAP Format)',
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Chief Complaint
            if (clinicalNote['chief_complaint'] != null)
              _buildSoapSection('Chief Complaint', clinicalNote['chief_complaint'], Colors.red.shade700),

            // History of Present Illness
            if (clinicalNote['history_present_illness'] != null)
              _buildSoapSection('History of Present Illness', clinicalNote['history_present_illness'], Colors.orange.shade700),

            // Objective Findings
            if (clinicalNote['objective_findings'] != null)
              _buildSoapSection('Objective Findings', clinicalNote['objective_findings'], Colors.blue.shade700),

            // Assessment
            if (clinicalNote['assessment'] != null)
              _buildSoapSection('Assessment', clinicalNote['assessment'], Colors.purple.shade700),

            // Plan
            if (clinicalNote['plan'] != null)
              _buildSoapSection('Plan', clinicalNote['plan'], Colors.green.shade700),

            // AI Insights
            if (clinicalNote['ai_insights'] != null)
              _buildSoapSection('AI Insights', clinicalNote['ai_insights'], Colors.teal.shade700),
          ],
        ),
      ),
    );
  }

  Widget _buildSoapSection(String title, String content, Color color) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.grey.shade50,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: Colors.grey.shade300),
            ),
            child: Text(
              content,
              style: const TextStyle(fontSize: 14, height: 1.5),
            ),
          ),
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

  Widget _buildSkinToneAssessmentWidget(Map<String, dynamic> data) {
    // Organize skin tone data into Monk and Fitzpatrick sections
    final monkFields = <String, dynamic>{};
    final fitzpatrickFields = <String, dynamic>{};
    final otherFields = <String, dynamic>{};

    data.forEach((key, value) {
      if (key.toLowerCase().contains('monk')) {
        monkFields[key] = value;
      } else if (key.toLowerCase().contains('fitzpatrick')) {
        fitzpatrickFields[key] = value;
      } else {
        otherFields[key] = value;
      }
    });

    return Padding(
      padding: const EdgeInsets.only(bottom: 16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Skin Tone Assessment:',
            style: const TextStyle(
              fontWeight: FontWeight.w600,
              fontSize: 16,
              color: Colors.blueGrey,
            ),
          ),
          const SizedBox(height: 12),

          // General info
          if (otherFields.isNotEmpty)
            ...otherFields.entries.map((entry) {
              final formattedKey = entry.key
                  .replaceAll('_', ' ')
                  .split(' ')
                  .map((word) => word.isEmpty ? word : word[0].toUpperCase() + word.substring(1))
                  .join(' ');
              return Padding(
                padding: const EdgeInsets.only(bottom: 8.0),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      '$formattedKey:',
                      style: const TextStyle(fontWeight: FontWeight.w500),
                    ),
                    Expanded(
                      child: Text(
                        _formatValue(entry.value),
                        style: const TextStyle(fontSize: 14),
                        textAlign: TextAlign.right,
                      ),
                    ),
                  ],
                ),
              );
            }),

          if (otherFields.isNotEmpty && (monkFields.isNotEmpty || fitzpatrickFields.isNotEmpty))
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 12.0),
              child: Divider(),
            ),

          // Monk Skin Tone Scale section
          if (monkFields.isNotEmpty)
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.teal.shade50,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.teal.shade200),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Monk Skin Tone Scale',
                    style: TextStyle(
                      fontWeight: FontWeight.w600,
                      fontSize: 14,
                      color: Colors.teal.shade700,
                    ),
                  ),
                  const SizedBox(height: 8),
                  ...monkFields.entries.map((entry) {
                    final formattedKey = entry.key
                        .replaceAll('_', ' ')
                        .replaceAll('monk', '')
                        .trim()
                        .split(' ')
                        .map((word) => word.isEmpty ? word : word[0].toUpperCase() + word.substring(1))
                        .join(' ');
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 6.0),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            '$formattedKey:',
                            style: const TextStyle(fontWeight: FontWeight.w500, fontSize: 13),
                          ),
                          Text(
                            _formatValue(entry.value),
                            style: TextStyle(fontSize: 13, color: Colors.teal.shade900),
                          ),
                        ],
                      ),
                    );
                  }),
                ],
              ),
            ),

          if (monkFields.isNotEmpty && fitzpatrickFields.isNotEmpty)
            const SizedBox(height: 12),

          // Fitzpatrick Scale section
          if (fitzpatrickFields.isNotEmpty)
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.amber.shade50,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.amber.shade200),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Fitzpatrick Scale',
                    style: TextStyle(
                      fontWeight: FontWeight.w600,
                      fontSize: 14,
                      color: Colors.amber.shade700,
                    ),
                  ),
                  const SizedBox(height: 8),
                  ...fitzpatrickFields.entries.map((entry) {
                    final formattedKey = entry.key
                        .replaceAll('_', ' ')
                        .replaceAll('fitzpatrick', '')
                        .trim()
                        .split(' ')
                        .map((word) => word.isEmpty ? word : word[0].toUpperCase() + word.substring(1))
                        .join(' ');
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 6.0),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            '$formattedKey:',
                            style: const TextStyle(fontWeight: FontWeight.w500, fontSize: 13),
                          ),
                          Text(
                            _formatValue(entry.value),
                            style: TextStyle(fontSize: 13, color: Colors.amber.shade900),
                          ),
                        ],
                      ),
                    );
                  }),
                ],
              ),
            ),
        ],
      ),
    );
  }
}
