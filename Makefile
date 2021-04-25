# GNU makefile.

.PHONY: clean, wheel, test

test:
	cd src ; python3 runtests.py

wheel:
	python3 -m build
	mv dist/*.whl .

clean:
	-rm *.whl *.tar.gz
	rm -rf build dist src/*.egg-info
