#!/usr/bin/env python3
"""
Test script for PDF generation functionality
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.pdf_service import PDFGenerator
from io import BytesIO
import uuid

# Sample user report data
sample_user_report = {
    'severity': 'Moderate',
    'summary': 'The analysis shows moderate atopic dermatitis with affected areas predominantly in the flexural regions. The skin exhibits signs of inflammation, dryness, and recent flare activity.',
    'key_findings': [
        'Moderate severity with 40-50% body surface affected',
        'Flexural distribution pattern consistent with adult AD',
        'Active flare status detected',
        'High itch intensity reported (7/10)',
        'Sleep disruption observed (4 nights/week)'
    ],
    'recommendations': [
        'Apply moisturizer at least twice daily, preferably within 3 minutes of bathing',
        'Continue topical steroids as prescribed; consider stepping up to moderate potency if not improving',
        'Identify and avoid triggers (stress, irritants, allergens)',
        'Consider antihistamines before bed to improve sleep',
        'Reduce stress through relaxation techniques'
    ],
    'when_to_seek_help': 'Seek immediate medical attention if you develop signs of infection (increasing redness, warmth, oozing, fever), or if your condition worsens despite treatment.',
    'ai_insights': {
        'severity_score': 68,
        'affected_area_pct': 45.2,
        'flare_status': 'active'
    }
}

# Sample HCP report data
sample_hcp_report = {
    'severity_assessment': {
        'cnn_severity': 68,
        'severity_category': 'Moderate',
        'lesion_count': 12,
        'erythema_percentage': 45.3,
        'inflammation_index': 7.2
    },
    'soap_note': {
        'subjective': 'Patient reports itch intensity 7/10 with chronic relapsing course over 2 years. Sleep disruption present (4 nights/week). Recent stress level 6/10. Using topical steroids (hydrocortisone) in past 2 weeks. Moisturizer applied once daily.',
        'objective': 'CNN Analysis: Severity 68/100, Flexural distribution, Active flare detected. Vision AI: Clinical assessment shows characteristic AD morphology with lichenification and excoriation.',
        'assessment': 'Atopic Dermatitis - Moderate severity with active flare. Meets Hanifin & Rajka criteria. Sleep-disrupting pruritus noted.',
        'plan': 'Continue emollients with focus on post-bathing application. Consider escalating topical corticosteroid to moderate potency (triamcinolone 0.1%). Offer systemic antihistamine for nighttime itch. Address stress management and trigger avoidance. Reassess in 2 weeks.'
    },
    'cnn_analysis': {
        'severity_score': 68,
        'flare_status': 'active',
        'body_region_distribution': {
            'head_neck': '10%',
            'trunk': '15%',
            'upper_extremities': '35%',
            'lower_extremities': '40%'
        }
    },
    'vision_agent_findings': {
        'clinical_assessment': 'Image shows characteristic AD morphology: erythema, lichenification, and excoriation primarily in flexural regions. Skin barrier compromise evident.',
        'differential_diagnosis': 'Primary diagnosis: Atopic Dermatitis. Differential considerations: Contact dermatitis (less likely given distribution), allergic dermatitis, asteatotic eczema.',
        'key_features': [
            'Flexural predominance (classic AD distribution)',
            'Evidence of lichenification (chronic rubbing)',
            'Excoriation marks from scratching',
            'Erythema indicating active inflammation'
        ]
    },
    'treatment_recommendations': [
        'Escalate topical corticosteroid: Triamcinolone acetate 0.1% cream BID',
        'Continue high-potency emollient (petroleum jelly or specialized AD cream)',
        'Oral antihistamine (diphenhydramine 25-50 mg QHS for sleep)',
        'Evaluate for secondary infection; prescribe antibacterial if oozing present',
        'Refer to dermatology if no improvement in 2 weeks'
    ],
    'differential_considerations': [
        'Contact dermatitis - but distribution and history not suggestive',
        'Allergic dermatitis - possible trigger, needs identification',
        'Scabies - excluded by history and lesion morphology',
        'Psoriasis - ruled out (no thick silvery scales, chronic relapsing pattern fits AD)'
    ],
    'prognosis': 'With appropriate management, most patients see improvement within 2-4 weeks. Long-term management requires maintenance of skin barrier and trigger avoidance.',
    'next_assessment_recommended': 'Follow-up in 2 weeks or sooner if worsening. Consider patch testing if contact dermatitis suspected.'
}


def test_user_pdf():
    """Test user report PDF generation"""
    print("Testing User Report PDF Generation...")
    try:
        session_id = str(uuid.uuid4())
        pdf_buffer = PDFGenerator.generate_user_report_pdf(
            session_id=session_id,
            report_data=sample_user_report
        )

        # Verify it's a valid PDF
        pdf_content = pdf_buffer.getvalue()
        if pdf_content.startswith(b'%PDF'):
            print(f"✓ User PDF generated successfully ({len(pdf_content)} bytes)")

            # Save to file for inspection
            output_path = f"/tmp/test_user_report_{session_id}.pdf"
            with open(output_path, 'wb') as f:
                f.write(pdf_content)
            print(f"  Saved to: {output_path}")
            return True
        else:
            print("✗ Invalid PDF format")
            return False

    except Exception as e:
        print(f"✗ Error generating user PDF: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_hcp_pdf():
    """Test HCP report PDF generation"""
    print("\nTesting HCP Report PDF Generation...")
    try:
        session_id = str(uuid.uuid4())
        pdf_buffer = PDFGenerator.generate_hcp_report_pdf(
            session_id=session_id,
            report_data=sample_hcp_report
        )

        # Verify it's a valid PDF
        pdf_content = pdf_buffer.getvalue()
        if pdf_content.startswith(b'%PDF'):
            print(f"✓ HCP PDF generated successfully ({len(pdf_content)} bytes)")

            # Save to file for inspection
            output_path = f"/tmp/test_hcp_report_{session_id}.pdf"
            with open(output_path, 'wb') as f:
                f.write(pdf_content)
            print(f"  Saved to: {output_path}")
            return True
        else:
            print("✗ Invalid PDF format")
            return False

    except Exception as e:
        print(f"✗ Error generating HCP PDF: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("PDF Generation Test Suite")
    print("=" * 60)

    results = []
    results.append(("User Report PDF", test_user_pdf()))
    results.append(("HCP Report PDF", test_hcp_pdf()))

    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")

    all_passed = all(result for _, result in results)
    print("\n" + ("All tests passed!" if all_passed else "Some tests failed!"))
    return 0 if all_passed else 1


if __name__ == '__main__':
    exit(main())
