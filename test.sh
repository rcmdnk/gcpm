#!/usr/bin/env bash

poetry run pytest -v --cov=./src --cov-report=html
