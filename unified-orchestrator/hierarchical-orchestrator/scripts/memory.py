#!/usr/bin/env python3
"""
Unified memory system for cross-project context.
Combines file-based storage with optional Qdrant vector search.
"""

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import hashlib

@dataclass
class Experience:
    id: str
    timestamp: str
    task: str
    model: str
    complexity: float
    success: bool
    feedback: float
    tokens_in: int
    tokens_out: int
    duration_ms: int
    output_summary: Optional[str] = None
    error_type: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, d: Dict) -> "Experience":
        return cls(**d)

class UnifiedMemory:
    """
    Unified memory system combining:
    - File-based storage for structured data and audit trails
    - Optional Qdrant integration for semantic search
    """
    
    def __init__(self, base_path: Optional[Path] = None, use_qdrant: bool = False):
        self.base_path = base_path or Path.home() / ".claude-orchestrator" / "memory"
        self.use_qdrant = use_qdrant
        
        # Initialize directories
        self._init_directories()
        
        # Initialize Qdrant if enabled
        if use_qdrant:
            self._init_qdrant()
    
    def _init_directories(self):
        """Create memory directory structure"""
        dirs = [
            self.base_path / "semantic",
            self.base_path / "episodic" / "sessions",
            self.base_path / "episodic" / "summaries" / "weekly",
            self.base_path / "procedural",
            self.base_path / "model_profiles",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
    
    def _init_qdrant(self):
        """Initialize Qdrant collections"""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import VectorParams, Distance
            
            self.qdrant = QdrantClient("localhost", port=6333)
            
            # Create collections if they don't exist
            collections = ["experiences", "code_patterns"]
            for coll in collections:
                try:
                    self.qdrant.get_collection(coll)
                except:
                    self.qdrant.create_collection(
                        collection_name=coll,
                        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                    )
            
            # Initialize encoder
            from sentence_transformers import SentenceTransformer
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
            
        except ImportError:
            print("Warning: Qdrant not available. Using file-based storage only.")
            self.use_qdrant = False
        except Exception as e:
            print(f"Warning: Could not connect to Qdrant: {e}")
            self.use_qdrant = False
    
    def store_experience(
        self,
        task: str,
        model: str,
        success: bool,
        feedback: float = 0.5,
        complexity: float = 0,
        tokens_in: int = 0,
        tokens_out: int = 0,
        duration_ms: int = 0,
        output_summary: Optional[str] = None,
        error_type: Optional[str] = None
    ) -> str:
        """Store an experience from a task execution"""
        
        # Generate ID
        exp_id = hashlib.md5(
            f"{task}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        experience = Experience(
            id=exp_id,
            timestamp=datetime.now().isoformat(),
            task=task,
            model=model,
            complexity=complexity,
            success=success,
            feedback=feedback,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            duration_ms=duration_ms,
            output_summary=output_summary,
            error_type=error_type
        )
        
        # Store to file
        self._store_to_file(experience)
        
        # Store to Qdrant if enabled
        if self.use_qdrant:
            self._store_to_qdrant(experience)
        
        return exp_id
    
    def _store_to_file(self, experience: Experience):
        """Append experience to daily session file"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        session_dir = self.base_path / "episodic" / "sessions" / date_str
        session_dir.mkdir(parents=True, exist_ok=True)
        
        session_file = session_dir / "session.jsonl"
        with open(session_file, "a") as f:
            f.write(json.dumps(experience.to_dict()) + "\n")
    
    def _store_to_qdrant(self, experience: Experience):
        """Store experience to Qdrant for semantic search"""
        embedding = self.encoder.encode(experience.task)
        
        self.qdrant.upsert(
            collection_name="experiences",
            points=[{
                "id": experience.id,
                "vector": embedding.tolist(),
                "payload": experience.to_dict()
            }]
        )
    
    def retrieve_relevant(
        self,
        query: str,
        limit: int = 5,
        min_score: float = 0.7,
        success_only: bool = True
    ) -> List[Dict]:
        """Retrieve relevant past experiences"""
        
        if self.use_qdrant:
            return self._retrieve_from_qdrant(query, limit, min_score, success_only)
        else:
            return self._retrieve_from_files(query, limit, success_only)
    
    def _retrieve_from_qdrant(
        self,
        query: str,
        limit: int,
        min_score: float,
        success_only: bool
    ) -> List[Dict]:
        """Semantic search using Qdrant"""
        embedding = self.encoder.encode(query)
        
        filter_conditions = []
        if success_only:
            filter_conditions.append({
                "key": "success",
                "match": {"value": True}
            })
        
        results = self.qdrant.search(
            collection_name="experiences",
            query_vector=embedding.tolist(),
            limit=limit,
            score_threshold=min_score,
            query_filter={"must": filter_conditions} if filter_conditions else None
        )
        
        return [
            {
                "task": r.payload["task"],
                "model": r.payload["model"],
                "success": r.payload["success"],
                "feedback": r.payload["feedback"],
                "similarity": r.score
            }
            for r in results
        ]
    
    def _retrieve_from_files(
        self,
        query: str,
        limit: int,
        success_only: bool
    ) -> List[Dict]:
        """Simple keyword-based retrieval from files"""
        experiences = []
        query_words = set(query.lower().split())
        
        sessions_dir = self.base_path / "episodic" / "sessions"
        for date_dir in sorted(sessions_dir.iterdir(), reverse=True)[:7]:  # Last 7 days
            session_file = date_dir / "session.jsonl"
            if session_file.exists():
                with open(session_file) as f:
                    for line in f:
                        exp = json.loads(line)
                        if success_only and not exp.get("success"):
                            continue
                        
                        # Simple keyword matching
                        task_words = set(exp["task"].lower().split())
                        overlap = len(query_words & task_words)
                        if overlap > 0:
                            experiences.append({
                                **exp,
                                "similarity": overlap / len(query_words)
                            })
        
        # Sort by similarity and return top N
        experiences.sort(key=lambda x: x["similarity"], reverse=True)
        return experiences[:limit]
    
    def get_model_profile(self, model_id: str) -> Dict:
        """Load model performance profile"""
        profile_file = self.base_path / "model_profiles" / f"{model_id.replace('/', '_')}.json"
        
        if profile_file.exists():
            with open(profile_file) as f:
                return json.load(f)
        
        return {"model_id": model_id, "task_affinities": {}}
    
    def update_model_profile(self, model_id: str, task_type: str, success: bool, duration_ms: int):
        """Update model profile with new experience"""
        profile = self.get_model_profile(model_id)
        
        if task_type not in profile["task_affinities"]:
            profile["task_affinities"][task_type] = {
                "success_rate": 0.0,
                "avg_time_ms": 0,
                "sample_size": 0
            }
        
        stats = profile["task_affinities"][task_type]
        n = stats["sample_size"]
        
        # Update running averages
        stats["success_rate"] = (stats["success_rate"] * n + (1 if success else 0)) / (n + 1)
        stats["avg_time_ms"] = (stats["avg_time_ms"] * n + duration_ms) / (n + 1)
        stats["sample_size"] = n + 1
        
        profile["last_updated"] = datetime.now().isoformat()
        
        # Save
        profile_file = self.base_path / "model_profiles" / f"{model_id.replace('/', '_')}.json"
        with open(profile_file, "w") as f:
            json.dump(profile, f, indent=2)
    
    def get_semantic_memory(self, key: str) -> Dict:
        """Load semantic memory (preferences, libraries, etc.)"""
        file_path = self.base_path / "semantic" / f"{key}.json"
        
        if file_path.exists():
            with open(file_path) as f:
                return json.load(f)
        
        return {}
    
    def update_semantic_memory(self, key: str, updates: Dict):
        """Update semantic memory"""
        current = self.get_semantic_memory(key)
        current.update(updates)
        
        file_path = self.base_path / "semantic" / f"{key}.json"
        with open(file_path, "w") as f:
            json.dump(current, f, indent=2)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Manage unified memory")
    subparsers = parser.add_subparsers(dest="command")
    
    # Store experience
    store = subparsers.add_parser("store", help="Store a new experience")
    store.add_argument("--task", required=True, help="Task description")
    store.add_argument("--model", required=True, help="Model used")
    store.add_argument("--success", type=bool, default=True, help="Was it successful?")
    store.add_argument("--feedback", type=float, default=0.5, help="Feedback score 0-1")
    
    # Retrieve
    retrieve = subparsers.add_parser("retrieve", help="Retrieve relevant experiences")
    retrieve.add_argument("query", help="Query to search for")
    retrieve.add_argument("--limit", type=int, default=5, help="Max results")
    
    # Profile
    profile = subparsers.add_parser("profile", help="View model profile")
    profile.add_argument("model", help="Model ID")
    
    args = parser.parse_args()
    
    memory = UnifiedMemory()
    
    if args.command == "store":
        exp_id = memory.store_experience(
            task=args.task,
            model=args.model,
            success=args.success,
            feedback=args.feedback
        )
        print(f"Stored experience: {exp_id}")
    
    elif args.command == "retrieve":
        results = memory.retrieve_relevant(args.query, limit=args.limit)
        for r in results:
            print(f"[{r.get('similarity', 0):.2f}] {r['model']}: {r['task'][:50]}...")
    
    elif args.command == "profile":
        profile = memory.get_model_profile(args.model)
        print(json.dumps(profile, indent=2))

if __name__ == "__main__":
    main()
