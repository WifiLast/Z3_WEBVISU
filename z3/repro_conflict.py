
from z3 import *

def repro():
    locals_dict = {}
    
    # 1. Setup Environment like mcp_backend
    obj_sort = DeclareSort('Object')
    locals_dict['Object'] = obj_sort
    solver = Solver()
    locals_dict['s'] = solver # <--- The issue
    
    # 2. User Aliases
    aliases = {"H": "Human", "s": "socrates"}
    
    # Register symbols (mocking register_symbol)
    if "H" not in locals_dict:
        # H is predicate
        locals_dict["H"] = Function("Human", obj_sort, BoolSort())
        
    if "s" not in locals_dict:
        # s is constant
        locals_dict["s"] = Const("socrates", obj_sort)
    else:
        print(f"'s' already in locals_dict: {type(locals_dict['s'])}")
        
    # 3. Eval
    premise = "H(s)"
    try:
        print(f"Evaluating: {premise}")
        # H(s) -> Human(solver) -> FAIL
        expr = eval(premise, globals(), locals_dict)
        print("Success")
    except Exception as e:
        print(f"Caught expected error: {e}")

if __name__ == "__main__":
    repro()
