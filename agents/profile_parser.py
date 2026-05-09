"""
Profile Parser Agent
Extracts structured candidate data from raw resume text using an LLM.
"""
from models.schemas import CandidateProfile
from utils.llm_client import chat_completion, extract_json

_SYSTEM_PROMPT = """You are an expert resume parser. Extract structured candidate information 
from the provided resume text.

You MUST respond with ONLY a valid JSON object — no extra text, no markdown.

JSON schema to follow:
{
  "name": "Full name of the candidate (use 'Unknown' if not found)",
  "email": "email address or null",
  "phone": "phone number or null",
  "skills": ["list of ALL technical and soft skills mentioned"],
  "experience_years": float (total years of professional experience, 0 if fresher),
  "experience_domains": ["list of domains/industries worked in"],
  "education": "highest degree and field, e.g. B.Tech Computer Science from XYZ University",
  "certifications": ["list of certifications, courses, and training completed"],
  "projects": ["list of project names or brief descriptions (1 line each)"],
  "summary": "2-3 sentence professional summary of the candidate",
  "current_role": "most recent job title or null"
}

Rules:
- experience_years must be a number (float or int), NOT a string.
- Extract every skill you can identify, including programming languages, frameworks, tools, soft skills.
- Be precise — do not hallucinate information not present in the resume.
- projects should list the project names/titles, not long descriptions.
"""


def parse_profile(
    resume_text: str,
    filename: str,
    model: str = None,
    api_key: str = None,
) -> CandidateProfile:
    """
    Parse raw resume text into a structured CandidateProfile.

    Args:
        resume_text: Raw extracted text from a resume file
        filename: Original filename (for reference)
        model: OpenRouter model string
        api_key: OpenRouter API key

    Returns:
        CandidateProfile pydantic model
    """
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Parse this resume (file: {filename}) and return structured JSON:\n\n"
                f"{resume_text}"
            ),
        },
    ]

    raw = chat_completion(messages, model=model, api_key=api_key)
    data = extract_json(raw)

    # Coerce experience_years to float
    try:
        data["experience_years"] = float(data.get("experience_years", 0))
    except (ValueError, TypeError):
        data["experience_years"] = 0.0

    return CandidateProfile(**data)
