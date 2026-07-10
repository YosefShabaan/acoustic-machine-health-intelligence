import hashlib
import json
from pathlib import Path
import sys

# Add src to path to import config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import config as cfg

def compute_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def main():
    machine_type = "fan"
    machine_id = "id_00"
    snr_tag = "minus6dB"
    
    # Required paths based on ArtifactRegistry
    expert_a_model = cfg.ad_paths_for(snr_tag)["model"]
    expert_a_norm_stats = cfg.ad_paths_for(snr_tag)["norm_stats"]
    
    expert_b_ref_index = cfg.PROCESSED_DIR / f"timbre_reference_index_{machine_type}_{machine_id}_{snr_tag}.json"
    
    from rag import default_embedding_index_path
    semantic_index = default_embedding_index_path("AMHI-FAN-MAINT-KB-v1")
    
    files_to_hash = [
        ("expert_a_model", "anomaly_detection_model", expert_a_model),
        ("expert_a_norm_stats", "anomaly_detection_normalization", expert_a_norm_stats),
        ("expert_b_reference_index", "timbre_reference_index", expert_b_ref_index),
        ("semantic_rag_index", "semantic_rag_index", semantic_index)
    ]
    
    artifacts = []
    
    pdm_root = cfg.PDM_DATA_ROOT
    
    for artifact_id, role, path in files_to_hash:
        if not path.exists():
            print(f"Warning: {path} does not exist!")
            continue
            
        # Get logical reference relative to PDM_DATA_ROOT
        try:
            logical_ref = path.relative_to(pdm_root).as_posix()
        except ValueError:
            # Fallback if not relative
            logical_ref = path.name
            
        artifacts.append({
            "artifact_id": artifact_id,
            "artifact_role": role,
            "logical_reference": logical_ref,
            "checksum": compute_sha256(path),
            "size_bytes": path.stat().st_size
        })
        
    manifest = {
        "machine_type": machine_type,
        "machine_id": machine_id,
        "snr_tag": snr_tag,
        "version": "1.0.0",
        "artifacts": artifacts
    }
    
    out_dir = cfg.PROJECT_ROOT / "data" / "manifests"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"artifact_manifest_{machine_type}_{machine_id}_{snr_tag}.json"
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)
        f.write("\n")
        
    print(f"Manifest written to {out_path}")

if __name__ == "__main__":
    main()
