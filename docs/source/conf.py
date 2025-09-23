# --- Path setup ---
import os
import sys
from datetime import datetime

# Шлях до проекту (корінь, де лежить src/, main.py, etc.)
sys.path.insert(0, os.path.abspath('../..'))   # корень проекта
sys.path.insert(0, os.path.abspath('../../src'))  # src/


# --- Project information ---
project = 'Contacts API'
author = 'Andrew Tarnavsky'
current_year = datetime.now().year
copyright = f'{current_year}, {author}'
release = '2.0.0'


# --- Sphinx-style ---
""" reStructuredText (RST / Sphinx-style) """
# NumPy-style
# Google-style


# --- General configuration ---
extensions = [
    'sphinx.ext.autodoc',         # автогенерація документації з docstrings
    # 'sphinx.ext.napoleon',        # підтримка Google / NumPy стилів docstrings 
    'sphinx.ext.viewcode',        # кнопка “view source” 
    'sphinx.ext.autosectionlabel',# посилання на заголовки через їх текст 
    'sphinx.ext.intersphinx',     # посилання на зовнішні доки (наприклад, Python)
    'sphinx_autodoc_typehints',   # красиві type hints в описах 
    'sphinx.ext.todo',            # опціонально: TODO-блоки
]


# --- Autosectionlabel ---
autosectionlabel_prefix_document = True  # унікальні якорі


# --- Nitpick fixes ---
# баг з SQLAlchemy metadata
suppress_warnings = [
    "autosectionlabel.*",  # ігнор дублікатів заголовків
    "ref.ref",  # ігнор "undefined label: 'orm_declarative_metadata'"
]


# --- Syntax highlighting ---
pygments_style = "sphinx"
pygments_dark_style = "monokai"


# # Napoleon (щоб :param: / :rtype: і Google/Numpy-стилі працювали)
# napoleon_google_docstring = True
# napoleon_numpy_docstring = False
# napoleon_include_init_with_doc = False
# napoleon_use_param = True
# napoleon_use_rtype = True


# --- Autodoc ---
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
    "exclude-members": "Config, model_config",
}


# --- Autodoc config ---
# Анотації типів: рендерим в описі, а не в сигнатурі (читабельніше)
autodoc_typehints = 'description'
# Autodoc - порядок членів та дефолтні опції
autodoc_member_order = "bysource"
# Модулі, які не потрібно імпортувати при складанні
autodoc_mock_imports = [
    "check_smtp",
    "seed",
    "parse_jwt",
]
suppress_warnings = ["autodoc.mocked_object"]

nitpick_ignore = [
    ("py:attr", "orm_declarative_metadata"),
]


# Intersphinx – для посилань на стандартну бібліотеку Python
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "fastapi": ("https://fastapi.tiangolo.com/", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
}


# --- Templates / static ---
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
html_static_path = ["_static"]
html_css_files = ["custom.css"]


# --- HTML theme ---
html_theme = "nature"  # або 'alabaster', 'furo', 'sphinx_rtd_theme', 'nature'


# TODO-блоки, якщо вони використовуються.. todo:: у доках
todo_include_todos = True

