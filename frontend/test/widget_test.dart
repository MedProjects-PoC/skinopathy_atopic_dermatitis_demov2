import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/main.dart';

void main() {
  testWidgets('App loads correctly', (WidgetTester tester) async {
    await tester.pumpWidget(const SkinopathyADApp());
    expect(find.text('Atopic Dermatitis Assessment'), findsOneWidget);
  });
}
