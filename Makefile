# GNU makefile.

.PHONY: clean, wheel, pypi, test

test:
	cd src ; python3 runtests.py

wheel:
	python3 -m build
	mv dist/*.whl .

pypi:
	python3 -m build
	twine upload dist/*

clean:
	-rm *.whl *.tar.gz
	rm -rf build dist src/*.egg-info
	find . | grep -E "(__pycache__|\.pyc|\.pyo$$)" | xargs rm -rf
