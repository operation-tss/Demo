import re
from typing import List, Tuple, Optional
from ..schemas.report_schema import TestResult, Summary

def normalize_number_string(val_str: str) -> str:
    """
    Normalizes numeric string:
    - Distinguishes thousands separator (e.g. 150,000 -> 150000)
    - Distinguishes decimal comma (e.g. 3,9 -> 3.9, 10,5 -> 10.5)
    """
    if not val_str:
        return ""
    s = val_str.strip()
    # If comma is followed by exactly 3 digits and non-digit: thousands separator
    s = re.sub(r"(\d+),(\d{3})(?!\d)", r"\1\2", s)
    # If comma is between numbers (e.g. 3,9 or 12,0): decimal comma
    s = re.sub(r"(\d+),(\d+)", r"\1.\2", s)
    return s

def clean_num(val_str: str) -> Optional[float]:
    """Cleans commas, spaces, inequalities and parses float."""
    try:
        norm = normalize_number_string(val_str)
        cleaned = re.sub(r"[^\d\.]", "", norm)
        if cleaned:
            return float(cleaned)
    except Exception:
        pass
    return None

def parse_range(ref_str: str) -> Tuple[Optional[float], Optional[float], bool]:
    """
    Parses a reference range string into (min_val, max_val, is_valid).
    Supports:
      - "13.0 - 17.0", "13.0 to 17.0", "13.0 – 17.0"
      - "< 200", "<= 200", "Up to 200", "Less than 200"
      - "> 40", ">= 40", "More than 40"
    """
    if not ref_str:
        return None, None, False

    clean_ref = normalize_number_string(ref_str.strip())

    # Check for two-sided range: min - max
    two_sided = re.search(r"(\d+(?:\.\d+)?)\s*(?:-|–|to)\s*(\d+(?:\.\d+)?)", clean_ref, re.IGNORECASE)
    if two_sided:
        try:
            min_v = float(two_sided.group(1))
            max_v = float(two_sided.group(2))
            return min_v, max_v, True
        except ValueError:
            pass

    # Check for upper bound: < X, <= X, Up to X
    upper_bound = re.search(r"(?:<|<=|up\s+to|less\s+than)\s*(\d+(?:\.\d+)?)", clean_ref, re.IGNORECASE)
    if upper_bound:
        try:
            max_v = float(upper_bound.group(1))
            return 0.0, max_v, True
        except ValueError:
            pass

    # Check for lower bound: > X, >= X, More than X
    lower_bound = re.search(r"(?:>|>=|more\s+than)\s*(\d+(?:\.\d+)?)", clean_ref, re.IGNORECASE)
    if lower_bound:
        try:
            min_v = float(lower_bound.group(1))
            return min_v, None, True
        except ValueError:
            pass

    return None, None, False

def analyze_test_result(item: TestResult) -> TestResult:
    """
    Applies strict rule-based logic to classify a test result as LOW, HIGH, NORMAL, or NEEDS REVIEW.
    Preserves original extracted values and respect printed reference ranges.
    """
    val_str = item.value.strip()
    ref_str = (item.reference_range or "").strip()

    # 1. Check for qualitative tests (e.g. Urine analysis, Serology)
    qualitative_normal_tokens = ["negative", "nil", "absent", "non-reactive", "normal", "clear", "yellow", "straw", "sinus rhythm", "unremarkable"]
    qualitative_abnormal_tokens = ["positive", "trace", "reactive", "present", "cloudy", "turbid", "1+", "2+", "3+", "4+"]

    lower_val = val_str.lower()
    lower_ref = ref_str.lower()

    if any(q == lower_val for q in qualitative_normal_tokens):
        item.status = "NORMAL"
        return item
    if any(q in lower_val for q in qualitative_abnormal_tokens):
        item.status = "HIGH"
        return item

    # 2. Check for ranges in values themselves (e.g. Pus cells: "8-10" or "0-2")
    val_range_match = re.search(r"(\d+)\s*(?:-|–|to)\s*(\d+)", val_str)
    if val_range_match:
        val_min = float(val_range_match.group(1))
        val_max = float(val_range_match.group(2))
        min_r, max_r, valid_r = parse_range(ref_str)
        if valid_r:
            if max_r is not None and val_max > max_r:
                item.status = "HIGH"
            elif min_r is not None and val_min < min_r:
                item.status = "LOW"
            else:
                item.status = "NORMAL"
            return item

    # 3. Numeric comparison
    num_val = clean_num(val_str)
    if num_val is None:
        # Cannot parse numeric value and not a recognized qualitative result
        item.status = "NEEDS REVIEW"
        return item

    min_r, max_r, valid_r = parse_range(ref_str)
    if not valid_r:
        # If printed flag exists, use it
        if item.flag in ["HIGH", "H", "*"]:
            item.status = "HIGH"
        elif item.flag in ["LOW", "L"]:
            item.status = "LOW"
        else:
            item.status = "NEEDS REVIEW"
        return item

    # Evaluate against parsed reference range
    if min_r is not None and num_val < min_r:
        item.status = "LOW"
    elif max_r is not None and num_val > max_r:
        item.status = "HIGH"
    elif (min_r is None or num_val >= min_r) and (max_r is None or num_val <= max_r):
        item.status = "NORMAL"
    else:
        item.status = "NEEDS REVIEW"

    return item

def generate_findings_and_summary(results: List[TestResult]) -> Tuple[List[str], Summary]:
    """
    Produces deterministic, rule-based summary statements and aggregates status counts.
    Generates NO medical diagnoses or disease attributions.
    """
    summary = Summary(total_parameters=len(results))
    findings: List[str] = []
    normal_count = 0

    for res in results:
        status = res.status
        if status == "LOW":
            summary.low += 1
            unit_str = f" {res.unit}" if res.unit else ""
            range_str = f" (Reference: {res.reference_range}{unit_str})" if res.reference_range else ""
            findings.append(f"{res.test_name} ({res.value}{unit_str}) is below the reference range{range_str}.")
        elif status == "HIGH":
            summary.high += 1
            unit_str = f" {res.unit}" if res.unit else ""
            range_str = f" (Reference: {res.reference_range}{unit_str})" if res.reference_range else ""
            findings.append(f"{res.test_name} ({res.value}{unit_str}) is above the reference range{range_str}.")
        elif status == "NORMAL":
            summary.normal += 1
            normal_count += 1
        else:
            summary.needs_review += 1

    if normal_count > 0:
        if normal_count == len(results):
            findings.append("All analyzed parameters are within their stated reference ranges.")
        else:
            findings.append(f"{normal_count} parameter(s) are within normal reference ranges.")

    if summary.needs_review > 0:
        findings.append(f"{summary.needs_review} parameter(s) require manual review due to ambiguous format or missing reference range.")

    return findings, summary
