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
def test(c):
    """Build, install, and then run unit tests."""
    c.run('hatch run test:run')


@task()
def deploy(c):
    """Upload all artifacts in dist/ to PyPI."""
    c.run('twine upload dist/*')
