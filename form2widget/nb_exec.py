"""
Executing Notebook Cells

This module provides functionality to execute Jupyter notebook code cells
programmatically. It offers the ability to run code cells in a notebook,
handling shell commands, IPython magic commands, and standard Python code.

Usage:
    The module is intended to work with Jupyter notebooks, allowing for the
    programmatic execution of code cells, either individually or in batches.
"""
__author__ = "York <york.jong@gmail.com>"
__date__ = "2024/09/19 (initial version) ~ 2024/09/19 (last revision)"

__all__ = [
    'run_code_cells',
    'run_code_cell',
]

import os

from IPython import get_ipython


def run_code_cells(cells):
    """Execute a list of Jupyter code cells.

    This function iterates over a list of Jupyter notebook cells and executes
    any cell with the type `'code'`. Non-code cells (e.g., markdown or raw)
    are ignored.

    Args:
        cells (list of nbformat.NotebookNode): A list of Jupyter notebook cell
        objects. The function will execute only the cells where `cell_type`
        is `'code'`.

    Returns:
        None: The function executes the code in the cells in the current
        environment but does not return any output.
    """
    for cell in cells:
        if cell.cell_type == 'code':
            run_code_cell(cell)


def run_code_cell(cell):
    """Executes a Jupyter notebook code cell, handling Python, shell, and magic
    commands.

    Args:
        cell (nbformat.NotebookNode): A notebook cell object, typically from
        a Jupyter notebook. The function only processes cells with
        `cell_type` set to `'code'`.

    Returns:
        None: The function executes the cell in the current environment, but
        does not return any output.
    """
    if cell.cell_type != 'code':
        return

    code = cell.source.strip()
    lines = code.split('\n')

    # Buffer to accumulate Python code lines
    python_code = []

    for line in lines:
        line = line.strip()
        if line.startswith('!'):
            # First, execute any accumulated Python code
            if python_code:
                try:
                    exec('\n'.join(python_code), globals())
                except Exception as e:
                    print(f"Error executing Python code: {e}")
                python_code = []  # Clear the buffer

            # Execute the shell command
            os.system(line[1:])

        elif line.startswith('%'):
            # First, execute any accumulated Python code
            if python_code:
                try:
                    exec('\n'.join(python_code), globals())
                except Exception as e:
                    print(f"Error executing Python code: {e}")
                python_code = []  # Clear the buffer

            # Execute the magic command
            magic_command = line[1:].split()[0]
            magic_args = ' '.join(line.split()[1:])
            try:
                get_ipython().run_line_magic(magic_command, magic_args)
            except Exception as e:
                print(f"Error executing magic command: {e}")

        else:
            # Accumulate Python code
            python_code.append(line)

    # After the loop, execute any remaining Python code
    if python_code:
        try:
            exec('\n'.join(python_code), globals())
        except Exception as e:
            print(f"Error executing Python code: {e}")

