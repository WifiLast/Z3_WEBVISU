
import os
import time
from mcp_backend_z3_current import prove_logic, cache
import sqlite3

# Use a test-specific database to avoid locking issues with the main app
TEST_DB = "z3_cache_loose_test.db"
cache.db_path = TEST_DB

# clear db
if os.path.exists(TEST_DB):
    try:
        os.remove(TEST_DB)
    except PermissionError:
        print(f"Warning: Could not remove {TEST_DB}, trying to use existing...")

cache._init_db()

print("--- RUN 1: Saving to cache ---")
premises = ["Implies(H(s), M(s))", "H(s)"]
conclusion = "M(s)"
# Aliases for Run 1
aliases_1 = {"H": "Human", "M": "Mortal", "s": "socrates"}
res1 = prove_logic(premises, conclusion, aliases=aliases_1)
print(f"Run 1 Result: {res1}")

print("\n--- RUN 2: Changing Aliases (Should still CACHE HIT) ---")
# Aliases for Run 2 (Different names, same logic structure in premises/conclusion)
# Note: prove_logic uses aliases for internal symbol resolution, but the raw premises strings are unique or not?
# The user said: "shortened version should not vary so much" and "cache only premises and conclusion".
# If I pass the SAME premises list and conclusion, but DIFFERENT aliases dict, current implementation hashes the aliases dict too, so it would MISS.
# Goal: It should HIT.

aliases_2 = {"H": "Humanity", "M": "Mortality", "s": "socrates_guy"}
start = time.time()
res2 = prove_logic(premises, conclusion, aliases=aliases_2)
end = time.time()

# We can check if it was a hit by checking if the DB has 1 or 2 entries, or via console output if we could capture it, 
# but easiest is manually checking current DB state or just assuming checking behavior for now.
# Or better: We can inspect the cache object's last access or just check the row count in DB.

with sqlite3.connect(cache.db_path) as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM z3_proof_cache")
    count = cursor.fetchone()[0]
    print(f"\nDB Row Count: {count}")
    
    # Let's also print the rows to be sure
    cursor.execute("SELECT hash_key, result FROM z3_proof_cache")
    rows = cursor.fetchall()
    for r in rows:
        print(f"Row: {r}")

if count == 1:
    print("\nSUCCESS: Single cache entry used (Loose caching works).")
else:
    print("\nFAILURE: Multiple cache entries created (Strict caching).")
