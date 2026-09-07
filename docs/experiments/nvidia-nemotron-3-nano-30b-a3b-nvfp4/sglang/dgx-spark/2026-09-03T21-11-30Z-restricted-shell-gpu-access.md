# 2026-09-03T21:11:30Z — Restricted shell could not access the NVIDIA driver

Run ID: `RUN-0001`

- Status: resolved
- Phase: preflight
- Related turns: none
- Repo revision: `c520931` (`dirty`)
- Host/GPU: DGX Spark, NVIDIA GB10, driver `580.173.02`, ARM64
- Container: `nvcr.io/nvidia/pytorch:26.02-py3`
  (`sha256:c0e6c0b168faa1be027564e9a004e842c342e22ea51903d5fc7b9008850398d0`)
- Engine: SGLang `0.5.15.post1`
- Model: `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4`, NVFP4

## Command

```bash
nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version \
  --format=csv,noheader
```

## Error Or Observation

```text
NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver.
Make sure that the latest NVIDIA driver is installed and running.
```

## Diagnosis

- Symptom: `nvidia-smi` failed in the restricted command environment, and no
  `/dev/nvidia*` nodes or systemd bus were visible there.
- Root cause: the command sandbox isolated host GPU devices and the system bus;
  the host NVIDIA driver was not broken.
- Evidence: the restricted environment could read the loaded NVIDIA kernel
  modules and driver version but could not see device nodes. Repeating the
  checks with host-level access detected the GB10, reported driver `580.173.02`,
  and showed `nvidia-persistenced.service` as active. Docker also reported an
  ARM64 server and found the required cached base image.

## Fix Or Change

Run host GPU and Docker setup commands with host-level device and daemon access.
No driver restart or recipe change was required.

## Verification

```bash
nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version \
  --format=csv,noheader
systemctl is-active nvidia-persistenced.service
docker info --format 'server={{.ServerVersion}} architecture={{.Architecture}}'
docker image inspect nvcr.io/nvidia/pytorch:26.02-py3
```

The host-level checks reported an NVIDIA GB10, an active persistence daemon,
Docker `29.2.1` on ARM64, and the cached `26.02-py3` base image.

## Lesson

When `nvidia-smi` fails, first distinguish a host driver failure from execution
isolation. Compare device-node visibility and repeat the check in the same
host-level context that will operate Docker before restarting drivers or
changing an inference recipe.

## Next Step

Continue preflight, build, startup, and inference commands with host-level
Docker and GPU access.
