# GNU makefile.

.PHONY: clean, wheel, pypi, test

test:
	cd src ; python3 runtests.py

dist: src
	rm -rf dist
	python3 -m build

wheel: dist
	cp dist/*.whl .

pypi: dist
	twine upload dist/*

clean:
	-rm *.whl *.tar.gz
	rm -rf build dist src/*.egg-info
	find . | grep -E "(__pycache__|\.pyc|\.pyo$$)" | xargs rm -rf
