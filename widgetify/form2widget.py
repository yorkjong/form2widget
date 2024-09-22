"""
form2widget - Google Colab notebook Forms to Jupyter Widgets converter

This module provides functionality to extract form parameters from Colab
notebooks and convert them into interactive ipywidgets that are compatible
with Voilà, enabling easier deployment of Colab notebooks as web applications.

The module parses Colab form parameters (annotated with `# @param` and
`# @title`), generates corresponding ipywidgets code, and modifies the notebook
accordingly.

Usage:

Example usage to convert a Colab notebook to Voilà-compatible widgets:
::

    from form2widget import widgetify
    widgetify('example_colab_forms.ipynb')
"""
__author__ = "York <york.jong@gmail.com>"
__date__ = "2024/09/19 (initial version) ~ 2024/09/22 (last revision)"

__all__ = [
    'widgetify',
]

import ast
import re
import logging

import nbformat

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def widgetify(nb_filename):
    """Convert Colab Forms to Jupyter Widgets for Voilà compatibility.

    Extracts form parameters from code cells, generates ipywidgets code, and
    embeds it into the notebook. Adds a markdown cell with a title if "@title"
    is present.

    Args:
        nb_filename (str): The path to the notebook file.
    """
    # Read the original notebook file
    with open(nb_filename, 'r', encoding='utf-8') as f:
        notebook = nbformat.read(f, as_version=4)

    new_cells = []
    form_id = 0

    for cell in notebook.cells:
        if cell.cell_type != 'code':
            # Preserve markdown cells
            new_cells.append(cell)
            continue

        # Skip cells that don't contain Colab form parameters
        if not re.search(r'.*=.*#\s*@param', cell.source):
            new_cells.append(cell)
            continue

        form_id += 1

        # Extract parameters from Colab form
        form_params = extract_parameters(cell.source)

        # Generate widgets code
        widgets_code, update_code = generate_widgets(form_params, form_id)

        # Remove lines related to Colab form parameters and title
        lines = [line for line
                 in cell.source.splitlines()
                 if '@param' not in line and '@title' not in line]
        remaining_code = '\n        '.join(lines)

        # Extract global variables from the remaining code
        global_vars = extract_global_vars('\n'.join(lines))
        global_line = f"global {', '.join(global_vars)}" if global_vars else ""

        # Combine widgets and remaining code into a new cell
        updated_source = f"""
import ipywidgets as widgets
from IPython.display import display
import pandas as pd
from widgetify import create_input_dropdown

{widgets_code}
submit_button{form_id} = widgets.Button(description="Submit")
display(submit_button{form_id})
voila_out{form_id} = widgets.Output()
display(voila_out{form_id})

def on_submit_clicked{form_id}(b):
    # Get parameter values from widgets
    {update_code}

    # Execute the remaining code
    with voila_out{form_id}:
        voila_out{form_id}.clear_output()

        # Global variables
        {global_line}

        {remaining_code}

submit_button{form_id}.on_click(on_submit_clicked{form_id})
"""
        new_cells.append(nbformat.v4.new_code_cell(source=updated_source))

    # Create a new notebook and write to the output file
    new_notebook = nbformat.v4.new_notebook()
    new_notebook.cells = new_cells
    with open(nb_filename, 'w', encoding='utf-8') as f:
        nbformat.write(new_notebook, f)


