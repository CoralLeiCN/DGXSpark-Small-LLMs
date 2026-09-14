.DEFAULT_GOAL := start

MODEL ?=
ENGINE ?= sglang
TARGET ?= dgx-spark
MONITORING_ENVIRONMENT ?= dev

.PHONY: start stop-all
start:
	@test -n "$(MODEL)" || { echo 'Usage: make start MODEL=<model> [ENGINE=sglang] [TARGET=dgx-spark]' >&2; exit 1; }
	uv run --python 3.12 infer start "$(MODEL)" --engine "$(ENGINE)" --target "$(TARGET)" --environment "$(MONITORING_ENVIRONMENT)"

stop-all:
	uv run --python 3.12 infer stop-all
