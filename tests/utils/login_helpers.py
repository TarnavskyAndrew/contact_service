import csv
import pathlib
from typing import List, Dict


def load_cases(filename: str) -> List[Dict]:
    """
    Load test cases from CSV file.

    Required columns:
        - email
        - password
        - expected_status
        - expected_msg

    Optional columns:
        - case_id : unique identifier for the test case.
        - description   : logical description name (e.g. 'email', 'password').

    Notes:
        - File must start with a header row.
        - Spaces around values are stripped automatically.
        - Raises ValueError if required columns are missing.
    """
    path = pathlib.Path(__file__).parent.parent / "data" / filename

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        # normalize header fieldnames
        if reader.fieldnames:
            reader.fieldnames = [h.strip() for h in reader.fieldnames]

        required = {"email", "password", "expected_status", "expected_msg"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing columns in {filename}: {missing}")

        cases: List[Dict] = []
        for row in reader:

            case = {
                "email": row["email"].strip(),
                "password": row["password"].strip(),
                "expected_status": int(row["expected_status"].strip()),
                "expected_msg": row["expected_msg"].strip(),
            }
            if "case_id" in row:
                case["id"] = row["case_id"].strip()
            if "description" in row:
                case["description"] = row["description"].strip()

            cases.append(case)

    return cases


def make_id(case: Dict) -> str:
    """
    Generate a readable pytest ID for a given case.

    Format:
        "<case_id>-<description>" if present,
        otherwise "<expected_status>-<email>".
    """

    cid = case.get("id") or case.get("case_id")
    desc = case.get("description", "")
    if cid and desc:
        # Example: B05-empty_email
        return f"{cid}-{desc.replace(' ', '_').lower()}"
    if cid:
        return cid
    return f"{case['expected_status']}-{case['email']}"
