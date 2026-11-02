import sys

from evals.cases import cases
from evals.compare import run_case

minimum_score_percent = 80


def run_all_cases():
    passed_count = 0

    for case in cases:
        passed, note = run_case(case)

        if passed:
            passed_count = passed_count + 1
            print("PASS", case["name"])
        else:
            print("FAIL", case["name"])
            print("     ", note)

    return passed_count


if __name__ == "__main__":
    passed_count = run_all_cases()
    total_count = len(cases)
    score_percent = round(100 * passed_count / total_count)

    print()
    print(f"Score: {passed_count} of {total_count} ({score_percent}%)")

    if score_percent < minimum_score_percent:
        print(f"Below the minimum of {minimum_score_percent}%.")
        sys.exit(1)