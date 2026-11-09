"""The repository installs as the package cpp_xer_parser.

pyproject.toml maps scripts/ to the package cpp_xer_parser. These checks
load scripts/ as that package, the way an installed copy is imported, so
they run without building anything: the relative imports bind validation
and config_profiles inside the package, and the names __init__ exports
exist. The CI package job builds the wheel, installs it in a clean
environment and runs the console script.
"""
import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPTS = os.path.join(ROOT, 'scripts')


def _load_as_package():
    for name in [n for n in sys.modules if n == 'cpp_xer_parser'
                 or n.startswith('cpp_xer_parser.')]:
        del sys.modules[name]
    spec = importlib.util.spec_from_file_location(
        'cpp_xer_parser', os.path.join(SCRIPTS, '__init__.py'),
        submodule_search_locations=[SCRIPTS])
    pkg = importlib.util.module_from_spec(spec)
    sys.modules['cpp_xer_parser'] = pkg
    spec.loader.exec_module(pkg)
    return pkg


def test_the_package_binds_its_own_helpers():
    pkg = _load_as_package()
    xp = sys.modules['cpp_xer_parser.xer_parser']
    assert xp._VALIDATION_AVAILABLE is True
    # The helpers are the package's, not top-level modules.
    assert xp.get_profile.__module__ == 'cpp_xer_parser.config_profiles'
    assert xp.ValidationReport.__module__ == 'cpp_xer_parser.validation'
    for name in pkg.__all__:
        assert hasattr(pkg, name), name


def test_the_version_agrees_everywhere():
    # tomllib is 3.11+; the project supports 3.10, so read the one line.
    with open(os.path.join(ROOT, 'pyproject.toml'), encoding='utf-8') as f:
        version = re.search(r'(?m)^version = "([^"]+)"$', f.read()).group(1)
    pkg = _load_as_package()
    assert pkg.__version__ == version
    with open(os.path.join(ROOT, 'CHANGELOG.md'), encoding='utf-8') as f:
        assert ('## v%s ' % version) in f.read()


def test_a_clone_still_imports_the_top_level_modules():
    sys.path.insert(0, SCRIPTS)
    try:
        import xer_parser
        assert xer_parser._VALIDATION_AVAILABLE is True
    finally:
        sys.path.remove(SCRIPTS)
