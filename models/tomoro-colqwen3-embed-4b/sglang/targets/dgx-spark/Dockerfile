# syntax=docker/dockerfile:1.7
ARG BASE_IMAGE=lmsysorg/sglang:dev-qwen38-27b-dflash2
FROM ${BASE_IMAGE}
ENV HF_HOME=/root/.cache/huggingface \
    CUDA_HOME=/usr/local/cuda \
    PYTHONPATH=/opt/inferpack \
    SGLANG_EXTERNAL_MODEL_PACKAGE=tomoro_sglang
WORKDIR /opt/inferpack
COPY start.sh prepare_model.py ./
COPY tomoro_sglang ./tomoro_sglang
COPY tests ./tests
RUN chmod 0755 start.sh
EXPOSE 30000
ENTRYPOINT ["/opt/inferpack/start.sh"]
