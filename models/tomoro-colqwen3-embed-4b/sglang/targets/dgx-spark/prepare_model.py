"""Create a container-local config view; never modify cached model files."""
import json
import os
from pathlib import Path
from huggingface_hub import snapshot_download

REVISION = "13517a29e8c5e408f7f2684337ed407df3acb212"


def main():
    snapshot = Path(snapshot_download(
        repo_id=os.environ.get("MODEL_ID", "TomoroAI/tomoro-colqwen3-embed-4b"),
        revision=os.environ.get("MODEL_REVISION", REVISION),
    ))
    target = Path("/opt/inferpack/model")
    target.mkdir(exist_ok=True)
    config = json.loads((snapshot / "config.json").read_text())
    if config["architectures"] != ["ColQwen3"] or config["embed_dim"] != 320:
        raise ValueError("Unexpected checkpoint architecture or projection dimension")
    for source in snapshot.iterdir():
        if not source.is_file():
            continue
        destination = target / source.name
        if destination.is_symlink() or destination.exists():
            destination.unlink()
        if source.name in {
            "config.json", "processor_config.json", "preprocessor_config.json",
            "video_preprocessor_config.json", "tokenizer_config.json",
        }:
            data = json.loads(source.read_text())
            data.pop("auto_map", None)
            if source.name == "config.json":
                data.update(model_type="qwen3_vl", architectures=["Qwen3VLForConditionalGeneration"],
                            tie_word_embeddings=True)
            elif "processor_class" in data:
                data["processor_class"] = "Qwen3VLProcessor"
            destination.write_text(json.dumps(data, indent=2) + "\n")
        else:
            destination.symlink_to(source)
    print(f"Prepared Tomoro checkpoint {snapshot.name}", flush=True)


if __name__ == "__main__":
    main()
