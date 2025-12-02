#!/usr/bin/env python3
"""
Test script for AD Multi-Agent API
Tests the updated Gemini 2.5 models
"""
import requests
import time
import json
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TEST_IMAGE = Path("/Users/rakesh/Desktop/GIT/skinopathy_atopic_dermatitis_demov2/storage/images/f99a70aa-e794-4423-aa8f-cb44c0656381.jpg")

# Mock questionnaire data
QUESTIONNAIRE_DATA = {
    "itch_intensity": 7,
    "nights_sleep_disturbed": 5,
    "chronic_relapsing": True,
    "atopic_triad_history": True,
    "oozing_honey_crusts": False,
    "thick_silvery_scales": False,
    "household_itchy_or_nighttime_worse": False,
    "new_exposure_trigger": False,
    "primary_location": "flexural",
    "recent_stress_level": 6,
    "age": 35,
    "duration_current_flare_days": 14
}


def test_upload():
    """Test the upload endpoint"""
    print("=" * 80)
    print("TESTING AD MULTI-AGENT API WITH GEMINI 2.5")
    print("=" * 80)

    # Check if server is running
    try:
        health_response = requests.get(f"{API_BASE_URL.replace('/api/v1', '')}/health", timeout=5)
        print(f"✅ Server health check: {health_response.json()}")
    except Exception as e:
        print(f"❌ Server not reachable: {e}")
        return None

    # Prepare upload
    if not TEST_IMAGE.exists():
        print(f"❌ Test image not found: {TEST_IMAGE}")
        return None

    print(f"\n📤 Uploading test image: {TEST_IMAGE.name}")
    print(f"📋 Questionnaire data: {json.dumps(QUESTIONNAIRE_DATA, indent=2)}")

    # Upload image and questionnaire
    try:
        with open(TEST_IMAGE, 'rb') as img_file:
            files = {'file': (TEST_IMAGE.name, img_file, 'image/jpeg')}
            data = {'questionnaire': json.dumps(QUESTIONNAIRE_DATA)}

            response = requests.post(
                f"{API_BASE_URL}/upload/",
                files=files,
                data=data,
                timeout=30
            )

        if response.status_code == 200:
            result = response.json()
            session_id = result.get('session_id')
            print(f"✅ Upload successful!")
            print(f"   Session ID: {session_id}")
            print(f"   Status: {result.get('status')}")
            return session_id
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Upload error: {e}")
        return None


def poll_analysis(session_id, max_attempts=30, interval=3):
    """Poll the analysis endpoint until complete"""
    print(f"\n🔄 Polling analysis status (max {max_attempts} attempts, {interval}s interval)...")

    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(
                f"{API_BASE_URL}/analysis/{session_id}",
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                status = result.get('status')

                print(f"   Attempt {attempt}: Status = {status}")

                if status == 'completed':
                    print(f"\n✅ Analysis COMPLETED!")
                    return result
                elif status == 'failed':
                    print(f"\n❌ Analysis FAILED!")
                    print(f"   Error: {result.get('error', 'Unknown error')}")
                    return result
                elif status in ['processing', 'pending']:
                    time.sleep(interval)
                    continue
            else:
                print(f"   ⚠️  HTTP {response.status_code}: {response.text}")
                time.sleep(interval)

        except Exception as e:
            print(f"   ⚠️  Poll error: {e}")
            time.sleep(interval)

    print(f"\n⏱️  Timeout after {max_attempts} attempts")
    return None


def display_results(result):
    """Display the analysis results"""
    print("\n" + "=" * 80)
    print("ANALYSIS RESULTS")
    print("=" * 80)

    if not result:
        print("❌ No results to display")
        return

    status = result.get('status')
    print(f"Status: {status}")

    if status == 'failed':
        print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
        return

    # CNN Results
    cnn_results = result.get('cnn_results', {})
    if cnn_results:
        print(f"\n📊 CNN Analysis:")
        print(f"   Severity Score: {cnn_results.get('severity_score', 'N/A')}")
        print(f"   Affected Area: {cnn_results.get('affected_area_pct', 'N/A')}%")
        print(f"   Flare Status: {cnn_results.get('flare_status', 'N/A')}")
        print(f"   Confidence: {cnn_results.get('cnn_confidence', 'N/A')}")

    # Vision Agent Results
    vision_results = result.get('vision_agent_results')
    if vision_results:
        print(f"\n👁️  Vision Agent (Gemini 2.5):")
        if isinstance(vision_results, dict):
            print(f"   Status: ✅ SUCCESS")
            findings = vision_results.get('findings', 'N/A')
            if isinstance(findings, str):
                print(f"   Findings: {findings[:200]}...")
            else:
                print(f"   Findings: {findings}")
        else:
            print(f"   Status: ❌ FAILED or NO DATA")
            print(f"   Response: {vision_results}")
    else:
        print(f"\n👁️  Vision Agent: ❌ NO RESULTS")

    # EASI Results
    easi_results = result.get('easi_results')
    if easi_results:
        print(f"\n📋 EASI Scoring Agent (Gemini 2.5):")
        if isinstance(easi_results, dict):
            print(f"   Status: ✅ SUCCESS")
            easi_score = easi_results.get('total_easi_score', 'N/A')
            severity = easi_results.get('severity_interpretation', 'N/A')
            print(f"   EASI Score: {easi_score}")
            print(f"   Severity: {severity}")
        else:
            print(f"   Status: ❌ FAILED or NO DATA")
            print(f"   Response: {easi_results}")
    else:
        print(f"\n📋 EASI Agent: ❌ NO RESULTS")

    # Saliency Map
    saliency_map = result.get('saliency_map_url')
    if saliency_map:
        print(f"\n🗺️  Saliency Map: {saliency_map}")

    # Reports
    user_report = result.get('user_report_url')
    hcp_report = result.get('hcp_report_url')
    if user_report:
        print(f"\n📄 User Report: {user_report}")
    if hcp_report:
        print(f"📄 HCP Report: {hcp_report}")

    # Cost
    cost = result.get('estimated_cost', 0)
    print(f"\n💰 Estimated Cost: ${cost:.6f}")

    print("\n" + "=" * 80)


def main():
    """Run the complete test"""
    # Step 1: Upload
    session_id = test_upload()
    if not session_id:
        print("\n❌ Test failed at upload stage")
        return

    # Step 2: Poll for results
    result = poll_analysis(session_id, max_attempts=40, interval=3)

    # Step 3: Display results
    display_results(result)

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    if result and result.get('status') == 'completed':
        vision_ok = bool(result.get('vision_agent_results'))
        easi_ok = bool(result.get('easi_results'))

        print(f"✅ Upload: SUCCESS")
        print(f"{'✅' if vision_ok else '❌'} Vision Agent (Gemini 2.5): {'SUCCESS' if vision_ok else 'FAILED'}")
        print(f"{'✅' if easi_ok else '❌'} EASI Agent (Gemini 2.5): {'SUCCESS' if easi_ok else 'FAILED'}")

        if vision_ok and easi_ok:
            print(f"\n🎉 ALL TESTS PASSED! Gemini 2.5 models are working correctly.")
        else:
            print(f"\n⚠️  PARTIAL SUCCESS: Some agents failed. Check logs for details.")
    else:
        print(f"❌ TEST FAILED")

    print("=" * 80)


if __name__ == "__main__":
    main()
