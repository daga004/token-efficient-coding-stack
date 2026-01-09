#!/usr/bin/env python3
"""
Unified AI Orchestrator MCP Server

Combines:
- AuZoom: Multi-resolution code navigation
- Orchestrator: Model routing and execution  
- Memory: Cross-project learning

Single MCP server exposing all tools to Claude Code.
"""

import json
import os
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional, Dict, List, Any
from pathlib import Path


# =============================================================================
# AUZOOM INTEGRATION
# =============================================================================

class FetchLevel(Enum):
    SKELETON = "skeleton"  # ~15 tokens/node - names + deps
    SUMMARY = "summary"    # ~75 tokens/node - + docstrings, signatures
    FULL = "full"          # ~400 tokens/node - + source code


@dataclass
class AuZoomContext:
    """Context built from AuZoom for model consumption"""
    skeleton: str           # Always included
    summaries: List[str]    # For medium/complex tasks
    full_code: List[str]    # Only for modification targets
    total_tokens: int
    nodes_included: int


class AuZoomBridge:
    """Bridge to AuZoom MCP server or direct integration"""
    
    def __init__(self, auzoom_client=None):
        self.client = auzoom_client
        
    def get_graph(
        self,
        node_id: str = "root",
        level: FetchLevel = FetchLevel.SKELETON,
        depth_down: int = 2,
        depth_up: int = 0
    ) -> Dict:
        """Fetch code graph at specified resolution"""
        # TODO: Connect to actual AuZoom MCP or library
        # For now, return mock structure
        return {
            "node_id": node_id,
            "level": level.value,
            "children": [],
            "content": f"[{level.value} view of {node_id}]"
        }
    
    def find(self, query: str, scope: Optional[str] = None) -> List[str]:
        """Find nodes matching query"""
        # TODO: Semantic search in code graph
        return []
    
    def get_dependencies(
        self,
        node_id: str,
        direction: str = "both",
        depth: int = 1
    ) -> List[str]:
        """Get dependency graph for a node"""
        return []


# =============================================================================
# CONTEXT BUILDER (AuZoom-aware)
# =============================================================================

