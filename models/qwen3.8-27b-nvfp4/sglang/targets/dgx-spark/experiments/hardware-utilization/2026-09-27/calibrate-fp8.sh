set -e
uv run --offline --no-project --python /opt/sglang/bin/python /work/scripts/fp8.py > /work/calibration/fp8-unprofiled.jsonl 2> /work/calibration/fp8-unprofiled.stderr
/opt/nvidia/nsight-compute/2025.3.1/ncu --target-processes all --profile-from-start off --cache-control none --clock-control none --metrics gpu__time_duration.sum,sm__ops_path_tensor_src_fp8_dst_fp32.sum --export /work/calibration/fp8-ncu uv run --offline --no-project --python /opt/sglang/bin/python /work/scripts/fp8.py profile > /work/calibration/fp8-ncu.log 2>&1
