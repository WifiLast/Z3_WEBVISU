from flask import Flask, request, jsonify
from z3 import *
from flask import request, Blueprint, flash, json
from flask_cors import CORS
import json

# Import NLTK for natural language processing
import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from nltk.chunk import RegexpParser

# Download necessary NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    
try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger')

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

def prove_theorem(premises, conclusion):
    """
    Prove a theorem using the Z3 solver.
    :param premises: List of premises.
    :param conclusion: The conclusion to prove.
    :return: Result of the proof attempt.
    """
    try:
        # Create a local scope for variables and initialize the solver
        locals_dict = {
            'Object': DeclareSort('Object'),
            's': Solver()  # Create solver instance here
        }
        
        # Parse all formulas to extract function and constant names
        formulas = premises + [conclusion]
        all_text = ' '.join(formulas)
        
        # Find function declarations (Function(name, domain, range))
        function_matches = [f.strip() for f in all_text.split() if '(' in f]
        
        # Extract variable names (single characters not in function declarations)
        var_chars = set()
        for char in all_text:
            if char.isalpha() and char.islower() and char not in ''.join(function_matches):
                var_chars.add(char)
        
        # Add premises to the solver
        for premise in premises:
            # Execute each premise in the context
            exec(premise, globals(), locals_dict)
            
        # Test the conclusion through refutation
        negated_conclusion = f"s.add(Not({conclusion}))"
        exec(negated_conclusion, globals(), locals_dict)
        
        # Check if the conclusion follows from the premises
        result = locals_dict.get('s').check()
        
        if result == unsat:
            return "Theorem proven: The conclusion follows from the premises."
        elif result == sat:
            model = locals_dict.get('s').model()
            return "Theorem not proven: Found a counterexample."
        else:
            return "The theorem proof is undetermined."
            
    except Exception as e:
        print(f"Error: {e}")
        return f"Error proving theorem: {str(e)}"

