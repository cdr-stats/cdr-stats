#
# Usage:
#   ./update_version.sh 3.0.0
#

git flow release start v$1

sed -i -e "s/VERSION = '.*'/VERSION = '$1'/g" cdr_stats/cdr_stats/__init__.py

#rm -rf docs/html
#python setup.py develop
#make docs

git commit -a -m "Update to version v$1"
git flow release finish v$1
#python setup.py sdist upload -r pypi

git push origin develop; git push origin master; git push --tags
