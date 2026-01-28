
import sqlite3
import hashlib
import json
import os
import time
from typing import List, Dict, Optional

class Z3Cache:
    def __init__(self, db_path: str = "z3_cache.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the database table if it doesn't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS z3_proof_cache (
                        hash_key TEXT PRIMARY KEY,
                        result INTEGER,
                        timestamp REAL
                    )
                """)
                conn.commit()
        except Exception as e:
            print(f"[Z3Cache] Error initializing database: {e}")

    def _compute_hash(self, premises: List[str], conclusion: str, declarations: Dict = None, aliases: Dict = None) -> str:
        """Compute a deterministic hash for the inputs."""
        # Normalize inputs
        norm_premises = sorted(premises) if premises else []
        
        # Create a structure to hash
        data = {
            "premises": norm_premises,
            "conclusion": conclusion
        }
        
        # Serialize to JSON with sorted keys for determinism
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode("utf-8")).hexdigest()

    def get_cache(self, premises: List[str], conclusion: str, declarations: Dict = None, aliases: Dict = None) -> Optional[bool]:
        """Retrieve result from cache if it exists."""
        hash_key = self._compute_hash(premises, conclusion, declarations, aliases)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT result FROM z3_proof_cache WHERE hash_key = ?", (hash_key,))
                row = cursor.fetchone()
                if row:
                    return bool(row[0])
        except Exception as e:
            print(f"[Z3Cache] Error reading cache: {e}")
        return None

    def set_cache(self, premises: List[str], conclusion: str, declarations: Dict = None, aliases: Dict = None, result: bool = False):
        """Save result to cache."""
        hash_key = self._compute_hash(premises, conclusion, declarations, aliases)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO z3_proof_cache (hash_key, result, timestamp)
                    VALUES (?, ?, ?)
                """, (hash_key, int(result), time.time()))
                conn.commit()
        except Exception as e:
            print(f"[Z3Cache] Error writing cache: {e}")
