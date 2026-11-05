"""Generate a self-contained, offline progress dashboard from one JSON source."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate(data):
    states = {"active", "blocked", "pending", "partial", "verified"}
    if len(data["milestones"]) != 6:
        raise ValueError("Expected six milestones")
    ids = set()
    for item in data["milestones"] + data["modules"]:
        if item["id"] in ids or item["state"] not in states:
            raise ValueError("Invalid or duplicate progress item")
        ids.add(item["id"])
    for item in data["milestones"]:
        if not item["checks"] or any(type(c["done"]) is not bool for c in item["checks"]):
            raise ValueError("Checks must use explicit boolean outcomes")
    if type(data["tests_passed"]) is not int or data["tests_passed"] < 0:
        raise ValueError("Invalid test count")
    if "tests_run" in data:
        counts = [data["tests_passed"], data.get("tests_expected_failures", 0),
                  data.get("tests_failed", 0), data.get("tests_skipped", 0)]
        if any(type(value) is not int or value < 0 for value in counts):
            raise ValueError("Invalid test outcome count")
        if sum(counts) != data["tests_run"]:
            raise ValueError("Test outcomes must sum to the executed count")
    rollout=data.get('component_rollout')
    if rollout is not None:
        seen=set()
        for phase in rollout['phases']:
            if not phase['checks']:raise ValueError('Empty component rollout phase')
            for check in phase['checks']:
                if check['id'] in seen or type(check['done']) is not bool or not check['acceptance']:
                    raise ValueError('Invalid component rollout check')
                seen.add(check['id'])
        if seen!={f'C{index:02}' for index in range(1,13)}:
            raise ValueError('Expected component rollout checks C01 through C12')


def build():
    data = json.loads((ROOT / "docs/progress.json").read_text(encoding="utf-8"))
    validate(data)
    template = (ROOT / "scripts/progress-template.html").read_text(encoding="utf-8")
    # Prevent a future label from terminating the embedded JSON script element.
    encoded = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    return template.replace("__PROGRESS_DATA__", encoded)


if __name__ == "__main__":
    target = ROOT / "docs/progress.html"
    target.write_text(build(), encoding="utf-8")
    print(target)
