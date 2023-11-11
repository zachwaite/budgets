SHELL := /bin/bash
.ONESHELL:

.PHONY: clean reload watch build rebuild

build/budget.html: src/build.py src/budget.html.j2
	python3 src/build.py src/budget.html.j2 src/budget.yml \
		--title="Quick Budget - $(shell pwd | xargs basename)" \
		> ./build/budget.html

build/budget.pdf: build/budget.html
	wkhtmltopdf --page-size Letter ./build/budget.html ./build/budget.pdf 

build: build/budget.html build/budget.pdf

devbuild: src/build.py src/budget.html.j2
	python3 src/build.py src/budget.html.j2 src/budget.yml \
		--title="Quick Budget - $(shell pwd | xargs basename)" \
		> ./build/budget.html

serve:
	./hot-reload

reload:
	curl "http://localhost:8000/reload"

watch:
	while true; do\
		inotifywait -qr -e modify -e create -e delete -e move "./src";\
		make devbuild
		make reload;\
	done

clean:
	rm -rf ./build
	mkdir ./build

