all: dist

doc:
	make -C doc/

dist:   doc
	python setup.py sdist

clean:
	rm -rf dist/ build/ doc/{html,man} rdopkg.egg-info

.PHONY: dist doc
