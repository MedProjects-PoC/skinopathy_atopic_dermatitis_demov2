#!/usr/bin/env python3
"""
Comprehensive Test Script for AD Multi-Agent API
Tests updated Gemini 2.5 models and new service configuration
"""
import requests
import time
import json
import base64
from pathlib import Path
from typing import Optional, Dict
import sys

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TEST_IMAGE = Path("/Users/rakesh/Desktop/GIT/skinopathy_atopic_dermatitis_demov2/storage/images/f99a70aa-e794-4423-aa8f-cb44c0656381.jpg")

# Complete questionnaire data with all required fields
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
    "duration_current_flare_days": 14,
    "steroid_use_last_2weeks": True,
    "moisturizer_frequency": "once_daily"
}


def print_header(text: str, char: str = "=") -> None:
    """Print a formatted header"""
    print(f"\n{char * 80}")
    print(f"  {text}")
    print(f"{char * 80}\n")


def print_step(step: int, total: int, description: str) -> None:
    """Print a step indicator"""
    print(f"[{step}/{total}] {description}")


def check_server_health() -> bool:
    """Test the health endpoint"""
    print_step(1, 5, "Checking server health...")
    try:
        response = requests.get(f"{API_BASE_URL.replace('/api/v1', '')}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server is healthy")
            print(f"   Status: {data.get('status')}")
            print(f"   Version: {data.get('version')}")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Server not reachable at {API_BASE_URL}")
        print(f"   Make sure the backend is running:")
        print(f"   cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000")
        return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def verify_test_image() -> bool:
    """Verify test image exists"""
    print_step(2, 5, "Verifying test image...")
    if not TEST_IMAGE.exists():
        print(f"❌ Test image not found: {TEST_IMAGE}")
        return False

    size_mb = TEST_IMAGE.stat().st_size / (1024 * 1024)
    print(f"✅ Test image found: {TEST_IMAGE.name}")
    print(f"   Size: {size_mb:.2f} MB")
    return True


