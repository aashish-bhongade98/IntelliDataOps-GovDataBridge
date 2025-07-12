# app.py

from flask import Flask, render_template, request, jsonify
import re # Import the regular expression module

# Initialize the Flask application
app = Flask(__name__)

# --- Schema Parsing & Normalization Logic ---
def parse_schema_string(schema_str):
    """
    Parses a comma-separated string of column names and returns a list
    of normalized column names.

    Normalization steps:
    1. Splits the string by commas.
    2. Strips leading/trailing whitespace from each part.
    3. Converts each part to lowercase.
    4. Removes all non-alphanumeric characters (including spaces) from each part.

    Args:
        schema_str (str): A string representing column names, e.g., "CitizenID, Full Name, DOB".

    Returns:
        list: A list of normalized column names, e.g., ["citizenid", "fullname", "dob"].
    """
    if not isinstance(schema_str, str):
        return [] # Return empty list for invalid input

    # Split by comma, strip whitespace from each part
    column_names = [col.strip() for col in schema_str.split(',')]

    normalized_names = []
    for name in column_names:
        # Remove non-alphanumeric characters (including spaces) and convert to lowercase
        normalized_name = re.sub(r'[^a-zA-Z0-9]', '', name).lower()
        if normalized_name: # Only add if not empty after normalization
            normalized_names.append(normalized_name)

    return normalized_names

# --- Basic Matching Logic ---
def match_schemas(schema_a_normalized, schema_b_normalized):
    """
    Performs exact matching between two lists of normalized column names.

    Args:
        schema_a_normalized (list): A list of normalized column names from schema A.
        schema_b_normalized (list): A list of normalized column names from schema B.

    Returns:
        dict: A dictionary containing:
              - 'matches': A list of column names found in both schemas.
              - 'unmatched_a': A list of column names unique to schema A.
              - 'unmatched_b': A list of column names unique to schema B.
    """
    # Convert lists to sets for efficient set operations (intersection, difference)
    set_a = set(schema_a_normalized)
    set_b = set(schema_b_normalized)

    # Exact matches: elements present in both sets
    matches = sorted(list(set_a.intersection(set_b)))

    # Unmatched in A: elements present in A but not in B
    unmatched_a = sorted(list(set_a.difference(set_b)))

    # Unmatched in B: elements present in B but not in A
    unmatched_b = sorted(list(set_b.difference(set_a)))

    return {
        "matches": matches,
        "unmatched_a": unmatched_a,
        "unmatched_b": unmatched_b
    }

# --- Flask Routes ---

@app.route('/')
def index():
    """
    This function handles requests to the root URL ('/').
    It renders the index.html template.
    """
    return render_template('index.html')

@app.route('/match', methods=['POST'])
def perform_match():
    """
    This endpoint receives schema strings from the frontend,
    parses and normalizes them, performs matching, and returns
    the results as JSON.
    """
    data = request.get_json() # Get JSON data from the request body
    schema_a_str = data.get('schemaA', '')
    schema_b_str = data.get('schemaB', '')

    normalized_a = parse_schema_string(schema_a_str)
    normalized_b = parse_schema_string(schema_b_str)

    matching_results = match_schemas(normalized_a, normalized_b)

    return jsonify(matching_results) # Return results as JSON

# This block ensures the Flask development server runs only when the script is executed directly.
if __name__ == '__main__':
    app.run(debug=True)