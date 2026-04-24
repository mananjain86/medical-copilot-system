#!/usr/bin/env python3
"""
API Testing Script
Tests the Medical Copilot API endpoints
"""

import requests
import json
import sys

def test_api(base_url="http://localhost:8000"):
    """Test all API endpoints."""
    
    print("=" * 60)
    print("Medical Copilot API Test")
    print("=" * 60)
    print(f"\nTesting API at: {base_url}\n")
    
    results = []
    
    # Test 1: Health Check
    print("Test 1: Health Check")
    print("-" * 40)
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"GET {base_url}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ PASS\n")
            results.append(("Health Check", True))
        else:
            print("❌ FAIL\n")
            results.append(("Health Check", False))
    except Exception as e:
        print(f"❌ FAIL - Error: {e}\n")
        results.append(("Health Check", False))
    
    # Test 2: Patient Search
    print("Test 2: Patient Search")
    print("-" * 40)
    try:
        payload = {
            "user_id": 1,
            "query": "female patients over 60"
        }
        response = requests.post(
            f"{base_url}/api/v1/search",
            json=payload,
            timeout=30
        )
        print(f"POST {base_url}/api/v1/search")
        print(f"Body: {json.dumps(payload)}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            results_count = len(data.get("results", []))
            print(f"Results: {results_count} patients found")
            print("✅ PASS\n")
            results.append(("Patient Search", True))
        else:
            print(f"Response: {response.text[:200]}")
            print("❌ FAIL\n")
            results.append(("Patient Search", False))
    except Exception as e:
        print(f"❌ FAIL - Error: {e}\n")
        results.append(("Patient Search", False))
    
    # Test 3: Search History
    print("Test 3: Search History")
    print("-" * 40)
    try:
        response = requests.get(f"{base_url}/api/v1/history/1", timeout=10)
        print(f"GET {base_url}/api/v1/history/1")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"History entries: {len(data)}")
            print("✅ PASS\n")
            results.append(("Search History", True))
        else:
            print(f"Response: {response.text[:200]}")
            print("❌ FAIL\n")
            results.append(("Search History", False))
    except Exception as e:
        print(f"❌ FAIL - Error: {e}\n")
        results.append(("Search History", False))
    
    # Test 4: Cohorts List
    print("Test 4: Cohorts List")
    print("-" * 40)
    try:
        response = requests.get(f"{base_url}/api/v1/cohorts", timeout=10)
        print(f"GET {base_url}/api/v1/cohorts")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Cohorts: {len(data)}")
            print("✅ PASS\n")
            results.append(("Cohorts List", True))
        else:
            print(f"Response: {response.text[:200]}")
            print("❌ FAIL\n")
            results.append(("Cohorts List", False))
    except Exception as e:
        print(f"❌ FAIL - Error: {e}\n")
        results.append(("Cohorts List", False))
    
    # Test 5: Various Queries
    print("Test 5: Various Search Queries")
    print("-" * 40)
    
    queries = [
        "diabetic patients",
        "male patients with hypertension",
        "patients in cardiology"
    ]
    
    query_results = []
    for query in queries:
        try:
            payload = {"user_id": 1, "query": query}
            response = requests.post(
                f"{base_url}/api/v1/search",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"✅ '{query}' - PASS")
                query_results.append(True)
            else:
                print(f"❌ '{query}' - FAIL (Status: {response.status_code})")
                query_results.append(False)
        except Exception as e:
            print(f"❌ '{query}' - FAIL (Error: {e})")
            query_results.append(False)
    
    all_queries_pass = all(query_results)
    results.append(("Various Queries", all_queries_pass))
    print()
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    # Get API URL from command line or use default
    api_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print("\nUsage:")
    print("  Test locally:  python test_api.py")
    print("  Test deployed: python test_api.py https://your-app.onrender.com")
    print()
    
    exit_code = test_api(api_url)
    sys.exit(exit_code)
