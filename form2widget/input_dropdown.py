"""
input_dropbox - Creating Jupyter Widgets with user input capability.

This module provides a function `create_input_dropdown` to create an
interactive Jupyter Widget that mimics the behavior of a Colab Form dropdown
with user input enabled. The widget includes both a dropdown menu and an input
box, allowing users to select from a list of options or type their own input,
which is reflected in both the dropdown and the input box.

Usage:
    Import this module and call `create_input_dropdown` to generate a widget
    box with a dropdown and input field suitable for Jupyter environments.

Example:
::

    import input_dropbox as idb

    # Define options and initial value
    options = ['Option 1', 'Option 2', 'Option 3']
    initial_value = 'Option 1'
    description = 'Select an option:'

    # Create the widget
    dropdown = idb.create_input_dropdown(options, initial_value, description)

    # Display the widget
    display(dropdown)

    print(dropdown.value)
"""
__author__ = "York <york.jong@gmail.com>"
__date__ = "2024/09/19 (initial version) ~ 2024/09/19 (last revision)"

__all__ = [
    'create_input_dropdown',
]

import ipywidgets as widgets


def create_input_dropdown(options, value, description,
                          layout=widgets.Layout(width='auto')):
    """
    Create a dropdown widget that allows user input, mimicking a Colab Form
    dropdown with the `{"allow-input": true}` setting.

    Args:
        options (list): A list of options to be displayed in the dropdown.
        value (str): The initial value of the dropdown, which should be one of
            the options.
        description (str): The description (label) to be displayed next to the
            dropdown.
        layout (widgets.Layout, optional): A layout object to control the size
            and appearance of the dropdown and input box. Default is a layout
            with width set to 'auto'.

    Returns:
        widget_box (HBox): An HBox containing the dropdown and an input box,
            with a value property to get/set the dropdown value.
    """
    dropdown = widgets.Dropdown(
        options=options,
        value=value if value in options else None,
        description=description,
        layout=layout,
    )
    input_box = widgets.Text(
        description='',
        placeholder='Type to Input',
        layout=layout,
    )

    def update_dropdown(change, dropdown, options):
        '''Update the options in the dropdown based on search input'''
        input = change['new']
        if input not in options:
            dropdown.options = [input] + options
        dropdown.value = input

    def update_input_box(change, input_box):
        '''Update the search box based on the selected option in the dropdown'''
        selected = change['new']
        if selected:
            input_box.value = selected

    input_box.observe(lambda change:
                       update_dropdown(change, dropdown, options),
                       names='value')
    dropdown.observe(lambda change:
                     update_input_box(change, input_box),
                     names='value')

    widget_box = widgets.HBox([dropdown, input_box])

    # Define the property getter for value
    @property
    def value(self):
        return self.children[0].value

    # Define the property setter for value
    @value.setter
    def value(self, new_value):
        self.children[0].value = new_value

    # Patch the widget_box to have the value property
    type(widget_box).value = value

    return widget_box

