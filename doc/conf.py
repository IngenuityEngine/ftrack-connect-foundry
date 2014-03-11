# :coding: utf-8
# :copyright: Copyright (c) 2013 ftrack

'''ftrack connect The Foundry documentation build configuration file'''

import os
import re

import sphinx_rtd_theme

# -- General ------------------------------------------------------------------

# Extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.extlinks',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
]

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'ftrack connect The Foundry'
copyright = u'2013, ftrack'

# Version
_setup_path = os.path.join(os.path.dirname(__file__), '..', 'setup.py')
with open(_setup_path) as _setup_file:
    _version = re.match(
        r'.*version=\'(.*?)\'', _setup_file.read(), re.DOTALL
    ).group(1)

version = _version
release = _version

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['_template', '_theme']

# A list of prefixes to ignore for module listings
modindex_common_prefix = ['ftrack_connect_foundry.']


# -- HTML output --------------------------------------------------------------

html_theme = 'sphinx_rtd_theme'
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

html_theme_options = {
    'sticky_navigation': True,
}

# If True, copy source rst files to output for reference.
html_copy_source = True


# -- Autodoc ------------------------------------------------------------------

autodoc_default_flags = ['members', 'undoc-members', 'show-inheritance']
autodoc_member_order = 'bysource'

def autodoc_skip(app, what, name, obj, skip, options):
    '''Don't skip __init__ method for autodoc.'''
    if name == '__init__':
        return False

    return skip


# -- Intersphinx --------------------------------------------------------------

intersphinx_mapping = {'python': ('http://docs.python.org/', None)}


# -- Setup --------------------------------------------------------------------

def setup(app):
    app.connect('autodoc-skip-member', autodoc_skip)
