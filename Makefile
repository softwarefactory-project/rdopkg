NAME = rdopkg
RPM_DIRS = --define "_sourcedir `pwd`/dist" \
           --define "_rpmdir `pwd`/dist" \
           --define "_specdir `pwd`" \
           --define "_builddir `pwd`/dist" \
           --define "_srcrpmdir `pwd`/dist"

all: srpm

doc:
	make -C doc/

dist:   doc
	python setup.py sdist

clean:
	rm -rf dist/ doc/{html,man} rdopkg.egg-info

rpm: dist $(NAME).spec
	rpmbuild $(RPM_DIRS) -ba $(NAME).spec

srpm: dist $(NAME).spec
	rpmbuild $(RPM_DIRS) -bs $(NAME).spec

.PHONY: dist doc rpm srpm
