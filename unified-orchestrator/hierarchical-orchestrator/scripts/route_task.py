#!/usr/bin/env python3
"""
Route tasks to optimal model based on complexity, history, and cost optimization.
"""

import json
import re
from dataclasses import dataclass
from typing import Optional, Dict, List
from pathlib import Path

@dataclass
class RoutingDecision:
    model: str
    reason: str
    complexity: float
    output_limit: Optional[int] = None
    validation_required: bool = False

class TaskComplexityScorer:
    """Score task complexity from 0-10"""
    
    ARCHITECTURAL_PATTERNS = [
        "refactor", "restructure", "architect", "redesign", 
        "migrate", "rewrite", "overhaul"
    ]
    
    SIMPLE_PATTERNS = [
        "format", "rename", "add comment", "fix typo",
        "simple", "basic", "straightforward"
    ]
    
    def score(self, task: str, context: Optional[Dict] = None) -> float:
        context = context or {}
        score = 0.0
        task_lower = task.lower()
        
        # Length factor (0-3)
        word_count = len(task.split())
        score += min(3.0, word_count / 50)
        
        # Architectural complexity (+3)
        if any(p in task_lower for p in self.ARCHITECTURAL_PATTERNS):
            score += 3.0
        
        # Simple task reduction (-2)
        if any(p in task_lower for p in self.SIMPLE_PATTERNS):
            score -= 2.0
        
        # Multi-file complexity (+2)
        if context.get("files", 0) > 1:
            score += 2.0
        
        # Testing requirement (+1.5)
        if context.get("requires_tests") or "test" in task_lower:
            score += 1.5
        
        # Security sensitivity (+2)
        if any(w in task_lower for w in ["security", "auth", "encrypt", "credential"]):
            score += 2.0
        
        # Database complexity (+1)
        if any(w in task_lower for w in ["database", "migration", "schema", "query"]):
            score += 1.0
        
        return max(0, min(10, score))

class HierarchicalRouter:
    """Route tasks to optimal model based on complexity and history"""
    
    MODEL_TIERS = {
        "local/qwen3-30b-a3b": {"max_complexity": 2, "cost": 0, "type": "generator"},
        "cerebras/glm-4.7": {"max_complexity": 4, "cost": 0.60, "type": "generator", "task_types": ["code"]},
        "haiku": {"max_complexity": 4, "cost": 0.25, "type": "generator"},
        "sonnet": {"max_complexity": 7, "cost": 3.00, "type": "generator"},
        "opus": {"max_complexity": 10, "cost": 15.00, "type": "generator"},
    }
    
    def __init__(self, memory_path: Optional[Path] = None):
        self.scorer = TaskComplexityScorer()
        self.memory_path = memory_path or Path.home() / ".claude-orchestrator" / "memory"
        
    def route(self, task: str, context: Optional[Dict] = None) -> RoutingDecision:
        context = context or {}
        complexity = self.scorer.score(task, context)
        
        # Check for validation checkpoint
        if context.get("checkpoint") == "validation":
            return RoutingDecision(
                model="sonnet",
                reason="Input-heavy validation checkpoint",
                complexity=complexity,
                output_limit=100,
                validation_required=False  # This IS the validation
            )
        
        # Check for major checkpoint requiring Opus
        if context.get("checkpoint") == "major" and context.get("needs_redirect"):
            return RoutingDecision(
                model="opus",
                reason="Strategic redirect at major checkpoint",
                complexity=complexity,
                output_limit=50
            )
        
        # Check past performance for similar tasks
        best_model = self._check_history(task)
        if best_model:
            return RoutingDecision(
                model=best_model,
                reason="Historical success with similar task",
                complexity=complexity,
                validation_required=complexity > 2
            )
        
        # Route based on complexity
        return self._route_by_complexity(task, complexity, context)
    
    def _route_by_complexity(self, task: str, complexity: float, context: Dict) -> RoutingDecision:
        task_lower = task.lower()
        is_code_task = any(w in task_lower for w in ["code", "function", "class", "implement", "write"])
        
        if complexity <= 2:
            return RoutingDecision(
                model="local/qwen3-30b-a3b",
                reason="Simple task - use free local model",
                complexity=complexity,
                validation_required=False
            )
        
        if complexity <= 4:
            if is_code_task:
                return RoutingDecision(
                    model="cerebras/glm-4.7",
                    reason="Medium code task - fast API with good accuracy",
                    complexity=complexity,
                    validation_required=True
                )
            return RoutingDecision(
                model="haiku",
                reason="Medium non-code task - cost-effective",
                complexity=complexity,
                validation_required=True
            )
        
        if complexity <= 7:
            return RoutingDecision(
                model="sonnet",
                reason="Complex task - needs strong reasoning",
                complexity=complexity,
                validation_required=True
            )
        
        return RoutingDecision(
            model="opus",
            reason="Highly complex - needs best reasoning",
            complexity=complexity,
            validation_required=False  # Opus output is authoritative
        )
    
    def _check_history(self, task: str) -> Optional[str]:
        """Check if similar tasks have been done before"""
        # TODO: Implement Qdrant search for similar tasks
        # Returns model that performed best on similar tasks
        return None

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Route task to optimal model")
    parser.add_argument("task", help="Task description")
    parser.add_argument("--files", type=int, default=0, help="Number of files involved")
    parser.add_argument("--checkpoint", choices=["validation", "major"], help="Checkpoint type")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    router = HierarchicalRouter()
    context = {"files": args.files}
    if args.checkpoint:
        context["checkpoint"] = args.checkpoint
    
    decision = router.route(args.task, context)
    
    if args.json:
        print(json.dumps({
            "model": decision.model,
            "reason": decision.reason,
            "complexity": decision.complexity,
            "output_limit": decision.output_limit,
            "validation_required": decision.validation_required
        }, indent=2))
    else:
        print(f"Model: {decision.model}")
        print(f"Complexity: {decision.complexity:.1f}/10")
        print(f"Reason: {decision.reason}")
        if decision.output_limit:
            print(f"Output limit: {decision.output_limit} tokens")
        if decision.validation_required:
            print("⚠️  Validation checkpoint required after generation")

if __name__ == "__main__":
    main()
