#!/usr/bin/env bash

commands=(test debug bandit version pypi testpypi)
usage="Usage: $0 <command>
  commands: ${commands[*]}"


version_update () {
  version=$(grep "^version" pyproject.toml | cut -d '"' -f2)
  echo "__version__ = \"$version\"" > ./src/gcpm/__version__.py
  sed -i.bak "s/    assert __version__ == '.*'/    assert __version__ == '$version'/" tests/test_gcpm.py
  rm -f tests/test_gcpm.py.bak
}

case $1 in
  test)poetry run pytest -v --cov=./src --cov-report=html:report;;
  debug)poetry run pytest -o log_cli=true --log-cli-level=DEBUG -v -s --cov=./src --cov-report=html:report;;
  bandit)mkdir -p report/;poetry run bandit -r ./src/gcpm -f html > report/bandit.html;;
  version)version_update;;
  pypi)version_update; poetry publish --build;;
  testpypi)version_update; poetry publish -r testpypi --build;;
  *)echo "$usage";exit 1;;
esac
