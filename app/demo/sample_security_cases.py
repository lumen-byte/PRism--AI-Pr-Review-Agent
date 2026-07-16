SECURITY_DIFF = """@@ -1,15 +1,15 @@
 import sqlite3

 def get_user_data(user_id):
-    # Use safe parameterized query
-    pass
+    # Raw SQL injection vulnerability
+    conn = sqlite3.connect("users.db")
+    cursor = conn.cursor()
+    query = f"SELECT * FROM users WHERE id = '{user_id}'"
+    cursor.execute(query)
+    return cursor.fetchall()
+
+def login(username, password):
+    # Hardcoded sensitive credentials
+    admin_pass = "super_secret_password_12345"
+    if username == "admin" and password == admin_pass:
+        return True
+    return False
"""

SECURITY_CONTENTS = {
    "app/security_vuln.py": """import sqlite3

def get_user_data(user_id):
    # Raw SQL injection vulnerability
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE id = '{user_id}'"
    cursor.execute(query)
    return cursor.fetchall()

def login(username, password):
    # Hardcoded sensitive credentials
    admin_pass = "super_secret_password_12345"
    if username == "admin" and password == admin_pass:
        return True
    return False
"""
}
