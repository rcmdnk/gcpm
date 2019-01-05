#!/usr/bin/env bash

commands=(test version)
usage="Usage: $0 <command>
  commands: ${commands[*]}"


version_update () {
  version=$(grep "^version" pyproject.toml | cut -d '"' -f2)
  echo "__version__ = \"$version\"" > ./src/gcpm/__version__.py
  sed -i .bak "s/    assert __version__ == '.*'/    assert __version__ == '$version'/" tests/test_gcpm.py
  rm -f tests/test_gcpm.py.bak
}

case $1 in
  test)poetry run pytest -v --cov=./src --cov-report=html;;
  version)version_update;;
  *)echo "$usage";exit 1;;
esac
