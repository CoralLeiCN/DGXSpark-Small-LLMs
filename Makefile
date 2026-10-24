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

.PHONY: vllm-run vllm-run-super vllm-run-nano vllm-down vllm-validate vllm-validate-super vllm-validate-nano

COMPOSE ?= docker compose
UV ?= uv
PYTHON ?= $(UV) run --python 3.12 python
SUPER_SERVED_MODEL_NAME ?= nemotron-3-super
NANO_SERVED_MODEL_NAME ?= model

vllm-run: vllm-run-nano

vllm-run-super:
	$(COMPOSE) --profile super up

vllm-run-nano:
	$(COMPOSE) --profile nano up

vllm-down:
	$(COMPOSE) down

vllm-validate: vllm-validate-nano

vllm-validate-super:
	VLLM_MODEL=$(SUPER_SERVED_MODEL_NAME) $(PYTHON) validate_vllm.py

vllm-validate-nano:
	VLLM_MODEL=$(NANO_SERVED_MODEL_NAME) $(PYTHON) validate_vllm.py
