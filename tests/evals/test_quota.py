import os
import json
import tempfile
from evals.runners.quota_generator import QuotaManifest

def test_quota_generator_provenance_and_counts():
    with tempfile.TemporaryDirectory() as tmp:
        generator = QuotaManifest()
        generator.generate(tmp)
        
        manifest_file = os.path.join(tmp, "manifest.json")
        assert os.path.exists(manifest_file)
        
        with open(manifest_file) as f:
            data = json.load(f)
            
        assert data["rag"] == 500
        assert data["tool"] == 150
        assert data["safety"] == 100
        assert data["injection"] == 100
        assert data["abstention"] == 100
        assert data["multi_turn"] == 50
        assert data["routing"] == 300
        assert data["provenance"] == "synthetic"
        assert data["synthetic"] is True

        # Ensure generated corpora exist and match counts
        assert len(open(os.path.join(tmp, "rag.jsonl")).readlines()) == 500
        assert len(open(os.path.join(tmp, "tool.jsonl")).readlines()) == 150
