# server.py
from mcp.server.fastmcp import FastMCP
from z3 import *
import traceback
from typing import List

import uvicorn
# Create an MCP server for Z3 Logic Solving
mcp = FastMCP("Z3 Logic Solver")


@mcp.tool()
def prove_logic(premises: List[str], conclusion: str, declarations: dict = None, aliases: dict = None) -> bool:
    """
    Prove whether a conclusion logically follows from given premises using Z3 solver.

    Returns True if the conclusion is proven, False otherwise.

    SYNTAX INSTRUCTIONS:
    ====================
    
    1. Simplified Mode (Recommended):
       - Pass mathematical/logical expressions as strings.
       - 'Object' sort and 'Solver' are automatically created.
       - Symbols are inferred:
         - "Name(...)" -> Predicate (Function returning Bool)
         - "name"      -> Constant (Object)
       
       Aliases:
       - Use 'aliases' dict to map short names to full names.
         e.g. aliases={"H": "Human", "s": "socrates"}
         Input: "H(s)" -> Interpreted as "Human(socrates)" in Z3, but you write "H(s)".
       
       declarations:
       - Use 'declarations' to explicitly set types if inference is wrong.
         e.g. declarations={"X": "Object", "P": "Predicate"}

       Example:
       prove_logic(
           premises=["H(s) -> M(s)", "H(s)"],
           conclusion="M(s)",
           aliases={"H": "Human", "M": "Mortal", "s": "socrates"}
       )

    2. Legacy Mode (Advanced):
       - Full Z3 Python script strings including "s = Solver()", "Object = DeclareSort...", etc.
       - Used if premises contain raw python code with "s.add(...)".

    Returns:
        True if conclusion is proven, False otherwise
    """
    try:
        # Create a fresh context for this theorem
        context = {
            'solver': None,
            'variables': {},
        }
        locals_dict = {}
        import re

        # Determine mode
        # If declarations/aliases provided OR proper logic syntax (no s.add), use Simplified Mode
        is_simplified_mode = False
        if declarations is not None or aliases is not None:
             is_simplified_mode = True
        elif premises and not any("s.add" in p for p in premises) and not any("Solver()" in p for p in premises):
             is_simplified_mode = True

        if is_simplified_mode:
            try:
                # 1. Setup Environment
                obj_sort = DeclareSort('Object')
                locals_dict['Object'] = obj_sort
                solver = Solver()
                locals_dict['s'] = solver
                context['solver'] = solver

                if declarations is None: declarations = {}
                if aliases is None: aliases = {}

                # 2. Process Aliases & Declarations
                # We need to map: "key" -> Z3 Object(name="value")
                
                # Helper to get z3 name: value if alias else key
                # Helper to register in locals_dict
                
                def register_symbol(symbol_key, z3_name=None, type_hint=None):
                    if symbol_key in locals_dict: return
                    
                    real_name = z3_name if z3_name else symbol_key
                    
                    # Decide type
                    # type_hint values: "Predicate", "Function", "Const", "Object"
                    # Default inference if no hint:
                    # If it looks like it's used as Function -> Predicate
                    # This is hard to know without parsing usage. 
                    # We will rely on Declarations + Inference from text regex later.
                    
                    # For now, just register what we know from declarations
                    
                    # Standard creation logic
                    if type_hint == "Predicate" or type_hint == "Function":
                        # We don't know arity (number of args) easily without parsing.
                        # Z3 Functions need domain signatures. 
                        # Simplified assumption: Unary predicate "Function(name, Object, BoolSort())"
                        # Or we utilize a flexible Python Function that returns a Z3 func? No z3 is strict.
                        
                        # LIMITATION: In simplified mode without explicit arity, we assume Unary Predicate (Object->Bool).
                        # If user needs binary, they must use Legacy or we find a way to detect arity.
                        # Detection: Regex search "Symbol(a, b)" -> Arity 2.
                        
                        # Let's do a quick scan of usage in premises/conclusion for this symbol
                        all_text = " ".join(premises) + " " + conclusion
                        # count commas in usage: Symbol(..., ..., ...)
                        # Regex: Symbol \s* \( ([^)]*) \)
                        matcher = re.search(rf'\b{symbol_key}\s*\((.*?)\)', all_text)
                        arity = 1
                        if matcher:
                            args_str = matcher.group(1)
                            if args_str.strip():
                                arity = args_str.count(',') + 1
                            else:
                                arity = 0 # Symbol() ?
                        
                        domain = [obj_sort] * arity
                        locals_dict[symbol_key] = Function(real_name, *domain, BoolSort())
                        
                    elif type_hint == "Const" or type_hint == "Object":
                         locals_dict[symbol_key] = Const(real_name, obj_sort)
                         
                    else:
                        # Fallback / Inference
                        # If starts with Lowercase -> Const
                        # If starts with Uppercase -> Predicate (Unary)
                        # This is a heuristic.
                        if symbol_key[0].islower():
                            locals_dict[symbol_key] = Const(real_name, obj_sort)
                        else:
                            # Check arity again for inference
                            all_text = " ".join(premises) + " " + conclusion
                            matcher = re.search(rf'\b{symbol_key}\s*\((.*?)\)', all_text)
                            arity = 1
                            if matcher:
                                args_str = matcher.group(1)
                                if args_str.strip():
                                    arity = args_str.count(',') + 1
                            
                            domain = [obj_sort] * arity
                            locals_dict[symbol_key] = Function(real_name, *domain, BoolSort())

                # Register Aliases
                for alias_key, full_name in aliases.items():
                    # Check declarations for type hint
                    hint = declarations.get(alias_key)
                    register_symbol(alias_key, z3_name=full_name, type_hint=hint)

                # Register Explicit Declarations (non-aliases)
                for decl_key, decl_type in declarations.items():
                    if decl_key not in aliases:
                        register_symbol(decl_key, z3_name=decl_key, type_hint=decl_type)

                # 3. Discovery of remaining symbols
                all_text = " ".join(premises) + " " + conclusion
                # Tokens: [a-zA-Z_]\w*
                potential_tokens = set(re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', all_text))
                
                # Blocklist
                reserved = set(globals().keys()) | {'True', 'False', 'None', 'And', 'Or', 'Not', 'Implies', 'ForAll', 'Exists', 'Object', 'BoolSort'}
                
                for token in potential_tokens:
                    if token not in locals_dict and token not in reserved and not hasattr(sys.modules[__name__], token):
                        register_symbol(token) # Will infer type/arity

                # 4. Add Constraints
                for premise in premises:
                    # If premise is just a boolean expression string, we add it.
                    # We assume NO "s.add" logic here.
                    expr = eval(premise, globals(), locals_dict)
                    solver.add(expr)
                    
            except Exception as e:
                print(f"[Z3 MCP] Error in Simplified Mode: {e}")
                traceback.print_exc()
                return False

        else:
            # --- LEGACY MODE ---
            # Execute all premises to build the logical context
            for premise in premises:
                try:
                    exec(premise, globals(), locals_dict)
                    if 's' in locals_dict and locals_dict['s'] is not None:
                        context['solver'] = locals_dict['s']
                except Exception as e:
                    print(f"[Z3 MCP] Error executing premise '{premise}': {e}")
                    return False
        
        # Ensure we have a solver
        if context['solver'] is None:
            print("[Z3 MCP] Error: No solver created.")
            return False

        # Test the conclusion
        try:
            # If simplified mode, conclusion is just string expr.
            if is_simplified_mode:
                 conc_expr = eval(conclusion, globals(), locals_dict)
                 negated_conclusion_expr = Not(conc_expr)
                 context['solver'].add(negated_conclusion_expr)
            else:
                negated_conclusion = f"s.add(Not({conclusion}))"
                exec(negated_conclusion, globals(), locals_dict)
                
        except Exception as e:
            print(f"[Z3 MCP] Error negating conclusion '{conclusion}': {e}")
            return False

        # Check
        result = context['solver'].check()

        if result == unsat:
            print(f"[Z3 MCP] PROVEN: {conclusion}")
            return True
        elif result == sat:
            print(f"[Z3 MCP] NOT PROVEN: {conclusion}")
            return False
        else:
            print(f"[Z3 MCP] UNKNOWN")
            return False

    except Exception as e:
        print(f"[Z3 MCP] Error proving theorem: {e}")
        traceback.print_exc()
        return False


@mcp.tool()
def check_satisfiability(constraints: List[str], variables: dict = None) -> dict:
    """
    Check if a set of logical constraints is satisfiable and return a model if it exists.

    This tool checks if there exists any assignment of values that satisfies all constraints.
    Unlike prove_logic which proves theorems, this finds solutions to constraint problems.

    SYNTAX:
    1. Simplified Mode (Recommended):
       Provide a list of mathematical string expressions.
       Variables are automatically detected and assumed to be Ints unless specified in 'variables'.
       
       constraints = ["x + y > 59", "x > 10"]
       variables = {"x": "Int", "y": "Int"} (Optional, defaults to Int)

    2. Legacy Mode (Advanced):
       Full Z3 Python script.
       constraints = [
           "s = Solver()",
           "x = Int('x')", 
           "s.add(x > 10)"
       ]

    Returns:
        {
            "satisfiable": True/False,
            "model": {"x": "4", "y": "6"} or None,
            "error": "..." (if any)
        }
    """
    import re
    
    try:
        locals_dict = {}
        solver = None

        # Determine mode: Simplified vs Legacy
        # logic: if 'variables' is provided OR constraints look like expressions (no "s.add"), utilize simplified mode
        is_simplified_mode = False
        if variables is not None:
             is_simplified_mode = True
        elif constraints and not any("s.add" in c for c in constraints) and not any("Solver()" in c for c in constraints):
             is_simplified_mode = True

        if is_simplified_mode:
            # --- SIMPLIFIED MODE ---
            try:
                # 1. Initialize Solver
                solver = Solver()
                locals_dict['s'] = solver
                
                # 2. Identify Variables
                # If variables dict is not provided, init as empty
                if variables is None:
                    variables = {}
                
                # Gather all tokens from constraints to find implicit variables
                all_text = " ".join(constraints)
                # Regex to find potential identifiers: starts with letter, contains alphanumeric/_
                potential_vars = set(re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', all_text))
                
                # Filter out Z3 keywords/functions and python builtins
                # We can check if they are already in globals() (which has from z3 import *)
                # or in a strict blocklist
                reserved = set(globals().keys()) | {'True', 'False', 'None', 'and', 'or', 'not', 'if', 'else', 'in', 'is'}
                
                discovered_vars = [v for v in potential_vars if v not in reserved and not hasattr(sys.modules[__name__], v)]

                # 3. Create Z3 Variables
                # Prioritize explicit types in 'variables' dict, otherwise default to Int
                for var_name in variables:
                    var_type = variables[var_name]
                    if var_type == 'Int':
                        locals_dict[var_name] = Int(var_name)
                    elif var_type == 'Real':
                        locals_dict[var_name] = Real(var_name)
                    elif var_type == 'Bool':
                        locals_dict[var_name] = Bool(var_name)
                    else:
                        # Fallback for unknown types or if user passed something specific
                        # defaulting to Int is safest if unknown string
                        locals_dict[var_name] = Int(var_name)

                for var_name in discovered_vars:
                    if var_name not in locals_dict:
                        # Default assumption: Int
                        locals_dict[var_name] = Int(var_name)

                # 4. Add Constraints
                for constraint in constraints:
                    # Eval string logic -> Z3 expression
                    # We assume the constraint string evaluates to a Z3 Bool expression
                    # e.g. "x + y > 59" -> (x + y > 59)
                    
                    # Handle common replacements if needed (e.g. valid python syntax)
                    # But Z3 overloads operators so standard python syntax usually works.
                    # Just need to be careful with implicit boolean conversion if mixed? 
                    # Z3 'And', 'Or' are functions, python 'and', 'or' are kw. 
                    # Users should likely use z3 syntax And(..), Or(..), separate constraints implies implicit And
                    
                    expr = eval(constraint, globals(), locals_dict)
                    solver.add(expr)

            except Exception as e:
                return {
                    "satisfiable": False,
                    "error": f"Error in Simplified Mode setup: {str(e)}"
                }

        else:
            # --- LEGACY MODE ---
            # Execute all constraints as raw python script
            for constraint in constraints:
                try:
                    exec(constraint, globals(), locals_dict)
                    if 's' in locals_dict:
                        solver = locals_dict['s']
                except Exception as e:
                    return {
                        "satisfiable": False,
                        "error": f"Error in constraint '{constraint}': {str(e)}"
                    }

            if solver is None:
                return {
                    "satisfiable": False,
                    "error": "No solver created. Include 's = Solver()' in constraints."
                }

        # Check satisfiability
        result = solver.check()

        if result == sat:
            model = solver.model()
            model_dict = {}
            for decl in model.decls():
                model_dict[decl.name()] = str(model[decl])

            return {
                "satisfiable": True,
                "model": model_dict
            }
        elif result == unsat:
            return {
                "satisfiable": False,
                "model": None
            }
        else:
            return {
                "satisfiable": False,
                "model": None,
                "error": "Unknown result from solver"
            }

    except Exception as e:
        return {
            "satisfiable": False,
            "error": f"Error checking satisfiability: {str(e)}"
        }


# Run the server
if __name__ == "__main__":
    import sys

    # Default configuration
    host = "0.0.0.0"  # Change to "0.0.0.0" to accept connections from any IP
    port = 8000
    path = "/mcp"

    # Allow command-line overrides
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    if len(sys.argv) > 3:
        path = sys.argv[3]

    print("="*70)
    print("Z3 Logic Solver MCP Server")
    print("="*70)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Path: {path}")
    print(f"URL:  http://{host}:{port}{path}")
    print("="*70)
    print("\nServer is starting...")
    print("Press Ctrl+C to stop the server\n")

    # Run the server with HTTP transport
    #uvicorn.run(
    #    mcp, 
    #    host=host, 
    #    port=port
    #)
    #mcp.run(transport="http", host="0.0.0.0", port=8000)
    mcp.run(transport="streamable-http")
