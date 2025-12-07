import psycopg2
import os
from datetime import datetime, timedelta

# Connect to Cloud SQL via proxy (should be running on port 5433)
conn = psycopg2.connect(
    host="localhost",
    port=5433,
    database="skinopathy_ad",
    user="skinopathy",
    password=os.environ.get('DB_PASSWORD', 'mDXuee87pdmFyfTm1hGb1fbp7WM/TlrVm+B8EEHbaZE=')
)

cur = conn.cursor()

# Get last 10 sessions with their analysis status
print("\n=== Recent Sessions (Last 10) ===\n")
cur.execute("""
    SELECT 
        s.id,
        s.created_at,
        s.status,
        CASE WHEN ai.id IS NOT NULL THEN 'YES' ELSE 'NO' END as has_ai_result,
        CASE WHEN r.id IS NOT NULL THEN 'YES' ELSE 'NO' END as has_hcp_report,
        ai.saliency_map_path
    FROM sessions s
    LEFT JOIN ai_results ai ON s.id = ai.session_id
    LEFT JOIN reports r ON s.id = r.session_id AND r.report_type = 'hcp'
    ORDER BY s.created_at DESC
    LIMIT 10
""")

rows = cur.fetchall()
for row in rows:
    session_id, created_at, status, has_ai, has_report, saliency_path = row
    print(f"Session ID: {session_id}")
    print(f"  Created: {created_at}")
    print(f"  Status: {status}")
    print(f"  Has AI Result: {has_ai}")
    print(f"  Has HCP Report: {has_report}")
    print(f"  Saliency Map Path: {saliency_path or 'None'}")
    print()

cur.close()
conn.close()
