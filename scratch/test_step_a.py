import requests

BASE_URL = "http://localhost:8000"

def run_tests():
    print("Testing Step A: AI Suggestions, Duplicates, and Support...")

    # 1. Login student1
    res = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "student1@fixflow.demo", "password": "Demo@1234"})
    assert res.status_code == 200, f"Login failed: {res.text}"
    token_s1 = res.json()["access_token"]
    headers_s1 = {"Authorization": f"Bearer {token_s1}"}

    # Login student2
    res = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "student2@fixflow.demo", "password": "Demo@1234"})
    assert res.status_code == 200, f"Login failed: {res.text}"
    token_s2 = res.json()["access_token"]
    headers_s2 = {"Authorization": f"Bearer {token_s2}"}

    # 2. Test AI suggestions endpoint
    test_cases = [
        ("The projector screen in Room 204 is broken and the lamp won't turn on.", "Equipment", "High"),
        ("Live spark and smoke coming out of the electrical wall socket in lab 3.", "Electrical", "Critical"),
        ("There is a continuous water leak from the pipe under the restroom sink.", "Plumbing", "High"),
        ("Dust and dirty floor with garbage scattered near the canteen.", "Cleaning", "Low"),
    ]

    for desc, expected_cat, expected_prio in test_cases:
        res = requests.post(f"{BASE_URL}/api/ai/suggest", json={"description": desc}, headers=headers_s1)
        assert res.status_code == 200, f"Suggest failed: {res.text}"
        data = res.json()
        print(f"[OK] AI suggest for '{desc[:30]}...': {data['category']} / {data['priority']} (conf: {data['confidence']}, src: {data['source']})")
        assert data["category"] == expected_cat, f"Expected {expected_cat}, got {data['category']}"
        assert data["priority"] == expected_prio, f"Expected {expected_prio}, got {data['priority']}"
        assert data["source"] == "rules"
        assert len(data["summary"]) <= 120

    # 3. Test Check Duplicates endpoint
    dup_payload = {
        "category": "Equipment",
        "block": "Block A",
        "room": "Room 204",
        "description": "Projector not working and lamp is dead"
    }
    res = requests.post(f"{BASE_URL}/api/issues/check-duplicates", json=dup_payload, headers=headers_s1)
    assert res.status_code == 200, f"Duplicate check failed: {res.text}"
    dup_data = res.json()
    print(f"[OK] Duplicate check found {len(dup_data['duplicates'])} matches (has_duplicates={dup_data['has_duplicates']})")
    assert dup_data["has_duplicates"] is True
    top_dup = dup_data["duplicates"][0]
    print(f"     Top match: #{top_dup['issue_id']} '{top_dup['title']}' score={top_dup['score']}")
    assert top_dup["score"] >= 0.55

    # 4. Test Support Issue endpoint
    target_issue_id = top_dup["issue_id"]
    # Check issue details first
    res = requests.get(f"{BASE_URL}/api/issues/{target_issue_id}", headers=headers_s1)
    # If s1 is the reporter, testing own issue constraint:
    if res.status_code == 200:
        # S1 is reporter -> should fail with 400
        res_support = requests.post(f"{BASE_URL}/api/issues/{target_issue_id}/support", headers=headers_s1)
        assert res_support.status_code == 400, f"Expected 400 for supporting own issue, got {res_support.status_code}: {res_support.text}"
        print(f"[OK] Blocked reporter from supporting own issue: {res_support.json()['detail']}")

        # S2 is not reporter -> should succeed
        res_support2 = requests.post(f"{BASE_URL}/api/issues/{target_issue_id}/support", headers=headers_s2)
        if res_support2.status_code == 200:
            print(f"[OK] Student 2 supported issue #{target_issue_id}: count is now {res_support2.json()['support_count']}")
            # S2 tries to support again -> should fail with 400
            res_repeat = requests.post(f"{BASE_URL}/api/issues/{target_issue_id}/support", headers=headers_s2)
            assert res_repeat.status_code == 400, f"Expected 400 on duplicate support: {res_repeat.text}"
            print(f"[OK] Blocked duplicate support from same student: {res_repeat.json()['detail']}")
        elif res_support2.status_code == 400:
            print(f"[OK] S2 already supported or condition met: {res_support2.json()['detail']}")

    print("\nALL STEP A TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
