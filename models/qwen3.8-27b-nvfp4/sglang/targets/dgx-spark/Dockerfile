# syntax=docker/dockerfile:1.7
ARG BASE_IMAGE=lmsysorg/sglang:dev-qwen38-27b-dflash2
FROM ${BASE_IMAGE}

ENV HF_HOME=/root/.cache/huggingface \
    CUDA_HOME=/usr/local/cuda \
    PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

WORKDIR /opt/dgxspark

COPY start.sh /opt/dgxspark/start.sh
RUN chmod 0755 /opt/dgxspark/start.sh

EXPOSE 30000
ENTRYPOINT ["/opt/dgxspark/start.sh"]
