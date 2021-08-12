"""Recurring tasks used to organize the project.

http://www.pyinvoke.org/

"""

from invoke import task


@task()
def clean(c):
    """Destroy prior artifacts."""
    c.run('rm *.whl *.tar.gz dist/*', warn=True)
    c.run('rmdir build dist src/*.egg-info', warn=True)
    c.run(r'find . | grep -E "(__pycache__|\.pyc|\.pyo$$)" | xargs rm -rf')


@task(pre=[clean])
def build(c):
    """Build wheel in dist/."""
    c.run('python -m build')


@task(pre=[build])
def test(c):
    """Build, install, and then run unit tests."""
    with c.cd('dist'):
        c.run('sudo pip install --force-reinstall *.whl')
    with c.cd('src'):
        c.run('python runtests.py')


@task()
def deploy(c):
    """Upload all artifacts in dist/ to PyPI."""
    c.run('twine upload dist/*')
