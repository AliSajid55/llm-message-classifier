import json
import httpx
from pathlib import Path

CASES_FILE = Path(__file__).parent / "cases.json"
ENDPOINT = "http://localhost:8000/triage"


def run_eval(prompt_version="v1"):
    with open(CASES_FILE, "r", encoding="utf-8") as f:
        cases = json.load(f)

    passed = 0
    failed = []

    for i, case in enumerate(cases):
        text = case["text"]
        expected = case["expected"]

        try:
            r = httpx.post(ENDPOINT, json={"text": text}, timeout=60)
            result = r.json()

            category_match = result.get("category") == expected.get("category")
            urgency_match = result.get("urgency") == expected.get("urgency")

            if category_match and urgency_match:
                passed += 1
                status = "PASS"
            else:
                status = "FAIL"
                failed.append({
                    "input": text,
                    "expected": expected,
                    "got": result,
                })

            print(f"Case {i+1}: {status}")
            print(f"  Input: {text[:50]}...")
            print(f"  Expected: {expected}")
            print(f"  Got: category={result.get('category')}, urgency={result.get('urgency')}")
            print()

        except Exception as e:
            print(f"Case {i+1}: ERROR - {e}")
            failed.append({
                "input": text,
                "expected": expected,
                "error": str(e),
            })

    total = len(cases)
    score = f"{passed}/{total}"
    percentage = round((passed / total) * 100, 1)

    print("=" * 50)
    print(f"Prompt: {prompt_version}")
    print(f"Score: {score} ({percentage}%)")
    print(f"Passed: {passed}, Failed: {len(failed)}")

    if failed:
        print("\nFailed cases:")
        for f_item in failed:
            print(f"  - {f_item['input'][:40]}...")

    return score, percentage, failed


if __name__ == "__main__":
    import sys
    version = sys.argv[1] if len(sys.argv) > 1 else "v1"
    run_eval(version)
