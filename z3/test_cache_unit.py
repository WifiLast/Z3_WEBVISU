
from z3_cache import Z3Cache

def test_cache_hashing():
    cache = Z3Cache("test_unit_cache.db")
    # clear db just in case
    import os
    if os.path.exists("test_unit_cache.db"):
        os.remove("test_unit_cache.db")
    cache._init_db()

    premises = ["A -> B", "A"]
    conclusion = "B"
    
    # Context 1
    decls1 = {"A": "bool", "B": "bool"}
    aliases1 = {"A": "Alpha"}
    
    # Context 2
    decls2 = {"A": "bool", "B": "bool", "C": "bool"}
    aliases2 = {"A": "AlphaBet"}
    
    # Compute hashes
    # Note: _compute_hash is internal, but for testing we can access it or use set/get
    
    hash1 = cache._compute_hash(premises, conclusion, decls1, aliases1)
    hash2 = cache._compute_hash(premises, conclusion, decls2, aliases2)
    
    print(f"Hash 1: {hash1}")
    print(f"Hash 2: {hash2}")
    
    if hash1 == hash2:
        print("SUCCESS: Hashes are identical despite different declarations/aliases.")
    else:
        print("FAILURE: Hashes differ.")
        
    # Verify DB interaction
    cache.set_cache(premises, conclusion, decls1, aliases1, True)
    
    # Try to get with DIFFERENT aliases
    res = cache.get_cache(premises, conclusion, decls2, aliases2)
    
    if res is True:
        print("SUCCESS: Cache HIT with different aliases.")
    else:
        print("FAILURE: Cache MISS with different aliases.")

if __name__ == "__main__":
    try:
        test_cache_hashing()
    except Exception as e:
        print(f"Test Error: {e}")