class ContextBuilder:
    """
    Builds optimal context for each model tier using AuZoom.
    
    Key principle: Less capable models get MORE compressed context.
    More capable models can handle more context efficiently.
    """
    
    # Context budgets by model tier (tokens)
    CONTEXT_BUDGETS = {
        "local": 2000,      # Local models - minimal context
        "haiku": 4000,      # Haiku - compressed context
        "glm": 6000,        # GLM 4.7 - medium context
        "sonnet": 16000,    # Sonnet - rich context
        "opus": 32000,      # Opus - full context
    }
    
    def __init__(self, auzoom: AuZoomBridge):
        self.auzoom = auzoom
    
    def build_for_model(
        self,
        task: str,
        target_model: str,
        target_nodes: List[str]
    ) -> AuZoomContext:
        """Build context appropriate for target model"""
        
        tier = self._get_tier(target_model)
        budget = self.CONTEXT_BUDGETS.get(tier, 4000)
        
        if tier == "local":
            return self._build_minimal(task, target_nodes, budget)
        elif tier in ["haiku", "glm"]:
            return self._build_medium(task, target_nodes, budget)
        else:
            return self._build_full(task, target_nodes, budget)
    
    def _get_tier(self, model: str) -> str:
        if "local" in model or "qwen" in model.lower():
            return "local"
        elif "haiku" in model:
            return "haiku"
        elif "glm" in model:
            return "glm"
        elif "sonnet" in model:
            return "sonnet"
        else:
            return "opus"
    
    def _build_minimal(
        self,
        task: str,
        targets: List[str],
        budget: int
    ) -> AuZoomContext:
        """
        Minimal context for local/simple models.
        Skeleton + ONLY target function full code.
        """
        skeleton = self.auzoom.get_graph("root", FetchLevel.SKELETON, depth_down=2)
        full_targets = [
            self.auzoom.get_graph(t, FetchLevel.FULL)
            for t in targets[:1]  # Only first target
        ]
        
        return AuZoomContext(
            skeleton=json.dumps(skeleton),
            summaries=[],
            full_code=[json.dumps(f) for f in full_targets],
            total_tokens=self._estimate_tokens(skeleton, [], full_targets),
            nodes_included=1 + len(full_targets)
        )
    
    def _build_medium(
        self,
        task: str,
        targets: List[str],
        budget: int
    ) -> AuZoomContext:
        """
        Medium context for Haiku/GLM.
        Skeleton + dependency summaries + target full.
        """
        skeleton = self.auzoom.get_graph("root", FetchLevel.SKELETON, depth_down=2)
        
        # Get summaries for dependencies
        summaries = []
        for target in targets[:2]:
            deps = self.auzoom.get_dependencies(target, depth=1)
            for dep in deps[:3]:
                summaries.append(
                    self.auzoom.get_graph(dep, FetchLevel.SUMMARY)
                )
        
        full_targets = [
            self.auzoom.get_graph(t, FetchLevel.FULL)
            for t in targets[:2]
        ]
        
        return AuZoomContext(
            skeleton=json.dumps(skeleton),
            summaries=[json.dumps(s) for s in summaries],
            full_code=[json.dumps(f) for f in full_targets],
            total_tokens=self._estimate_tokens(skeleton, summaries, full_targets),
            nodes_included=1 + len(summaries) + len(full_targets)
        )
    
    def _build_full(
        self,
        task: str,
        targets: List[str],
        budget: int
    ) -> AuZoomContext:
        """
        Full context for Sonnet/Opus.
        Deeper skeleton + full code for target and dependencies.
        """
        skeleton = self.auzoom.get_graph("root", FetchLevel.SKELETON, depth_down=3)
        
        full_nodes = []
        for target in targets[:3]:
            full_nodes.append(self.auzoom.get_graph(target, FetchLevel.FULL))
            deps = self.auzoom.get_dependencies(target, depth=1)
            for dep in deps[:2]:
                full_nodes.append(self.auzoom.get_graph(dep, FetchLevel.FULL))
        
        return AuZoomContext(
            skeleton=json.dumps(skeleton),
            summaries=[],
            full_code=[json.dumps(f) for f in full_nodes],
            total_tokens=self._estimate_tokens(skeleton, [], full_nodes),
            nodes_included=1 + len(full_nodes)
        )
    
    def _estimate_tokens(self, skeleton, summaries, fulls) -> int:
        """Rough token estimate"""
        return (
            len(json.dumps(skeleton)) // 4 +
            sum(len(json.dumps(s)) // 4 for s in summaries) +
            sum(len(json.dumps(f)) // 4 for f in fulls)
        )


# =============================================================================
# ROUTING ENGINE
# =============================================================================

@dataclass
class RoutingDecision:
    model: str
    confidence: float
    reason: str
    context_budget: int
    output_limit: Optional[int] = None
    validation_required: bool = False


class RoutingEngine:
    """
    Rule-based routing with adaptive learning.
    Zero LLM tokens for routing decisions.
    """
    
    COMPLEXITY_PATTERNS = {
        "simple": ["format", "rename", "typo", "comment", "simple"],
        "architectural": ["refactor", "restructure", "migrate", "architect"],
        "security": ["auth", "security", "encrypt", "credential", "password"]
    }
    
    def __init__(self, memory=None):
        self.memory = memory
        
    def route(self, task: str, context: Optional[Dict] = None) -> RoutingDecision:
        """Determine optimal model for task"""
        context = context or {}
        
        # Special cases first
        if context.get("checkpoint") == "validation":
            return RoutingDecision(
                model="sonnet",
                confidence=1.0,
                reason="Validation checkpoint (input-heavy)",
                context_budget=16000,
                output_limit=100,
                validation_required=False
            )
        
        if context.get("checkpoint") == "major":
            return RoutingDecision(
                model="opus",
                confidence=1.0,
                reason="Major checkpoint requiring strategic direction",
                context_budget=32000,
                output_limit=50
            )
        
        # Score complexity
        complexity = self._score_complexity(task, context)
        
        # Check historical performance if memory available
        if self.memory:
            historical = self.memory.get_best_model_for_similar(task)
            if historical and historical.get("confidence", 0) > 0.8:
                return RoutingDecision(
                    model=historical["model"],
                    confidence=historical["confidence"],
                    reason=f"Historical success on similar tasks",
                    context_budget=self._budget_for_model(historical["model"]),
                    validation_required=complexity > 2
                )
        
        # Route by complexity
        return self._route_by_complexity(task, complexity, context)
    
    def _score_complexity(self, task: str, context: Dict) -> float:
        """Score task complexity 0-10"""
        score = 0.0
        task_lower = task.lower()
        
        # Length factor
        score += min(3.0, len(task.split()) / 50)
        
        # Pattern matching
        if any(p in task_lower for p in self.COMPLEXITY_PATTERNS["simple"]):
            score -= 2.0
        if any(p in task_lower for p in self.COMPLEXITY_PATTERNS["architectural"]):
            score += 3.0
        if any(p in task_lower for p in self.COMPLEXITY_PATTERNS["security"]):
            score += 2.0
        
        # Multi-file
        if context.get("files", 0) > 1:
            score += 2.0
        
        # Testing
        if "test" in task_lower or context.get("requires_tests"):
            score += 1.5
        
        return max(0, min(10, score))
    
    def _route_by_complexity(
        self,
        task: str,
        complexity: float,
        context: Dict
    ) -> RoutingDecision:
        """Route based on complexity score"""
        
        is_code = any(w in task.lower() for w in ["code", "function", "implement"])
        
        if complexity <= 2:
            return RoutingDecision(
                model="local/qwen3-30b-a3b",
                confidence=0.9,
                reason="Simple task - local model",
                context_budget=2000,
                validation_required=False
            )
        
        if complexity <= 4:
            if is_code:
                return RoutingDecision(
                    model="cerebras/glm-4.7",
                    confidence=0.85,
                    reason="Medium code task - fast API",
                    context_budget=6000,
                    validation_required=True
                )
            return RoutingDecision(
                model="haiku",
                confidence=0.85,
                reason="Medium task - cost-effective",
                context_budget=4000,
                validation_required=True
            )
        
        if complexity <= 7:
            return RoutingDecision(
                model="sonnet",
                confidence=0.9,
                reason="Complex task - strong reasoning",
                context_budget=16000,
                validation_required=True
            )
        
        return RoutingDecision(
            model="opus",
            confidence=0.95,
            reason="Highly complex - best reasoning",
            context_budget=32000,
            validation_required=False
        )
    
    def _budget_for_model(self, model: str) -> int:
        budgets = {
            "local": 2000, "haiku": 4000, "glm": 6000,
            "sonnet": 16000, "opus": 32000
        }
        for key, budget in budgets.items():
            if key in model.lower():
                return budget
        return 4000


# =============================================================================
# MODEL EXECUTOR
# =============================================================================

@dataclass
class ExecutionResult:
    model: str
    response: str
    tokens_in: int
    tokens_out: int
    latency_ms: int
    success: bool
    error: Optional[str] = None


class ModelExecutor:
    """
    Execute prompts on specified models.
    Handles local (Ollama), Anthropic API, Cerebras API.
    """
    
    PROMPT_TEMPLATES = {
        "local": """<task>{task}</task>
<context>{skeleton}</context>
<code>{full_code}</code>
Output only the solution, no explanation.""",
        
        "haiku": """Task: {task}

Context:
{skeleton}

Code to modify:
{full_code}

Provide the solution.""",
        
        "glm": """<task>{task}</task>
<navigation>{skeleton}</navigation>
<dependencies>{summaries}</dependencies>
<modify>{full_code}</modify>
Think step by step. Output the solution.""",
        
        "sonnet": """Task: {task}

Code structure:
{skeleton}

Relevant code:
{summaries}
{full_code}

Analyze and provide the solution.""",
        
        "validation": """<context>{task}</context>
<structure>{skeleton}</structure>
<output>{code_to_validate}</output>

Validate. JSON only (max 100 tokens):
{{"pass": bool, "issues": ["..."], "confidence": 0-1, "escalate": bool}}"""
    }
    
    def __init__(self):
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.cerebras_key = os.getenv("CEREBRAS_API_KEY")
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    
    def execute(
        self,
        model: str,
        task: str,
        context: AuZoomContext,
        output_limit: Optional[int] = None
    ) -> ExecutionResult:
        """Execute task on specified model with AuZoom context"""
        
        import time
        start = time.time()
        
        # Build prompt from template
        template_key = self._get_template_key(model)
        prompt = self.PROMPT_TEMPLATES[template_key].format(
            task=task,
            skeleton=context.skeleton,
            summaries="\n".join(context.summaries),
            full_code="\n".join(context.full_code)
        )
        
        try:
            if "local" in model or "qwen" in model.lower():
                response = self._call_ollama(model, prompt, output_limit)
            elif "glm" in model or "cerebras" in model:
                response = self._call_cerebras(prompt, output_limit)
            elif "haiku" in model:
                response = self._call_anthropic("claude-3-haiku-20240307", prompt, output_limit)
            elif "sonnet" in model:
                response = self._call_anthropic("claude-3-5-sonnet-20241022", prompt, output_limit)
            elif "opus" in model:
                response = self._call_anthropic("claude-3-opus-20240229", prompt, output_limit)
            else:
                raise ValueError(f"Unknown model: {model}")
            
            latency = int((time.time() - start) * 1000)
            
            return ExecutionResult(
                model=model,
                response=response["content"],
                tokens_in=response.get("tokens_in", len(prompt) // 4),
                tokens_out=response.get("tokens_out", len(response["content"]) // 4),
                latency_ms=latency,
                success=True
            )
            
        except Exception as e:
            return ExecutionResult(
                model=model,
                response="",
                tokens_in=0,
                tokens_out=0,
                latency_ms=int((time.time() - start) * 1000),
                success=False,
                error=str(e)
            )
    
    def _get_template_key(self, model: str) -> str:
        if "local" in model or "qwen" in model.lower():
            return "local"
        elif "glm" in model:
            return "glm"
        elif "haiku" in model:
            return "haiku"
        else:
            return "sonnet"
    
    def _call_ollama(self, model: str, prompt: str, max_tokens: Optional[int]) -> Dict:
        """Call local Ollama model"""
        import requests
        
        model_name = model.replace("local/", "")
        response = requests.post(
            f"{self.ollama_host}/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": max_tokens} if max_tokens else {}
            }
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            "content": data["response"],
            "tokens_in": data.get("prompt_eval_count", 0),
            "tokens_out": data.get("eval_count", 0)
        }
    
    def _call_anthropic(self, model: str, prompt: str, max_tokens: Optional[int]) -> Dict:
        """Call Anthropic API"""
        import anthropic
        
        client = anthropic.Anthropic(api_key=self.anthropic_key)
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens or 4096,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            "content": response.content[0].text,
            "tokens_in": response.usage.input_tokens,
            "tokens_out": response.usage.output_tokens
        }
    
    def _call_cerebras(self, prompt: str, max_tokens: Optional[int]) -> Dict:
        """Call Cerebras API (GLM 4.7)"""
        import requests
        
        response = requests.post(
            "https://api.cerebras.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.cerebras_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "glm-4.7",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens or 4096
            }
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            "content": data["choices"][0]["message"]["content"],
            "tokens_in": data["usage"]["prompt_tokens"],
            "tokens_out": data["usage"]["completion_tokens"]
        }


