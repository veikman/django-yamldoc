"""Recurring tasks used to organize the project.

http://www.pyinvoke.org/

"""

from invoke import task


@task()
def clean(c):
    """Destroy prior artifacts, but not all Git-uncontrolled files."""
    c.run('rm -rf build dist src/*.egg-info', warn=True)
    c.run(r'find . | grep -E "(__pycache__|\.pyc|\.pyo$$)" | xargs rm -rf')


@task(pre=[clean])
def build(c):
    """Build wheel in dist/."""
    c.run('hatch build')


@task()
def static(c, fix=False):
    """Run static analysis, including format and type checks.

    With -f, apply all available automatic fixes, including unsafe fixes that
    can affect the abstract syntax tree (AST).

    """
    c.run('hatch run static:type')
    if fix:
        c.run('hatch run static:fix_ast')
        c.run('hatch run static:fix_nonast')
    else:
        c.run('hatch run static:check_ast')
        c.run('hatch run static:check_nonast')


@task()
def test(c):
    """Run unit tests in supported versions."""
    c.run('hatch run test:run')


@task()
def deploy(c):
    """Upload all artifacts in dist/ to PyPI."""
    c.run('twine upload dist/*')
