LOGIC_DIFF = """@@ -1,15 +1,15 @@
-def process_scores(scores):
-    return sum(scores) / len(scores)
+def process_scores(scores):
+    # Potential division by zero logic error
+    # Also array indexing out of bounds
+    average = sum(scores) / len(scores)
+    highest = scores[10]
+    return average, highest
+
+def calculate_discount(price, user_type):
+    # Infinite recursion logic bug
+    if user_type == "VIP":
+        return calculate_discount(price, "VIP")
+    return price * 0.95
"""

LOGIC_CONTENTS = {
    "app/logic_errors.py": """def process_scores(scores):
    # Potential division by zero logic error
    # Also array indexing out of bounds
    average = sum(scores) / len(scores)
    highest = scores[10]
    return average, highest

def calculate_discount(price, user_type):
    # Infinite recursion logic bug
    if user_type == "VIP":
        return calculate_discount(price, "VIP")
    return price * 0.95
"""
}
