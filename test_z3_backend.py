import sys
import os

# Ensure we can import the backend module
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from mcp_backend_z3_current import check_satisfiability
    # Mocking the tool decorator if necessary? 
    # The decorator @mcp.tool() might wrap the function. 
    # If the import works and we can call it, great. 
    # But usually @mcp.tool() returns a Tool object or similar?
    # Let's check line 12 of mcp_backend_z3_current.py: @mcp.tool()
    # If FastMCP.tool() returns the original function or a wrapper that is callable, we are good.
    # FastMCP typically registers it but might leave the function callable.
    # If not, we might need to access the underlying function.
    # We'll try calling it directly first.
except ImportError:
    print("Could not import check_satisfiability from mcp_backend_z3_current")
    sys.exit(1)

def run_test(name, constraints, variables=None, expected_sat=True):
    print(f"--- Running Test: {name} ---")
    print(f"Constraints: {constraints}")
    if variables:
        print(f"Variables: {variables}")
    
    # FastMCP tools might need to be called in a specific way if wrapped. 
    # Assuming standard python callable behavior or accessing __wrapped__ if needed.
    # Let's try direct call.
    try:
        result = check_satisfiability(constraints, variables)
    except Exception as e:
        # If direct call fails due to MCP wrapper, try finding the original func
        # This is a bit speculative without seeing FastMCP implementation
        print(f"Direct call failed: {e}")
        if hasattr(check_satisfiability, '__wrapped__'):
             print("Trying __wrapped__ function...")
             result = check_satisfiability.__wrapped__(constraints, variables)
        else:
             print("Could not call function.")
             return

    print(f"Result: {result}")
    
    is_sat = result.get("satisfiable")
    if is_sat == expected_sat:
        print("PASS")
    else:
        print(f"FAIL: Expected satisfiable={expected_sat}, got {is_sat}")
    print()

def main():
    # 1. Simplified Mode (Explicit Types)
    run_test("Simplified Explicit", 
             ["x > 10", "y < 5"], 
             {"x": "Int", "y": "Int"}, 
             expected_sat=True)

    # 2. Simplified Mode (Inferred Types)
    run_test("Simplified Inferred", 
             ["a + b == 20", "a > 10"], 
             None, 
             expected_sat=True)

    # 3. Complex Logic (Contradiction)
    # Using Z3 functions like Implies require them to be in scope of eval()
    # Detailed check: In our code, we do `eval(constraint, globals(), locals_dict)`
    # The `globals()` in eval call refers to the `mcp_backend_z3_current` Globals, which has `from z3 import *`.
    # So `Implies` should be available.
    run_test("Contradiction", 
             ["Implies(x > 0, y > 0)", "x == 5", "y < 0"], 
             None, 
             expected_sat=False)

    # 4. Complex Arithmetic
    run_test("Complex Arithmetic", 
             ["x * x + y * y == 25", "x == 3"], 
             None, 
             expected_sat=True)

    # 5. Legacy Mode
    run_test("Legacy Mode", 
             ["s = Solver()", "x = Int('x')", "s.add(x > 5)"], 
             None, 
             expected_sat=True)

if __name__ == "__main__":
    main()
