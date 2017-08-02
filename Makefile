define HELPBODY
Available commands:

	make help       - this thing.

	make init       - install python dependencies
	make build      - build for cli
	make clean      - clean build and pyc

endef

export HELPBODY
help:
	@echo "$$HELPBODY"

init:
	pip install -r requirements.txt

build:
	python setup.py install

clean:
	rm -rf dist build ethereumd.egg-info ethereumd/*.pyc *.pyc .cache .tox .coverage coverage.*