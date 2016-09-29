SRCS := $(wildcard *.adoc)
HTML := $(SRCS:%.adoc=html/%.html)
MANS := $(SRCS:%.adoc=man/%)
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

html/%.html: %.adoc | html_dir
	$(ASCIIDOC) -b html5 -a stylesheet=rdo.css -o $@ $<

man/%: %.adoc | man_dir
	a2x --doctype manpage --format manpage -D man $<

clean:
	rm -rf man html

.PHONY: html man
