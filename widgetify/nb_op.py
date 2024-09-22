"""
Notebook Operations (nb_op)

This module provides utilities for performing common operations on Jupyter
Notebooks using `nbformat`, such as inserting titles, removing sections,
commenting code cells, and more. It is designed to automate notebook
modifications like inserting markdown titles, removing specific sections, and
handling Colab-specific cells.
"""
__author__ = "York <york.jong@gmail.com>"
__date__ = "2024/09/19 (initial version) ~ 2024/09/19 (last revision)"

__all__ = [
    'insert_title_cells',
    'remove_open_in_colab_cell',
    'extract_and_comment_first_code_cell',
    'search_section',
    'extract_section',
    'remove_section',
]

import re
import logging

import nbformat
from nbformat.corpus.words import generate_corpus_id as random_cell_id

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def insert_title_cells(nb_filename):
    """
    Insert a markdown title cell above each Colab Form or widgets cell.

    The title cell is created with a level 4 heading (####) and the title
    extracted from the Colab Form's '@title' annotation. The title cell is added
    above any code  cell that contains Colab Form parameters or ipywidgets
    display calls.

    Args:
        nb_filename (str): The path to the notebook file to modify.
    """
    # Read the original notebook file
    with open(nb_filename, 'r', encoding='utf-8') as f:
        notebook = nbformat.read(f, as_version=4)

    new_cells = []

    for cell in notebook.cells:
        if cell.cell_type == 'code':
            # Initialize an empty string for the title line
            title_line = ''

            # Check if the cell contains Colab Form or ipywidgets code
            if (re.search(r'.*=.*#\s*@param', cell.source) or
                all(keyword in cell.source
                    for keyword in ['ipywidgets', '\ndisplay('])):

                # Extract the title from the @title annotation
                for line in cell.source.splitlines():
                    if '@title' in line:
                        title_line = line.split('@title')[1].strip()
                        title_line = title_line.split("{")[0].strip()
                        break

            # If the title line is just '_', set it to an empty string
            if title_line == '_':
                title_line = ''

            # Create and insert a markdown cell with the valid title
            if title_line:
                title_markdown = f"#### {title_line}"
                logger.info(title_markdown)
                md_cell = nbformat.v4.new_markdown_cell(source=title_markdown)

                # Move the 'id' field from the top-level to the 'metadata' field
                # This is done to match the format used by Colab, where 'id' is
                # placed in 'metadata'
                md_cell["metadata"]["id"] = md_cell['id']
                del md_cell['id']

                new_cells.append(md_cell)

        # Add all cells (including the newly inserted markdown cells)
        new_cells.append(cell)

    # Update the notebook with the new cells
    notebook.cells = new_cells

    #n_changes, notebook = nbformat.validator.normalize(notebook)
    #logger.debug(f"Normalized {n_changes} cells")
    #nbformat.validator.validate(notebook)

    # Write the modified notebook back to the file
    with open(nb_filename, 'w', encoding='utf-8') as f:
        nbformat.write(notebook, f)


def remove_open_in_colab_cell(nb_filename):
    """Remove the open-in-colab cell from a Jupyter notebook.

    Args:
        nb_filename (str): The path to the notebook file to modify.
    """
    # Read the original notebook file
    with open(nb_filename, 'r', encoding='utf-8') as f:
        notebook = nbformat.read(f, as_version=4)

    new_cells = []

    for cell in notebook.cells:
        # Check if the cell is a markdown cell with specific content to remove
        if cell.cell_type == 'markdown':
            if 'alt=\"Open In Colab\"' in cell.source:
                continue  # Skip this cell

        # Add all other cells to the new list
        new_cells.append(cell)

    # Update the notebook with the remaining cells
    notebook.cells = new_cells

    # Write the modified notebook to the output file
    with open(nb_filename, 'w', encoding='utf-8') as f:
        nbformat.write(notebook, f)


def extract_and_comment_first_code_cell(nb_filename):
    """Extracts the first code cell from a Jupyter Notebook file, comments out
    its content, and writes the modified notebook back to the file.

    Args:
        nb_filename (str): The path to the notebook file.

    Returns:
        nbformat.notebooknode.NotebookNode: The first code cell, or None if no
        code cell is found. The returned cell is an instance of NotebookNode,
        which behaves like a dictionary but is used by nbformat to represent
        notebook elements.
    """
    # Read the original notebook file
    with open(nb_filename, 'r', encoding='utf-8') as f:
        notebook = nbformat.read(f, as_version=4)

    # Find the first code cell
    first_code_cell = None
    for cell in notebook.cells:
        if cell.cell_type == 'code':
            first_code_cell = cell.copy()
            # Comment out the first block of code
            cell.source = '\n'.join([f"# {line}" for line
                                     in cell.source.splitlines()])
            break

    # Save the modified notebook
    if first_code_cell:
        with open(nb_filename, 'w', encoding='utf-8') as f:
            nbformat.write(notebook, f)
    else:
        logger.error("No code cell found")

    return first_code_cell


