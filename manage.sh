#!/usr/bin/env bash

commands=(test)
usage="Usage: $0 <command>
  commands: ${commands[*]}"

case $1 in
  test)poetry run pytest -v --cov=./src --cov-report=html;;
  *)echo "$usage";exit 1;;
esac
