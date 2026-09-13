.DEFAULT_GOAL := start

MODEL ?=
ENGINE ?= sglang
TARGET ?= dgx-spark

.PHONY: start stop-all
start:
	@test -n "$(MODEL)" || { echo 'Usage: make start MODEL=<model> [ENGINE=sglang] [TARGET=dgx-spark]' >&2; exit 1; }
	docker compose -f monitoring/compose.yaml up -d --wait
	uv run --python 3.12 infer deploy "$(MODEL)" --engine "$(ENGINE)" --target "$(TARGET)"

stop-all:
	uv run --python 3.12 infer stop-all