def search_section(nb_filename, text):
    """Search for a markdown section in a Jupyter Notebook file containing
    the specified text.

    The function searches through the markdown cells in the notebook for a
    heading that includes the given text. If a match is found, the full line
    containing the heading is returned.

    Args:
        nb_filename (str): The path to the notebook file.
        text (str): The text to search for within the markdown headings.

    Returns:
        str: The full line of the heading that contains the search text, or
        None if no matching heading is found.

    Note:
        The function searches only in markdown cells and checks if the line
        starts with a heading marker (e.g., '#', '##').
    """
    # Read the original notebook file
    with open(nb_filename, 'r', encoding='utf-8') as f:
        notebook = nbformat.read(f, as_version=4)

    for cell in notebook.cells:
        if cell.cell_type == 'markdown':
            for line in cell.source.splitlines():
                if line.startswith('#') and text in line:
                    return line
    return None


def extract_section(nb_filename, section_name, markdown_only=False):
    """Extract a specific section and its content from a Jupyter Notebook.

    This function searches for a section within the notebook based on the
    provided section name (heading) and extracts the cells that belong to
    that section. The extraction starts from the specified section and
    includes all subsequent cells until a heading of the same or higher level
    is encountered.

    Args:
        nb_filename (str): The path to the Jupyter Notebook file.
        section_name (str): The name of the section to extract, including the
            heading level (e.g., '## Section Name').
        markdown_only (bool, optional): If True, only markdown cells will be
            considered for extraction. Defaults to False.

    Returns:
        list: A list of `nbformat.NotebookNode` objects, representing the
        extracted cells belonging to the specified section. If the section
        is not found, an empty list is returned.

    Note:
        The function matches the `section_name` exactly, including the
        heading level (indicated by '#'). The extraction stops when it
        encounters a heading of the same or higher level than the given
        section's heading.
    """
    # Read the original notebook file
    with open(nb_filename, 'r', encoding='utf-8') as f:
        notebook = nbformat.read(f, as_version=4)

    # Calculate the section level from the section name
    section_level = section_name.split(' ')[0].count('#')

    extract_cells = []
    extract_mode = False
    start_extract = False

    for cell in notebook.cells:
        if cell.cell_type == 'markdown':
            lines = cell.source.splitlines()
            # Calculate the heading level of the current markdown cell
            heading_level = next(
                (line.split(' ')[0].count('#') for line in lines
                 if line.strip().startswith('#')),
                None
            )

            # Detect if the cell matches the section to start extracting
            if not start_extract:
                if any(section_name in line for line in lines):
                    start_extract = True
                    extract_mode = True  # Start extracting this section
            elif extract_mode:
                if heading_level is not None and heading_level <= section_level:
                    break

        if extract_mode:
            if markdown_only:
                if cell.cell_type == 'markdown':
                    extract_cells.append(cell)
            else:
                extract_cells.append(cell)

    return extract_cells


def remove_section(nb_filename, section_name, markdown_only=False):
    """Remove a specific section and its content from a Jupyter Notebook.

    This function removes a section and all its subsequent cells from the
    notebook, starting from the specified section until it encounters a
    heading of the same or higher level.

    Args:
        nb_filename (str): The path to the Jupyter Notebook file.
        section_name (str): The name of the section to remove, including the
            heading level (e.g., '## Section Name').
        markdwn_only (bool, optional): If True, only markdown cells will be
            considered for extraction. Defaults to False.

    Returns:
        None: The function modifies the notebook in place and writes the
        changes back to the file.

    Note:
        The section is identified by its exact heading (including the level
        of '#'). Once a matching section is found, the removal will continue
        until a markdown heading of the same or higher level is encountered.
        The rest of the notebook content will remain unchanged.
    """
    # Read the original notebook file
    with open(nb_filename, 'r', encoding='utf-8') as f:
        notebook = nbformat.read(f, as_version=4)

    # Calculate the section level from the section name
    section_level = section_name.split(' ')[0].count('#')

    new_cells = []
    remove_mode = False
    start_removal = False

    for cell in notebook.cells:
        if cell.cell_type == 'markdown':
            lines = cell.source.splitlines()
            # Calculate the heading level of the current markdown cell
            heading_level = next(
                (line.split(' ')[0].count('#') for line in lines
                 if line.strip().startswith('#')),
                None
            )

            # Detect if the markdown cell matches the section to start removing
            if not start_removal:
                if any(section_name in line for line in lines):
                    start_removal = True
                    remove_mode = True  # Start removing this section
                    continue

            # Stop removing when the markdown heading level is less than or
            # equal to the section_level
            if (remove_mode and heading_level is not None
                and heading_level <= section_level):
                remove_mode = False

        if remove_mode:
            # Remove markdown cell only i.e., keep code cell and raw cell
            if markdown_only and (cell.cell_type != 'markdown'):
                new_cells.append(cell)
        else:
            new_cells.append(cell)

    # Update the notebook with the remaining cells
    notebook.cells = new_cells

    # Write the modified notebook to the output file
    with open(nb_filename, 'w', encoding='utf-8') as f:
        nbformat.write(notebook, f)

