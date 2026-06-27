import os
import json
from enum import Enum
from dotenv import load_dotenv
from pydantic import BaseModel
import instructor
from groq import Groq

from testsentry.fingerprinter import fingerprint
from testsentry.collector import cache_lookup, cache_store


load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


class FailureCategory(str, Enum):
    REAL_BUG   = "REAL_BUG"
    FLAKY      = "FLAKY"
    ENV_ISSUE  = "ENV_ISSUE"
    DATA_ISSUE = "DATA_ISSUE"


class TriageResult(BaseModel):
    category:        FailureCategory
    confidence_pct:  int
    why_it_failed:   str
    suggested_fix:   str
    affected_module: str


def get_client():
    """Create Instructor-wrapped Groq client."""
    groq_client = Groq(api_key = GROQ_API_KEY)
    return instructor.from_groq(groq_client)



def triage_failure(result: dict) -> dict:
    """
    Main entry point. Called from plugin.py on every failure.

    Flow:
    1. Generate fingerprint from error
    2. Check cache — return instantly if found
    3. Call Groq API if cache miss
    4. Store result in cache
    5. Return triage result
    """
    error_msg = result.get("error_msg", "")
    test_name = result.get("test_name", "")

    if not GROQ_API_KEY:
        print("\n[TestSentry] ⚠️ GROQ_API_KEY not set. Skipping AI triage.")
        return None

    if not error_msg:
        return None

   
    fp = fingerprint(error_msg)

   
    cached = cache_lookup(fp)
    if cached:
        print(f"\n[TestSentry] 💾 CACHE HIT — {test_name}")
        print(f"             Category: {cached['category']}")
        return cached

    
    print(f"\n[TestSentry] 🤖 AI TRIAGE — {test_name}")

    client = get_client()

    triage = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        response_model=TriageResult,
        messages=[
            {
                "role": "system",
                "content": """You are a senior QA engineer analyzing pytest failures.
                Categorize each failure into exactly one of:
                - REAL_BUG: actual code defect
                - FLAKY: non-deterministic, passes sometimes
                - ENV_ISSUE: environment/infrastructure problem
                - DATA_ISSUE: test data missing or wrong
                Always provide a clear explanation and actionable fix."""
            },
            {
                "role": "user",
                "content": f"""Analyze this pytest failure:

Test name: {test_name}
Error message: {error_msg}

Return a structured triage with category, confidence, why it failed, and suggested fix."""
            }
        ]
    )

    
    triage_dict = {
        "category":        triage.category.value,
        "confidence_pct":  triage.confidence_pct,
        "why_it_failed":   triage.why_it_failed,
        "suggested_fix":   triage.suggested_fix,
        "affected_module": triage.affected_module,
        "cache_hit":       False
    }
    cache_store(fp, triage_dict)

    
    print(f"             Category:   {triage_dict['category']}")
    print(f"             Confidence: {triage_dict['confidence_pct']}%")
    print(f"             Why:        {triage_dict['why_it_failed']}")
    print(f"             Fix:        {triage_dict['suggested_fix']}")

    return triage_dict