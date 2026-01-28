
import os
import time
from mcp_backend_z3_current import prove_logic
from z3_cache import Z3Cache

# Setup
db_path = "z3_cache.db"
# Clear existing cache for test
if os.path.exists(db_path):
    os.remove(db_path)

# Re-init global cache in module? 
# The module initializes 'cache = Z3Cache()' at top level.
# Since we deleted the DB file, the next write will work (sqlite creates file).
# But if Z3Cache checked for table existence ONLY in init, deletion might be issue if connection open?
# Let's see implementation. init_db called in __init__.
# 'cache' object in mcp_backend_z3_current checks db on every call effectively by connecting.
# Actually, the 'set_cache' and 'get_cache' context managers open connection each time.
# So deleting file is fine, but table won't exist if we don't re-init.
# The cache object in backend was initialized at start.
# So we should probably remove file BEFORE import or trigger re-init?
# We imported prove_logic already. 
# Let's just create a new Z3Cache here to ensure DB/table exists, or rely on logic.
# Wait, Z3Cache._init_db is called only in __init__.
# If I delete file now, the table is gone. 
# The backend global 'cache' object won't know table is gone.
# It will try to select/insert and fail with "no such table".
# Solution: Don't delete file, just verify logic, OR ensure we call _init_db again.

# Better: Just run prove_logic for something unique.
unique_id = int(time.time())
premises = [f"Implies(A({unique_id}), B({unique_id}))", f"A({unique_id})"]
conclusion = f"B({unique_id})"

print("--- RUN 1 (Should be uncached) ---")
start = time.time()
res1 = prove_logic(premises, conclusion)
end = time.time()
print(f"Result: {res1}, Time: {end - start:.4f}s")

print("\n--- RUN 2 (Should be CACHED) ---")
start = time.time()
res2 = prove_logic(premises, conclusion)
end = time.time()
print(f"Result: {res2}, Time: {end - start:.4f}s")

if res1 == res2 == True:
    print("\nSUCCESS: Logic preserved.")
else:
    print("\nFAILURE: Results mismatch.")