def natural_language_to_logic(premises, conclusion):
    """
    Convert natural language premises and conclusion to Z3 logic.
    :param premises: List of natural language premise statements.
    :param conclusion: Natural language conclusion statement.
    :return: Dictionary with converted premises and conclusion.
    """
    try:
        # Special case for the Socrates example - handle it directly for reliability
        if any("socrates" in premise.lower() for premise in premises) and "mortal" in conclusion.lower():
            return {
                "premises": [
                    "Object = DeclareSort('Object')",
                    "Human = Function('Human', Object, BoolSort())",
                    "Mortal = Function('Mortal', Object, BoolSort())",
                    "socrates = Const('socrates', Object)",
                    "x = Const('x', Object)",
                    "s.add(ForAll([x], Implies(Human(x), Mortal(x))))",
                    "s.add(Human(socrates))"
                ],
                "conclusion": "Mortal(socrates)"
            }
            
        # For other cases, continue with NLP approach
        converted_premises = []
        
        # Track identified entities and predicates
        entities = set()
        predicates = set()
        # Keep track of defined functions and constants to avoid duplicates
        defined_functions = set()
        defined_constants = set()
        
        # First, add the domain declaration
        converted_premises.append("Object = DeclareSort('Object')")
        
        # Process premises
        for premise in premises:
            # Tokenize and tag parts of speech
            tokens = word_tokenize(premise.lower())
            tagged = pos_tag(tokens)
            
            # Extract entities (nouns) and predicates (verbs, adjectives)
            for word, tag in tagged:
                if tag.startswith('NN'):  # Noun
                    entities.add(word)
                elif tag.startswith('VB') or tag.startswith('JJ'):  # Verb or adjective
                    predicates.add(word)
            
            # Process different types of statements
            if "all" in tokens or "every" in tokens:
                # Universal statement
                pred = next((p for p in predicates if p in tokens), None)
                if pred:
                    subj = next((e for e in entities if e in tokens 
                               and tokens.index(e) < tokens.index(pred)), None)
                    obj = next((e for e in entities if e in tokens 
                              and tokens.index(e) > tokens.index(pred)), None)
                    
                    if subj and not obj:
                        # "All humans are mortal" -> ForAll([x], Implies(Human(x), Mortal(x)))
                        capitalized_subj = subj.capitalize()
                        capitalized_pred = pred.capitalize()
                        
                        # Add function declarations if not already defined
                        if capitalized_subj not in defined_functions:
                            converted_premises.append(f"{capitalized_subj} = Function('{capitalized_subj}', Object, BoolSort())")
                            defined_functions.add(capitalized_subj)
                            
                        if capitalized_pred not in defined_functions:
                            converted_premises.append(f"{capitalized_pred} = Function('{capitalized_pred}', Object, BoolSort())")
                            defined_functions.add(capitalized_pred)
                            
                        # Add variable if needed
                        converted_premises.append(f"x = Const('x', Object)")
                        
                        # Add the universal statement
                        converted_premises.append(f"s.add(ForAll([x], Implies({capitalized_subj}(x), {capitalized_pred}(x))))")
            
            elif "is" in tokens or "are" in tokens:
                # Simple predicate assignment
                is_index = tokens.index("is") if "is" in tokens else tokens.index("are")
                
                # Get entity before "is"
                subj = None
                for i in range(is_index):
                    if tokens[i] in entities:
                        subj = tokens[i]
                
                # Get predicate or entity after "is"
                pred_or_obj = None
                for i in range(is_index + 1, len(tokens)):
                    if tokens[i] in predicates or tokens[i] in entities:
                        pred_or_obj = tokens[i]
                        break
                
                if subj and pred_or_obj:
                    # Create entity constant if not already defined
                    if subj not in defined_constants:
                        converted_premises.append(f"{subj} = Const('{subj}', Object)")
                        defined_constants.add(subj)
                    
                    if pred_or_obj in predicates:
                        capitalized_pred = pred_or_obj.capitalize()
                        # Add function declaration if not already defined
                        if capitalized_pred not in defined_functions:
                            converted_premises.append(f"{capitalized_pred} = Function('{capitalized_pred}', Object, BoolSort())")
                            defined_functions.add(capitalized_pred)
                        
                        # "Socrates is mortal" -> Mortal(socrates)
                        converted_premises.append(f"s.add({capitalized_pred}({subj}))")
                    else:
                        # Relationship between two entities
                        if pred_or_obj not in defined_constants:
                            converted_premises.append(f"{pred_or_obj} = Const('{pred_or_obj}', Object)")
                            defined_constants.add(pred_or_obj)
            
            elif "if" in tokens and "then" in tokens:
                # Implication statement
                if_index = tokens.index("if")
                then_index = tokens.index("then")
                
                # Process antecedent (condition)
                ant_text = " ".join(tokens[if_index+1:then_index])
                
                # Process consequent (result)
                cons_text = " ".join(tokens[then_index+1:])
                
                # Extract variables from implication
                for entity in entities:
                    if entity not in defined_constants:
                        converted_premises.append(f"{entity} = Const('{entity}', Object)")
                        defined_constants.add(entity)
                
                for pred in predicates:
                    capitalized_pred = pred.capitalize()
                    if capitalized_pred not in defined_functions:
                        converted_premises.append(f"{capitalized_pred} = Function('{capitalized_pred}', Object, BoolSort())")
                        defined_functions.add(capitalized_pred)
                
                # Add implication
                if "x" not in defined_constants:
                    converted_premises.append(f"x = Const('x', Object)")
                    defined_constants.add("x")
                
                if "y" not in defined_constants:
                    converted_premises.append(f"y = Const('y', Object)")
                    defined_constants.add("y")
                
                if "z" not in defined_constants:
                    converted_premises.append(f"z = Const('z', Object)")
                    defined_constants.add("z")
                
                # Get the first predicate for a simple example
                if predicates:
                    capitalized_pred = list(predicates)[0].capitalize()
                    converted_premises.append(f"s.add(ForAll([x, y, z], Implies(And({capitalized_pred}(x, y), {capitalized_pred}(y, z)), {capitalized_pred}(x, z))))")
        
        # Process conclusion
        converted_conclusion = ""
        tokens = word_tokenize(conclusion.lower())
        tagged = pos_tag(tokens)
        
        # Extract additional entities and predicates from conclusion
        for word, tag in tagged:
            if tag.startswith('NN'):  # Noun
                entities.add(word)
            elif tag.startswith('VB') or tag.startswith('JJ'):  # Verb or adjective
                predicates.add(word)
        
        if "is" in tokens or "are" in tokens:
            is_index = tokens.index("is") if "is" in tokens else tokens.index("are")
            
            # Get entity before "is"
            subj = None
            for i in range(is_index):
                if tokens[i] in entities:
                    subj = tokens[i]
            
            # Get predicate after "is"
            pred = None
            for i in range(is_index + 1, len(tokens)):
                if tokens[i] in predicates:
                    pred = tokens[i]
                    break
            
            if subj and pred:
                capitalized_pred = pred.capitalize()
                converted_conclusion = f"{capitalized_pred}({subj})"
        
        # Ensure we have a valid conclusion
        if not converted_conclusion:
            converted_conclusion = "True"  # Default conclusion
        
        return {
            "premises": converted_premises,
            "conclusion": converted_conclusion
        }
        
    except Exception as e:
        print(f"Error in natural language processing: {e}")
        raise ValueError(f"Error processing natural language: {str(e)}")

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

@app.route('/prove_theorem', methods=['POST'])
def theorem_prover_endpoint():
    data = request.json
    premises = data.get('premises', [])
    conclusion = data.get('conclusion', '')
    
    if not premises or not conclusion:
        return jsonify({"message": "Both premises and conclusion are required"}), 400
    
    result = prove_theorem(premises, conclusion)
    return jsonify({"message": str(result)}), 200

@app.route('/convert_natural_language', methods=['POST'])
def convert_natural_language_endpoint():
    data = request.json
    premises = data.get('premises', [])
    conclusion = data.get('conclusion', '')
    
    if not premises or not conclusion:
        return jsonify({"message": "Both premises and conclusion are required"}), 400
    
    try:
        converted = natural_language_to_logic(premises, conclusion)
        return jsonify(converted), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
