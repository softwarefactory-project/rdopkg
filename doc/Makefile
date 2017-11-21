SRCS := $(wildcard *.adoc)
FEATURES_ABS := $(wildcard ../features/*.feature)
FEATURES := $(notdir ${FEATURES_ABS})
FEATURESADOC := $(FEATURES:%.feature=rdopkg-feature-%.7.adoc)
HTML := $(SRCS:%.adoc=html/%.html)
FEATURESHTML := $(FEATURESADOC:%.adoc=html/%.html)
MANS := $(SRCS:%.adoc=man/%)
FEATURESMAN := $(FEATURESADOC:%.adoc=man/%)
ASCIIDOC := $(shell which asciidoctor asciidoc | head -1)

all: doc

print-%  : ; @echo $* = $($*)

doc: html man

html: $(HTML) $(FEATURESHTML)

man: $(MANS) $(FEATURESMAN)

html_dir:
	mkdir -p html
	cp stylesheets/rdo.css html/

man_dir:
	mkdir -p man

html/rdopkg-feature-%.7.html: ../features/%.feature | html_dir
	python gherkin-parser.py $<
	$(ASCIIDOC) -b html5 -a stylesheet=rdo.css -o $@ $(@F:%.html=%.adoc)

html/%.html: %.adoc | html_dir
	$(ASCIIDOC) -b html5 -a stylesheet=rdo.css -o $@ $<

man/rdopkg-feature-%.7: ../features/%.feature | man_dir
	python gherkin-parser.py $<
	a2x --doctype manpage --format manpage -D man $(@F).adoc

man/%: %.adoc | man_dir
	a2x --doctype manpage --format manpage -D man $<

clean:
	rm -rf man html
	rm rdopkg-feature-*.7.adoc

.PHONY: html man
