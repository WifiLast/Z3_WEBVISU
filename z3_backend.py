from flask import Flask, request, jsonify
from z3 import *
from flask import request, Blueprint, flash, json
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def calculator(equation: str) -> str:
    """
    Calculate the result of an equation.
    :param equation: The equation to calculate.
    """

    # Avoid using eval in production code
    # https://nedbatchelder.com/blog/201206/eval_really_is_dangerous.html
    try:
        b = "-+/*=><1234567890 "
        cache = equation
        for char in b:
            cache = cache.replace(char, "")
        single_cache = set(cache)
        var_array = []
        for entry in single_cache:
            exec(f"{entry} = Real(entry)")
        print(var_array)
        result = eval("simplify(" + equation + ")")
        print(result)
        return f"{equation} = {result}"
    except Exception as e:
        print(e)
        return "Invalid equation"

def solve_equation(equation: str) -> str:
    """
    Calculate the result of an equation.
    :param equation: The equation to calculate.
    """

    try:
        # Create a local scope for variables
        locals_dict = {}
        
        # Parse the equation to extract variable names
        b = "-+/*=><1234567890, "
        cache = equation
        for char in b:
            cache = cache.replace(char, "")
        single_cache = set(cache)
        
        # Create Z3 variables in the local scope
        for entry in single_cache:
            locals_dict[entry] = Real(entry)
        
        # Create solver
        s = Solver()
        
        # Split constraints by comma
        constraints = equation.split(',')
        for constraint in constraints:
            # Add each constraint to the solver using the local scope
            s.add(eval(constraint.strip(), globals(), locals_dict))
        
        # Check satisfiability
        if s.check() == sat:
            model = s.model()
            result = ", ".join([f"{var} = {model[locals_dict[var]]}" for var in locals_dict])
            return f"Solution found: {result}"
        else:
            return "No solution exists for the given constraints"
    except Exception as e:
        print(f"Error: {e}")
        return f"Invalid equation: {str(e)}"

@app.route('/solver', methods=['POST'])
def create_solver():
    cache = request.get_data()
    cache_json = json.loads(cache)
    equation = cache_json['equation']
    result = solve_equation(equation)
    return jsonify({"message": str(result)}), 200

@app.route('/add_constraint', methods=['POST'])
def add_constraint():
    data = request.json
    constraint = data.get('constraint')
    # Here you would add the logic to add the constraint to the solver
    return jsonify({"message": "Constraint added", "constraint": constraint}), 200

@app.route('/check_satisfiability', methods=['POST'])
def check_satisfiability():
    # Here you would check the satisfiability of the constraints
    return jsonify({"message": "Satisfiability checked"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
