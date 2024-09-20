from setuptools import setup, find_packages
import os.path


def get_version(rel_path):
    """Get version from a file with __version__ assignment statement.
    """
    base_path = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(base_path, rel_path), 'r') as fp:
        for line in fp:
            if line.startswith('__version__'):
                delim = '"' if '"' in line else "'"
                return line.split(delim)[1]
    raise RuntimeError("Unable to find version string.")


setup(
    name = 'widgetify',
    version = get_version('widgetify/__init__.py'),
    license = 'MIT',
    author = 'York Jong',
    author_email = 'york.jong@gmail.com',
    description = 'Google Colab Forms into Jupyter Widgets Converter',
    long_description = open('README.md').read(),
    python_requires = '>=3.6',
    packages = find_packages(),
    install_requires = [
        'ipywidgets',
        'nbformat',
    ],
)

