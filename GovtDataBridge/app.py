from flask import Flask, request, render_template, jsonify
import pandas as pd
import io
import json
import xml.etree.ElementTree as ET
import base64
import os # To check file extensions

app = Flask(__name__)

# --- Schema Parsing & Normalization Logic ---

def normalize_name(name):
    """Normalize a column name for comparison."""
    # Ensure it's a string before calling .strip()
    if not isinstance(name, str):
        name = str(name)
    return name.strip().lower().replace(" ", "").replace("_", "")

def infer_schema_from_csv_content(csv_content_str):
    """Infers schema from CSV content string using pandas."""
    if not csv_content_str.strip():
        return []
    try:
        # pd.read_csv needs a file-like object or path
        df = pd.read_csv(io.StringIO(csv_content_str))
        return [normalize_name(col) for col in df.columns.tolist()]
    except pd.errors.EmptyDataError:
        return []
    except Exception as e:
        print(f"Error inferring CSV schema: {e}")
        return []

def infer_schema_from_json_content(json_content_str):
    """Infers schema from JSON content string (top-level keys of first object/array element)."""
    if not json_content_str.strip():
        return []
    try:
        data = json.loads(json_content_str)
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            # List of objects, infer from first object
            return [normalize_name(key) for key in data[0].keys()]
        elif isinstance(data, dict):
            # Single object
            return [normalize_name(key) for key in data.keys()]
        else:
            return [] # Unhandled JSON structure (e.g., list of primitives)
    except json.JSONDecodeError:
        print("Error: Invalid JSON content.")
        return []
    except Exception as e:
        print(f"Error inferring JSON schema: {e}")
        return []

def infer_schema_from_xlsx_content(file_content_bytes):
    """Infers schema from XLSX content bytes using pandas."""
    if not file_content_bytes:
        return []
    try:
        # pd.read_excel needs a file-like object or path
        df = pd.read_excel(io.BytesIO(file_content_bytes))
        return [normalize_name(col) for col in df.columns.tolist()]
    except Exception as e:
        print(f"Error inferring XLSX schema: {e}")
        return []

def infer_schema_from_xml_content(xml_content_str):
    """
    Infers schema from XML content string.
    Simplistic: takes top-level unique tags directly under the root.
    """
    if not xml_content_str.strip():
        return []
    try:
        root = ET.fromstring(xml_content_str)
        schema_fields = sorted(list(set([elem.tag for elem in root])))
        return [normalize_name(f) for f in schema_fields]
    except ET.ParseError:
        print("Error: Invalid XML content.")
        return []
    except Exception as e:
        print(f"Error inferring XML schema: {e}")
        return []


def match_schemas(schema_a_fields, schema_b_fields):
    """
    Matches two lists of normalized schema fields.
    Returns matches and unmapped fields.
    """
    matches = []
    # Create copies to safely remove elements during matching
    unmatched_a = list(schema_a_fields)
    unmatched_b = list(schema_b_fields)

    # Exact Match
    for field_a in schema_a_fields:
        if field_a in unmatched_b:
            matches.append((field_a, field_a)) # Store original names or normalized? For simplicity, normalized.
            unmatched_a.remove(field_a)
            unmatched_b.remove(field_a)
    return {
        "matches": matches,
        "unmatched_a": unmatched_a,
        "unmatched_b": unmatched_b
    }

# --- Flask Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/match', methods=['POST'])
def perform_match():
    data = request.json
    file_a_base64 = data.get('file_a_base64', '')
    file_a_name = data.get('file_a_name', '')
    file_b_base64 = data.get('file_b_base64', '')
    file_b_name = data.get('file_b_name', '')

    parsed_schema_a = []
    parsed_schema_b = []

    # Process File A
    if file_a_base64:
        try:
            file_a_bytes = base64.b64decode(file_a_base64)
            _, file_a_extension = os.path.splitext(file_a_name.lower())

            if file_a_extension == '.csv':
                parsed_schema_a = infer_schema_from_csv_content(file_a_bytes.decode('utf-8'))
            elif file_a_extension == '.json':
                parsed_schema_a = infer_schema_from_json_content(file_a_bytes.decode('utf-8'))
            elif file_a_extension == '.xlsx':
                parsed_schema_a = infer_schema_from_xlsx_content(file_a_bytes)
            elif file_a_extension == '.xml':
                parsed_schema_a = infer_schema_from_xml_content(file_a_bytes.decode('utf-8'))
            else:
                print(f"Unsupported file type for Schema A: {file_a_extension}")
        except Exception as e:
            print(f"Error processing file A: {e}")
            return jsonify({"error": f"Could not process file A: {e}"}), 400

    # Process File B
    if file_b_base64:
        try:
            file_b_bytes = base64.b64decode(file_b_base64)
            _, file_b_extension = os.path.splitext(file_b_name.lower())

            if file_b_extension == '.csv':
                parsed_schema_b = infer_schema_from_csv_content(file_b_bytes.decode('utf-8'))
            elif file_b_extension == '.json':
                parsed_schema_b = infer_schema_from_json_content(file_b_bytes.decode('utf-8'))
            elif file_b_extension == '.xlsx':
                parsed_schema_b = infer_schema_from_xlsx_content(file_b_bytes)
            elif file_b_extension == '.xml':
                parsed_schema_b = infer_schema_from_xml_content(file_b_bytes.decode('utf-8'))
            else:
                print(f"Unsupported file type for Schema B: {file_b_extension}")
        except Exception as e:
            print(f"Error processing file B: {e}")
            return jsonify({"error": f"Could not process file B: {e}"}), 400

    results = match_schemas(parsed_schema_a, parsed_schema_b)
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True) # Run in debug mode for development

    