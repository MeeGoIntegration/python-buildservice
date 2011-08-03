# ex: set tabstop=4 noexpandtab: 
VERSION = $(shell cat VERSION)
NAME=python-buildservice
TAGVER = $(shell cat VERSION | sed -e "s/\([0-9\.]*\).*/\1/")

ifeq ($(VERSION), $(TAGVER))
        TAG = $(TAGVER)
else
        TAG = "HEAD"
endif

PYTHON=python

all: 
	python setup.py build

install: all
	python setup.py install

develop: all
	python setup.py develop

tag:
	git tag $(TAGVER)

dist-bz2:
	git archive --format=tar --prefix=$(NAME)-$(TAGVER)/ $(TAG) | \
		bzip2  > $(NAME)-$(TAGVER).tar.bz2

dist-gz:
	git archive --format=tar --prefix=$(NAME)-$(TAGVER)/ $(TAG) | \
		gzip  > $(NAME)-$(TAGVER).tar.gz

dist: dist-bz2

clean:
	rm -f *.pyc *.pyo
