import os
import time
from enum import Enum
from dotenv import load_dotenv
from pydantic import BaseModel, field_validator
import instructor
from groq import Groq
from langfuse import get_client

from testsentry.fingerprinter import fingerprint
from testsentry.collector import cache_lookup, cache_store

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Langfuse v4 client
langfuse = get_client()


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

    @field_validator("confidence_pct", mode="before")
    @classmethod
    def parse_confidence(cls, v):
        """Accept both int and string for confidence_pct."""
        return int(v)


def get_groq_client():
    """Create Instructor-wrapped Groq client."""
    groq_client = Groq(api_key=GROQ_API_KEY)
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

    # Step 1 — Generate fingerprint
    fp = fingerprint(error_msg)

    # Step 2 — Check cache first
    cached = cache_lookup(fp)
    if cached:
        print(f"\n[TestSentry] 💾 CACHE HIT — {test_name}")
        print(f"             Category: {cached['category']}")

        # Log cache hit to Langfuse v4
        try:
            with langfuse.start_as_current_observation(
                as_type="span",
                name="triage-cache-hit",
                input={"test_name": test_name, "fingerprint": fp},
            ) as span:
                span.update(
                    output={"category": cached["category"]},
                    metadata={"cache_hit": True, "api_cost": 0.0}
                )
            langfuse.flush()
        except Exception as e:
            print(f"[TestSentry] ⚠️ Langfuse error: {e}")

        return cached

    # Step 3 — Cache miss — call Groq API
    print(f"\n[TestSentry] 🤖 AI TRIAGE — {test_name}")

    try:
        client = get_groq_client()
        start_time = time.time()

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

Return a structured triage with category, confidence as a plain integer
(not a string, e.g. 92 not "92"), why it failed, and suggested fix."""
                }
            ]
        )

        latency_ms = round((time.time() - start_time) * 1000, 2)

        # Safely handle category
        try:
            category_value = triage.category.value if isinstance(triage.category, Enum) else str(triage.category)
        except Exception:
            category_value = str(triage.category)

        # Step 4 — Build result dict
        triage_dict = {
            "category":        category_value,
            "confidence_pct":  int(triage.confidence_pct),
            "why_it_failed":   triage.why_it_failed,
            "suggested_fix":   triage.suggested_fix,
            "affected_module": triage.affected_module,
            "cache_hit":       False
        }

        # Step 5 — Store in cache
        cache_store(fp, triage_dict)

        # Log API call to Langfuse v4
        try:
            with langfuse.start_as_current_observation(
                as_type="generation",
                name="triage-api-call",
                model="llama-3.3-70b-versatile",
                input={"test_name": test_name, "error_msg": error_msg[:200]},
            ) as span:
                span.update(
                    output=triage_dict,
                    metadata={
                        "cache_hit": False,
                        "latency_ms": latency_ms,
                    }
                )
            langfuse.flush()
        except Exception as e:
            print(f"[TestSentry] ⚠️ Langfuse error: {e}")

        # Print result
        print(f"             Category:   {triage_dict['category']}")
        print(f"             Confidence: {triage_dict['confidence_pct']}%")
        print(f"             Why:        {triage_dict['why_it_failed']}")
        print(f"             Fix:        {triage_dict['suggested_fix']}")

        return triage_dict

    except Exception as e:
        print(f"\n[TestSentry] ⚠️ Triage error: {type(e).__name__}: {str(e)}")
        print(f"             Skipping AI analysis for this failure")
        return None