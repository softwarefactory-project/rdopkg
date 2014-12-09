SRCS := $(wildcard *.txt)
HTML := $(SRCS:%.txt=html/%.html)
MANS := $(SRCS:%.txt=man/%)

all: doc

doc: html man

html: $(HTML)

man: $(MANS)

html_dir:
	mkdir -p html

man_dir:
	mkdir -p man

html/%.html: %.txt | html_dir
	asciidoc -b html5 -a theme=flask -o $@ $<

man/%: %.txt | man_dir
	a2x --doctype manpage --format manpage -D man $<

clean:
	rm -rf man html

.PHONY: html man
