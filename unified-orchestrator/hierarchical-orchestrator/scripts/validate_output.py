#!/usr/bin/env python3
"""
Compact validation using Sonnet in input-heavy mode.
Reads generated output, emits minimal feedback (max 100 tokens).
"""

import json
import os
from typing import Optional, Dict
from dataclasses import dataclass

@dataclass
class ValidationResult:
    passed: bool
    issues: list
    confidence: float
    escalate: bool
    raw_response: str

VALIDATION_PROMPT = """<context>
{context}
</context>

<output_to_validate>
{output}
</output_to_validate>

Validate this output against the requirements. Respond ONLY with valid JSON (max 100 tokens):
{{"pass": boolean, "issues": ["max 3 issues, each under 20 words"], "confidence": 0.0-1.0, "escalate": boolean}}

Rules:
- pass: true if output meets requirements
- issues: list up to 3 critical issues (empty if pass=true)
- confidence: your confidence in this assessment
- escalate: true if this needs Opus-level review (architecture decisions, security concerns)"""

class SonnetValidator:
    """Validates outputs using Sonnet in input-heavy mode"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        
    def validate(
        self,
        output: str,
        context: str,
        max_output_tokens: int = 100
    ) -> ValidationResult:
        """
        Validate generated output using Sonnet.
        
        Args:
            output: The generated code/text to validate
            context: Task description and requirements
            max_output_tokens: Max tokens for Sonnet's response (default 100)
        
        Returns:
            ValidationResult with pass/fail, issues, confidence, escalation
        """
        prompt = VALIDATION_PROMPT.format(
            context=context,
            output=output
        )
        
        # Call Sonnet
        response = self._call_sonnet(prompt, max_output_tokens)
        
        # Parse response
        return self._parse_response(response)
    
    def _call_sonnet(self, prompt: str, max_tokens: int) -> str:
        """Call Sonnet API"""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
        except ImportError:
            raise RuntimeError("anthropic package not installed. Run: pip install anthropic")
        except Exception as e:
            raise RuntimeError(f"Sonnet API call failed: {e}")
    
    def _parse_response(self, response: str) -> ValidationResult:
        """Parse Sonnet's JSON response"""
        try:
            # Clean up response (remove markdown code blocks if present)
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            
            data = json.loads(clean)
            
            return ValidationResult(
                passed=data.get("pass", False),
                issues=data.get("issues", []),
                confidence=data.get("confidence", 0.5),
                escalate=data.get("escalate", False),
                raw_response=response
            )
            
        except json.JSONDecodeError:
            # If parsing fails, treat as failed validation
            return ValidationResult(
                passed=False,
                issues=["Failed to parse validation response"],
                confidence=0.0,
                escalate=True,
                raw_response=response
            )

def opus_redirect(task: str, attempts: list, api_key: Optional[str] = None) -> Dict:
    """
    Get strategic redirect from Opus (max 50 tokens output).
    Only called when validation escalates or multiple failures.
    """
    prompt = f"""<task>{task}</task>
<previous_attempts>
{json.dumps(attempts[-3:], indent=2)}
</previous_attempts>

Provide strategic redirect. Max 50 tokens. JSON only:
{{"redirect": "brief instruction", "reason": "why", "complexity_adjustment": int}}"""
    
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
        
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=50,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return json.loads(response.content[0].text)
        
    except Exception as e:
        return {"redirect": "retry with simpler approach", "reason": str(e), "complexity_adjustment": -1}

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Validate output using Sonnet")
    parser.add_argument("--output", required=True, help="Output to validate (file path or string)")
    parser.add_argument("--context", required=True, help="Task context (file path or string)")
    parser.add_argument("--max-tokens", type=int, default=100, help="Max output tokens")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    # Load from file if path exists
    output = args.output
    if os.path.exists(output):
        with open(output) as f:
            output = f.read()
    
    context = args.context
    if os.path.exists(context):
        with open(context) as f:
            context = f.read()
    
    validator = SonnetValidator()
    result = validator.validate(output, context, args.max_tokens)
    
    if args.json:
        print(json.dumps({
            "passed": result.passed,
            "issues": result.issues,
            "confidence": result.confidence,
            "escalate": result.escalate
        }, indent=2))
    else:
        status = "✅ PASSED" if result.passed else "❌ FAILED"
        print(f"Validation: {status}")
        print(f"Confidence: {result.confidence:.0%}")
        
        if result.issues:
            print("\nIssues:")
            for issue in result.issues:
                print(f"  • {issue}")
        
        if result.escalate:
            print("\n⚠️  Escalation recommended - needs Opus review")

if __name__ == "__main__":
    main()
