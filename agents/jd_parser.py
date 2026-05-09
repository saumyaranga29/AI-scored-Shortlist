"""
JD Parser Agent
Extracts structured requirements from a raw Job Description text using an LLM.
"""
import json
from models.schemas import JDRequirements
from utils.llm_client import chat_completion, extract_json

_SYSTEM_PROMPT = """You are an expert HR analyst. Your task is to parse a Job Description (JD) 
and extract structured requirements from it.

You MUST respond with ONLY a valid JSON object — no extra text, no markdown, no explanation.

JSON schema to follow:
{
  "job_title": "string",
  "required_skills": ["list of must-have skills"],
  "preferred_skills": ["list of nice-to-have skills"],
  "min_experience_years": integer,
  "education_requirements": "string (e.g. B.Tech/B.E. in CS or related field)",
  "key_responsibilities": ["list of main responsibilities"],
  "certifications": ["list of required/preferred certifications, empty if none"],
  "domain": "primary domain e.g. Software Engineering, Data Science, Finance",
  "seniority_level": "Junior | Mid | Senior | Lead | Principal"
}

Rules:
- If a field is not mentioned, use sensible defaults (empty list or 'Not specified').
- min_experience_years must be an integer (use 0 if not specified).
- Extract ALL skills mentioned anywhere in the JD.
- Separate required vs preferred skills based on language (must/required vs preferred/plus/bonus).
"""


def parse_jd(jd_text: str, model: str = None, api_key: str = None) -> JDRequirements:
    """
    Parse a Job Description into structured JDRequirements.
    
    Args:
        jd_text: Raw JD text
        model: OpenRouter model string
        api_key: OpenRouter API key
        
    Returns:
        JDRequirements pydantic model
    """
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Parse this Job Description and return structured JSON:\n\n{jd_text}",
        },
    ]

    raw = chat_completion(messages, model=model, api_key=api_key)
    data = extract_json(raw)

    # Ensure min_experience_years is an int
    if "min_experience_years" in data:
        try:
            data["min_experience_years"] = int(data["min_experience_years"])
        except (ValueError, TypeError):
            data["min_experience_years"] = 0

    return JDRequirements(**data)