def upload_test_case() -> Optional[str]:
    """Upload image and questionnaire"""
    print_step(3, 5, "Uploading test case...")

    try:
        # Read and encode image
        with open(TEST_IMAGE, 'rb') as img_file:
            image_data = img_file.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')

        print(f"   Base64 image size: {len(base64_image)} characters")

        # Create payload
        payload = {
            "image": base64_image,
            "questionnaire": QUESTIONNAIRE_DATA
        }

        # Upload with extended timeout
        print(f"   Uploading to: {API_BASE_URL}/upload/")
        response = requests.post(
            f"{API_BASE_URL}/upload/",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60  # Extended timeout for large image
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

    except requests.exceptions.Timeout:
        print(f"❌ Upload timeout (60 seconds)")
        print(f"   The upload may still be processing in the background")
        print(f"   Check backend logs for session ID")
        return None
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return None


def poll_analysis(session_id: str, max_attempts: int = 50, interval: int = 3) -> Optional[Dict]:
    """Poll for analysis results"""
    print_step(4, 5, f"Polling analysis status (max {max_attempts} attempts, {interval}s interval)...")

    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(
                f"{API_BASE_URL}/analysis/{session_id}",
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                status = result.get('status')

                # Show progress
                if attempt % 5 == 0 or status in ['completed', 'failed']:
                    print(f"   Attempt {attempt}/{max_attempts}: Status = {status}")

                if status == 'completed':
                    print(f"\n✅ Analysis COMPLETED in {attempt * interval} seconds!")
                    return result
                elif status == 'failed':
                    print(f"\n❌ Analysis FAILED!")
                    print(f"   Error: {result.get('error', 'Unknown error')}")
                    return result
                elif status in ['processing', 'pending']:
                    time.sleep(interval)
                    continue
            else:
                if attempt % 10 == 0:
                    print(f"   ⚠️  HTTP {response.status_code}: {response.text[:100]}")
                time.sleep(interval)

        except Exception as e:
            if attempt % 10 == 0:
                print(f"   ⚠️  Poll error: {e}")
            time.sleep(interval)

    print(f"\n⏱️  Timeout after {max_attempts * interval} seconds")
    return None


def display_detailed_results(result: Dict) -> Dict:
    """Display comprehensive analysis results"""
    print_step(5, 5, "Analysis Results")

    if not result:
        print("❌ No results to display")
        return {"success": False}

    status = result.get('status')
    print(f"\nOverall Status: {status}")

    if status == 'failed':
        print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
        return {"success": False}

    # Test results tracking
    test_results = {
        "success": True,
        "vision_agent": False,
        "easi_agent": False,
        "cnn": False,
        "reports": False
    }

    # CNN Results
    print("\n" + "─" * 80)
    print("📊 CNN Analysis")
    print("─" * 80)
    cnn_results = result.get('cnn_results', {})
    if cnn_results:
        test_results["cnn"] = True
        print(f"Severity Score:       {cnn_results.get('severity_score', 'N/A')}")
        print(f"Affected Area:        {cnn_results.get('affected_area_pct', 'N/A')}%")
        print(f"Inflammation:         {cnn_results.get('inflammation_score', 'N/A')}")
        print(f"Flare Status:         {cnn_results.get('flare_status', 'N/A')}")
        print(f"CNN Confidence:       {cnn_results.get('cnn_confidence', 'N/A')}")
    else:
        print("❌ No CNN results")

    # Vision Agent Results (Gemini 2.5)
    print("\n" + "─" * 80)
    print("👁️  Vision Agent Analysis (Gemini 2.5 Flash)")
    print("─" * 80)
    vision_results = result.get('vision_agent_results')
    if vision_results and isinstance(vision_results, dict):
        test_results["vision_agent"] = True
        print("✅ SUCCESS")

        findings = vision_results.get('findings', 'N/A')
        if isinstance(findings, str) and len(findings) > 200:
            print(f"\nFindings (preview):\n{findings[:200]}...")
        else:
            print(f"\nFindings:\n{findings}")

        if 'confidence' in vision_results:
            print(f"\nConfidence: {vision_results['confidence']}")
    else:
        print("❌ FAILED or NO DATA")
        test_results["vision_agent"] = False
        test_results["success"] = False

    # EASI Agent Results (Gemini 2.5)
    print("\n" + "─" * 80)
    print("📋 EASI Scoring Agent (Gemini 2.5 Flash)")
    print("─" * 80)
    easi_results = result.get('easi_results')
    if easi_results and isinstance(easi_results, dict):
        test_results["easi_agent"] = True
        print("✅ SUCCESS")

        easi_score = easi_results.get('total_easi_score', 'N/A')
        severity = easi_results.get('severity_interpretation', 'N/A')
        print(f"\nTotal EASI Score:     {easi_score}")
        print(f"Severity:             {severity}")

        # Body region scores
        regions = easi_results.get('body_region_scores', {})
        if regions:
            print(f"\nBody Region Scores:")
            for region, score in regions.items():
                print(f"  {region:12s}: {score}")
    else:
        print("❌ FAILED or NO DATA")
        test_results["easi_agent"] = False
        test_results["success"] = False

    # Reports
    print("\n" + "─" * 80)
    print("📄 Generated Reports")
    print("─" * 80)
    user_report = result.get('user_report_url')
    hcp_report = result.get('hcp_report_url')

    if user_report or hcp_report:
        test_results["reports"] = True
        if user_report:
            print(f"User Report:  {user_report}")
        if hcp_report:
            print(f"HCP Report:   {hcp_report}")
    else:
        print("⚠️  No reports generated")

    # Saliency Map
    saliency_map = result.get('saliency_map_url')
    if saliency_map:
        print(f"\n🗺️  Saliency Map: {saliency_map}")

    # Cost
    cost = result.get('estimated_cost', 0)
    print(f"\n💰 Estimated Cost: ${cost:.6f}")

    return test_results


def print_test_summary(test_results: Dict) -> None:
    """Print test summary"""
    print_header("TEST SUMMARY")

    if test_results.get("success"):
        print("✅ Upload:              SUCCESS")
        print(f"{'✅' if test_results['cnn'] else '❌'} CNN Analysis:        {'SUCCESS' if test_results['cnn'] else 'FAILED'}")
        print(f"{'✅' if test_results['vision_agent'] else '❌'} Vision Agent (2.5):  {'SUCCESS' if test_results['vision_agent'] else 'FAILED'}")
        print(f"{'✅' if test_results['easi_agent'] else '❌'} EASI Agent (2.5):    {'SUCCESS' if test_results['easi_agent'] else 'FAILED'}")
        print(f"{'✅' if test_results['reports'] else '⚠️'} Reports:             {'SUCCESS' if test_results['reports'] else 'PARTIAL'}")

        if test_results['vision_agent'] and test_results['easi_agent']:
            print("\n🎉 ALL TESTS PASSED!")
            print("   Gemini 2.5 models are working correctly")
            print("   System is ready for deployment")
        else:
            print("\n⚠️  PARTIAL SUCCESS")
            print("   Some agents failed - check logs for details")
    else:
        print("❌ TEST FAILED")
        print("   Check backend logs for error details")


def main():
    """Run comprehensive system test"""
    print_header("SKINOPATHY AD MULTI-AGENT SYSTEM TEST", "=")
    print("Testing Gemini 2.5 Flash Models")
    print("Configuration: Updated service names for deployment")

    # Step 1: Health check
    if not check_server_health():
        print_header("TEST ABORTED - Server Not Available", "!")
        sys.exit(1)

    # Step 2: Verify test image
    if not verify_test_image():
        print_header("TEST ABORTED - Test Image Not Found", "!")
        sys.exit(1)

    # Step 3: Upload
    session_id = upload_test_case()
    if not session_id:
        print_header("TEST FAILED - Upload Failed", "!")
        sys.exit(1)

    # Step 4: Poll for results
    result = poll_analysis(session_id, max_attempts=50, interval=3)

    # Step 5: Display results
    test_results = display_detailed_results(result)

    # Summary
    print_test_summary(test_results)

    print("\n" + "=" * 80)

    # Exit code
    if test_results.get("success") and test_results.get("vision_agent") and test_results.get("easi_agent"):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
