from dataclasses import dataclass
from typing import Dict
import json
import os

@dataclass
class QuotaManifest:
    rag_count: int = 500
    tool_count: int = 150
    safety_count: int = 100
    injection_count: int = 100
    abstention_count: int = 100
    multi_turn_count: int = 50
    routing_count: int = 300

    def generate(self, output_dir: str):
        os.makedirs(output_dir, exist_ok=True)
        manifest_path = os.path.join(output_dir, "manifest.json")
        with open(manifest_path, "w") as f:
            json.dump({
                "rag": self.rag_count,
                "tool": self.tool_count,
                "safety": self.safety_count,
                "injection": self.injection_count,
                "abstention": self.abstention_count,
                "multi_turn": self.multi_turn_count,
                "routing": self.routing_count,
                "provenance": "synthetic",
                "synthetic": True,
            }, f)
        
        # Keep corpora out of Git by writing to this non-git dir
        # In a real app we'd dump JSONL here
        for dataset, count in [
            ("rag", self.rag_count),
            ("tool", self.tool_count),
            ("safety", self.safety_count),
            ("injection", self.injection_count),
            ("abstention", self.abstention_count),
            ("multi_turn", self.multi_turn_count),
            ("routing", self.routing_count)
        ]:
            with open(os.path.join(output_dir, f"{dataset}.jsonl"), "w") as f:
                for i in range(count):
                    f.write(json.dumps({"id": f"{dataset}-{i}", "synthetic": True}) + "\n")
