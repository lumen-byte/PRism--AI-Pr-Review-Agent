QUALITY_DIFF = """@@ -1,25 +1,30 @@
-def calculate_total(price, tax):
-    return price + (price * tax)
+def Calculate_Total_Value_Of_Items_In_Cart_For_Customer(Items_List, Tax_Rate, Discount_Code):
+    # Deeply nested logic and naming smell
+    Total = 0
+    for Item in Items_List:
+        if Item is not None:
+            if Item.price > 0:
+                if Item.active:
+                    if Discount_Code == "SAVE10":
+                        Total += Item.price * 0.9
+                    elif Discount_Code == "SAVE20":
+                        Total += Item.price * 0.8
+                    else:
+                        Total += Item.price
+    return Total + (Total * Tax_Rate)
+
+def Calculate_Total_Value_Of_Items_In_Cart_For_Guest(Items_List, Tax_Rate, Discount_Code):
+    # Duplicate block smell
+    Total = 0
+    for Item in Items_List:
+        if Item is not None:
+            if Item.price > 0:
+                if Item.active:
+                    if Discount_Code == "SAVE10":
+                        Total += Item.price * 0.9
+                    elif Discount_Code == "SAVE20":
+                        Total += Item.price * 0.8
+                    else:
+                        Total += Item.price
+    return Total + (Total * Tax_Rate)
"""

QUALITY_CONTENTS = {
    "app/quality_smells.py": """def Calculate_Total_Value_Of_Items_In_Cart_For_Customer(Items_List, Tax_Rate, Discount_Code):
    # Deeply nested logic and naming smell
    Total = 0
    for Item in Items_List:
        if Item is not None:
            if Item.price > 0:
                if Item.active:
                    if Discount_Code == "SAVE10":
                        Total += Item.price * 0.9
                    elif Discount_Code == "SAVE20":
                        Total += Item.price * 0.8
                    else:
                        Total += Item.price
    return Total + (Total * Tax_Rate)

def Calculate_Total_Value_Of_Items_In_Cart_For_Guest(Items_List, Tax_Rate, Discount_Code):
    # Duplicate block smell
    Total = 0
    for Item in Items_List:
        if Item is not None:
            if Item.price > 0:
                if Item.active:
                    if Discount_Code == "SAVE10":
                        Total += Item.price * 0.9
                    elif Discount_Code == "SAVE20":
                        Total += Item.price * 0.8
                    else:
                        Total += Item.price
    return Total + (Total * Tax_Rate)
"""
}
