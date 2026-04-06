.PHONY: vllm-run

VLLM_IMAGE ?= vllm/vllm-openai:v0.18.1-cu130
VLLM_CONTAINER_NAME ?= vllm
VLLM_PORT ?= 8000
HF_CACHE_DIR ?= $(HOME)/.cache/huggingface
MODEL_CKPT ?= nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4
SERVED_MODEL_NAME ?= nemotron-3-super

vllm-run:
	docker run --rm \
		--gpus all \
		--name $(VLLM_CONTAINER_NAME) \
		-v $(HF_CACHE_DIR):/root/.cache/huggingface \
		-e HF_TOKEN=$$HF_TOKEN \
		-e VLLM_NVFP4_GEMM_BACKEND=marlin \
		-e VLLM_ALLOW_LONG_MAX_MODEL_LEN=1 \
		-e VLLM_FLASHINFER_ALLREDUCE_BACKEND=trtllm \
		-p $(VLLM_PORT):8000 \
		--ipc=host \
		$(VLLM_IMAGE) \
		$(MODEL_CKPT) \
		--served-model-name $(SERVED_MODEL_NAME) \
		--host 0.0.0.0 \
		--port 8000 \
		--async-scheduling \
		--dtype auto \
		--kv-cache-dtype fp8 \
		--tensor-parallel-size 1 \
		--pipeline-parallel-size 1 \
		--data-parallel-size 1 \
		--trust-remote-code \
		--gpu-memory-utilization 0.90 \
		--enable-chunked-prefill \
		--max-num-seqs 4 \
		--max-model-len 394000 \
		--attention-backend TRITON_ATTN \
		--mamba-ssm-cache-dtype float32 \
		--moe-backend marlin