# =============================================================================
# MCP TOOL DEFINITIONS
# =============================================================================

class OrchestratorMCPServer:
    """
    MCP Server exposing unified AI orchestration tools.
    
    Tools:
    - auzoom_get_graph: Multi-resolution code navigation
    - auzoom_find: Semantic code search
    - orchestrator_route: Get routing recommendation
    - orchestrator_execute: Execute on optimal model
    - orchestrator_validate: Sonnet validation checkpoint
    - memory_retrieve: Get relevant past experiences
    - memory_store: Log outcome for learning
    """
    
    def __init__(self):
        self.auzoom = AuZoomBridge()
        self.context_builder = ContextBuilder(self.auzoom)
        self.router = RoutingEngine()
        self.executor = ModelExecutor()
        # self.memory = UnifiedMemory()  # From previous implementation
    
    # === AuZoom Tools ===
    
    def tool_auzoom_get_graph(
        self,
        node_id: str = "root",
        level: str = "skeleton",
        depth_down: int = 2,
        depth_up: int = 0
    ) -> Dict:
        """
        Get code graph at specified resolution.
        
        Levels:
        - skeleton: Names + dependencies (~15 tokens/node)
        - summary: + docstrings, signatures (~75 tokens/node)
        - full: + source code (~400 tokens/node)
        
        Start with skeleton, zoom in as needed.
        """
        fetch_level = FetchLevel(level)
        return self.auzoom.get_graph(node_id, fetch_level, depth_down, depth_up)
    
    def tool_auzoom_find(
        self,
        query: str,
        scope: Optional[str] = None
    ) -> List[str]:
        """Find nodes matching semantic query"""
        return self.auzoom.find(query, scope)
    
    def tool_auzoom_dependencies(
        self,
        node_id: str,
        direction: str = "both",
        depth: int = 1
    ) -> List[str]:
        """Get dependencies for a node"""
        return self.auzoom.get_dependencies(node_id, direction, depth)
    
    # === Orchestrator Tools ===
    
    def tool_orchestrator_route(
        self,
        task: str,
        files: int = 0,
        checkpoint: Optional[str] = None
    ) -> Dict:
        """
        Get model routing recommendation.
        
        Returns optimal model for task with confidence score.
        Claude Code can accept or override this recommendation.
        """
        context = {"files": files}
        if checkpoint:
            context["checkpoint"] = checkpoint
        
        decision = self.router.route(task, context)
        return asdict(decision)
    
    def tool_orchestrator_execute(
        self,
        model: str,
        task: str,
        target_nodes: Optional[List[str]] = None
    ) -> Dict:
        """
        Execute task on specified model with AuZoom-optimized context.
        
        Context is automatically built at appropriate resolution for the model:
        - Local/Haiku: Minimal (skeleton + target only)
        - GLM: Medium (+ dependency summaries)
        - Sonnet/Opus: Full (+ dependency code)
        """
        target_nodes = target_nodes or []
        
        # Build optimal context for this model
        context = self.context_builder.build_for_model(task, model, target_nodes)
        
        # Get output limit if applicable
        decision = self.router.route(task, {"model_override": model})
        
        # Execute
        result = self.executor.execute(
            model=model,
            task=task,
            context=context,
            output_limit=decision.output_limit
        )
        
        return asdict(result)
    
    def tool_orchestrator_validate(
        self,
        task: str,
        output: str,
        target_nodes: Optional[List[str]] = None
    ) -> Dict:
        """
        Validate output using Sonnet (input-heavy mode).
        
        Sonnet reads the full output + context but produces
        minimal response (max 100 tokens).
        
        Returns: {pass, issues, confidence, escalate}
        """
        target_nodes = target_nodes or []
        
        # Build validation context
        context = self.context_builder.build_for_model(
            task, "sonnet", target_nodes
        )
        
        # Add output to validate
        validation_context = AuZoomContext(
            skeleton=context.skeleton,
            summaries=context.summaries,
            full_code=[output],  # The output to validate
            total_tokens=context.total_tokens + len(output) // 4,
            nodes_included=context.nodes_included
        )
        
        # Execute validation with strict output limit
        result = self.executor.execute(
            model="sonnet",
            task=f"Validate this solution for: {task}",
            context=validation_context,
            output_limit=100
        )
        
        # Parse JSON response
        try:
            validation = json.loads(result.response)
        except:
            validation = {
                "pass": False,
                "issues": ["Failed to parse validation"],
                "confidence": 0,
                "escalate": True
            }
        
        return {
            "validation": validation,
            "tokens_used": result.tokens_in + result.tokens_out,
            "latency_ms": result.latency_ms
        }


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run as MCP server"""
    # TODO: Implement MCP protocol handling
    # For now, demo the tools
    
    server = OrchestratorMCPServer()
    
    # Example workflow
    task = "Fix the login validation bug"
    
    # 1. Get routing recommendation
    routing = server.tool_orchestrator_route(task, files=1)
    print(f"Routing: {routing['model']} ({routing['reason']})")
    
    # 2. Execute with AuZoom-optimized context
    result = server.tool_orchestrator_execute(
        model=routing["model"],
        task=task,
        target_nodes=["auth.service.login"]
    )
    print(f"Result: {result['tokens_in']} in / {result['tokens_out']} out")
    
    # 3. Validate if required
    if routing.get("validation_required"):
        validation = server.tool_orchestrator_validate(
            task=task,
            output=result["response"],
            target_nodes=["auth.service.login"]
        )
        print(f"Validation: {validation['validation']}")


if __name__ == "__main__":
    main()
