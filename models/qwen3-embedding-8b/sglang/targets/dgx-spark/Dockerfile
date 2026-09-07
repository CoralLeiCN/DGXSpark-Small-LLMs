# syntax=docker/dockerfile:1.7
ARG BASE_IMAGE=lmsysorg/sglang:dev-qwen38-27b-dflash2
FROM ${BASE_IMAGE}
ENV HF_HOME=/root/.cache/huggingface \
    CUDA_HOME=/usr/local/cuda
WORKDIR /opt/inferpack
COPY start.sh ./
COPY tests ./tests
RUN chmod 0755 start.sh
EXPOSE 30000
ENTRYPOINT ["/opt/inferpack/start.sh"]
