#
#Makefile - Why not :)
#

SHELL := /bin/bash
VERSION = $(shell python setup.py --version)

DB_NAME=cdrstatsdb
DB_OPTS=
PRJ_DIR=./cdr_stats

all:
	@echo "See Makefile source for targets details"

recreate-static: clean-static create-static

create-static:
	cd $(PRJ_DIR) && ./manage.py collectstatic --noinput

#clean-static:
#	cd $(PRJ_DIR) && echo rm -rf $(dirname $(shell ./manage.py findstatic site.js))

makeallmessages:
	cd $(PRJ_DIR) && ./manage.py makemessages -s -a -e ".html,.txt"

compilemessages:
	cd $(PRJ_DIR) && ./manage.py compilemessages

test:
	python setup.py nosetests

release:
	git tag $(VERSION)
	git push origin $(VERSION)
	git push origin master
	python setup.py sdist upload

lint-js:
	# Check JS for any problems
	# Requires jshint
	jshint ${STATIC_DIR}/js/mycode.js

watch:
	bundle exec guard

runlocal: kill_server
	cd $(PRJ_DIR) && python manage.py runserver 0.0.0.0:8000

kill_server:
	@if /usr/sbin/lsof -i :8000; then \
		echo "WARNING: A server was already listening on port 8000, I'm trying to kill it"; \
		kill -9 `/usr/sbin/lsof -i :8000 -Fp|cut -c2-`; \
	fi

clean:
	find $(PRJ_DIR) -type f -name "*.pyc" -exec rm -rf \{\} \;

cleardb: clean
	-dropdb $(DB_NAME) $(DB_OPTS)
	createdb $(DB_NAME) $(DB_OPTS) -E UTF-8 -T cdrstatsdb

reset: cleardb
	cd $(PRJ_DIR) && python manage.py syncdb --noinput
	cd $(PRJ_DIR) && python manage.py loaddata fixtures/auth.json
	@echo 'Login as admin/admin'

graph_models:
	cd $(PRJ_DIR) && python manage.py graph_models -a -g -o project_models.png

doc_html:
	cd docs && rm -rf build/html && rm -rf build/doctrees && make html

doc_pdf:
	cd docs && rm -rf build/latex && rm -rf build/doctrees && make latexpdf