def extract_parameters(source_code):
    """
    Extract parameters from Colab form annotations in the given code.

    Args:
        source_code (str): The code from which to extract parameters.

    Returns:
        dict: A dictionary of parameter names and their corresponding types,
        options, and values.

    Examples:
        >>> extract_parameters('raw = ABC # @param {"type":"raw"}')
        {'raw': {'type': 'raw', 'value': 'ABC'}}
        >>> extract_parameters('string = "ABC" # @param {"type":"string"}')
        {'string': {'type': 'string', 'value': '"ABC"'}}
        >>> extract_parameters('num = 0 # @param {"type":"number"}')
        {'num': {'type': 'number', 'value': '0'}}
        >>> extract_parameters('integer = 0 # @param {"type":"integer"}')
        {'integer': {'type': 'integer', 'value': '0'}}
        >>> extract_parameters('date = "2024-09-19" # @param {"type":"date"}')
        {'date': {'type': 'date', 'value': '"2024-09-19"'}}
        >>> extract_parameters(
        ... 'slider=2 # @param {"type":"slider","min":0,"max":9,"step":1}')
        ...                         # doctest: +NORMALIZE_WHITESPACE
        {'slider': {'type': 'slider', 'min': '0', 'max': '9', 'step': '1',
                    'value': '2'}}
        >>> extract_parameters(
        ...     'stars = 5 # @param ["1","2","3","4","5"] {"type":"raw"}')
        ...                         # doctest: +NORMALIZE_WHITESPACE
        {'stars': {'type': 'raw',
                   'options': ['"1"', '"2"', '"3"', '"4"', '"5"'],
                   'value': '5', 'allow-input': False}}
    """
    assign_pat = re.compile(
        r'(?P<name>.+?)\s*=\s*(?P<value>.+?)\s*(#\s*@param.*)?$')
    options_pat = re.compile(r'#\s*@param\s*\[(.*)\]')
    type_pat = re.compile(
        r'#\s*@param.*\{\s*(?:type|"type")\s*:\s*"([^"]+)"\s*(?:,|})')
    slider_pat = re.compile(
        r'#\s*@param\s*\{\s*"type"\s*:\s*"slider"\s*,'
        r'\s*"min"\s*:(.*),\s*"max"\s*:(.*),\s*"step"\s*:(.*)\}')
    allow_input_pat = re.compile(
        r'#\s*@param.*\{\s*'
        r'(?:allow-input|"allow-input")\s*:\s*(true|false)\s*\}')

    form_params = {}
    for line in source_code.splitlines():
        # Check if the line contains an '=' and '# @param'
        assign_match = assign_pat.search(line)
        if not assign_match:
            continue

        # Extract the variable name and value part
        name = assign_match.group('name').strip()
        value = assign_match.group('value').strip()
        value = value.replace('"', "'")

        # Replace leading and trailing single quotes with double quotes
        value = re.sub(r"^'|'$", '"', value)

        options_match = options_pat.search(line)
        type_match = type_pat.search(line)
        if not options_match:
            slider_match = slider_pat.search(line)

        if options_match:
            allow_input_match = allow_input_pat.search(line)

            options = [opt.strip() for opt in options_match.group(1).split(",")]
            options = [opt.replace('"', "'") for opt in options]

            # Replace leading and trailing single quotes with double quotes
            options = [re.sub(r"^'|'$", '"', opt) for opt in options]

            type_name = type_match.group(1) if type_match else "string"
            form_params[name] = {
                "type": type_name,
                "options": options,
                "value": value,
                "allow-input": allow_input_match.group(1) == 'true'
                    if allow_input_match else False,
            }
            logger.info(f"form_params[{name}]: {form_params[name]}")
        elif slider_match:
            form_params[name] = {
                "type": "slider",
                "min": slider_match.group(1),
                "max": slider_match.group(2),
                "step": slider_match.group(3),
                "value": value,
            }
            logger.info(f"form_params[{name}]: {form_params[name]}")
        elif type_match:    # input box
            form_params[name] = {
                "type": type_match.group(1),
                "value": value,
            }
            logger.info(f"form_params[{name}]: {form_params[name]}")

    return form_params


def generate_widgets(form_params, form_id=""):
    r"""
    Generate ipywidgets code from the extracted form parameters.

    Args:
        form_params (dict): The extracted form parameters.
        form_id (int): The ID of the current form.

    Returns:
        tuple: A tuple containing the widget code as a string and the update
        code to extract values from the widgets.

    Examples:
        >>> params = extract_parameters('raw = ABC # @param {"type":"raw"}')
        >>> generate_widgets(params)
        ...                         # doctest: +NORMALIZE_WHITESPACE
        ("form = widgets.VBox([\n
            widgets.Text(value=ABC, description='raw'),\n])\ndisplay(form)\n",
        'raw = form.children[0].value')
    """
    widgets_code = f"form{form_id} = widgets.VBox([\n"
    for name, content in form_params.items():
        value = content['value']
        if "options" in content:
            options = [f"{opt}" for opt in content['options']]
            if content['type'] == 'raw':
                options = [opt.strip('"').strip("'") for opt in options]
            if value not in options:
                value = options[0]
            layout = "widgets.Layout(width='auto')"
            params = (f"options=[{', '.join(options)}], value={value}, "
                      f"description='{name}', layout={layout}")
            widgets_kind = {
                True: "create_input_dropdown",
                False: "widgets.Dropdown",
            }[content['allow-input']]
        else:
            if content['type'] == 'slider':
                params = (f"min={content['min']}, max={content['max']}, "
                        f"step={content['step']}, value={value}, "
                        f"description='{name}'")
            elif content['type'] == 'date':
                params = f"value=pd.to_datetime({value}), description='{name}'"
            elif content['type'] == 'raw':
                params = f"value=str({value}), description='{name}'"
            elif content['type'] in (
                    'string', 'number', 'integer', 'boolean'):
                params = f"value={value}, description='{name}'"
            widgets_kind = {
                'slider': "widgets.IntSlider",
                'date': "widgets.DatePicker",
                'string': "widgets.Text",
                'raw': "widgets.Text",
                'number': "widgets.FloatText",
                'integer': "widgets.IntText",
                'boolean': "widgets.Checkbox",
            }[content['type']]
        widgets_code += f"    {widgets_kind}({params}),\n"
    widgets_code += f"])\ndisplay(form{form_id})\n"

    update_code = "\n    ".join([f"{name} = form{form_id}.children[{i}].value"
                                 for i, name in enumerate(form_params.keys())])

    return widgets_code, update_code


def extract_global_vars(code):
    """
    Extracts global variable names from a given block of Python code. This
    function parses the code, identifies any variables declared as global or
    assigned at the top level, and returns their names as a set.

    Args:
        code (str): A string containing Python code from which global variables
                    should be extracted.

    Returns:
        set: A set of global variable names found in the provided code.
    """
    global_vars = set()

    class GlobalVarVisitor(ast.NodeVisitor):
        def visit_Global(self, node):
            global_vars.update(node.names)

    class AssignVisitor(ast.NodeVisitor):
        def visit_Assign(self, node):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    global_vars.add(target.id)

    tree = ast.parse(code)
    GlobalVarVisitor().visit(tree)
    AssignVisitor().visit(tree)

    return global_vars


if __name__ == "__main__":
    import doctest
    doctest.testmod()
