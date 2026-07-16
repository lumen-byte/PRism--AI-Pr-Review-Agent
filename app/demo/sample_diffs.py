from app.demo.sample_pull_requests import CLEAN_DIFF, SCENARIOS

# Exporting diffs dictionary
DIFFS = {
    "clean": CLEAN_DIFF,
    "security": SCENARIOS["security"]["raw_diff"],
    "quality": SCENARIOS["quality"]["raw_diff"],
    "logic": SCENARIOS["logic"]["raw_diff"],
    "mixed": SCENARIOS["mixed"]["raw_diff"],
}
