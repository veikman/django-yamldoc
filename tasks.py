"""Recurring tasks used to organize the project.

http://www.pyinvoke.org/

"""

from invoke import task


@task()
def clean(c):
    """Destroy prior artifacts."""
    c.run('rm dist/*', warn=True)
    c.run('rmdir dist', warn=True)


@task(pre=[clean])
def build(c):
    """Build wheel in dist/."""
    c.run('python -m build')


@task()
def deploy(c):
    """Upload all artifacts in dist/ to PyPI."""
    c.run('twine upload dist/*')
