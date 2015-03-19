SRCS := $(wildcard *.txt)
HTML := $(SRCS:%.txt=html/%.html)
MANS := $(SRCS:%.txt=man/%)
ASCIIDOC := $(shell which asciidoctor asciidoc | head -1)

all: doc

doc: html man

html: $(HTML)

man: $(MANS)

html_dir:
	mkdir -p html
	cp stylesheets/rdo.css html/

man_dir:
	mkdir -p man

html/%.html: %.txt | html_dir
	$(ASCIIDOC) -b html5 -a stylesheet=rdo.css -o $@ $<

man/%: %.txt | man_dir
	a2x --doctype manpage --format manpage -D man $<

clean:
	rm -rf man html

.PHONY: html man
