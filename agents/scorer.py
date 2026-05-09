"""
Scorer Agent
Evaluates a candidate profile against JD requirements using the mandatory 5-dimension rubric.
"""
from models.schemas import (
    JDRequirements,
    CandidateProfile,
    CandidateScore,
    DimensionScore,
    HireRecommendation,
)
from utils.llm_client import chat_completion, extract_json

# ── Rubric Definition ────────────────────────────────────────────────────────
RUBRIC = [
    {
        "dimension": "Skills Match",
        "weight": 0.30,
        "description": (
            "0–3: <30% skills match | "
            "4–6: 30–70% skills match | "
            "7–8: 70–85% skills match | "
            "9–10: >85% skills match"
        ),
    },
    {
        "dimension": "Experience Relevance",
        "weight": 0.25,
        "description": (
            "0–3: Unrelated domain/insufficient years | "
            "4–6: Adjacent domain or slightly under-experienced | "
            "7–8: Same domain, close seniority | "
            "9–10: Exact domain, exact or exceeds seniority"
        ),
    },
    {
        "dimension": "Education & Certifications",
        "weight": 0.15,
        "description": (
            "0–3: Does not meet minimum education | "
            "4–6: Meets minimum, no extras | "
            "7–8: Meets + has relevant certifications | "
            "9–10: Exceeds education requirement + strong certs"
        ),
    },
    {
        "dimension": "Project & Portfolio",
        "weight": 0.20,
        "description": (
            "0–3: No projects or evidence | "
            "4–6: 1–2 generic or unrelated projects | "
            "7–8: Relevant projects with decent complexity | "
            "9–10: Strong, directly relevant portfolio"
        ),
    },
    {
        "dimension": "Communication Quality",
        "weight": 0.10,
        "description": (
            "0–3: Poor grammar, unclear structure | "
            "4–6: Adequate clarity and structure | "
            "7–8: Clear and professional writing | "
            "9–10: Crisp, structured, impactful presentation"
        ),
    },
]

_SYSTEM_PROMPT = """You are a senior HR evaluator. Score a candidate against a Job Description 
using a structured 5-dimension rubric.

You MUST respond with ONLY a valid JSON object — no extra text, no markdown.

JSON schema:
{
  "scores": [
    {
      "dimension": "Skills Match",
      "weight": 0.30,
      "raw_score": float (0.0–10.0),
      "justification": "One concise sentence explaining this score"
    },
    {
      "dimension": "Experience Relevance",
      "weight": 0.25,
      "raw_score": float,
      "justification": "One concise sentence"
    },
    {
      "dimension": "Education & Certifications",
      "weight": 0.15,
      "raw_score": float,
      "justification": "One concise sentence"
    },
    {
      "dimension": "Project & Portfolio",
      "weight": 0.20,
      "raw_score": float,
      "justification": "One concise sentence"
    },
    {
      "dimension": "Communication Quality",
      "weight": 0.10,
      "raw_score": float,
      "justification": "One concise sentence"
    }
  ],
  "strengths": ["top 2-3 candidate strengths relevant to this role"],
  "gaps": ["top 2-3 skill or experience gaps vs the JD"],
  "overall_justification": "2-3 sentence overall assessment of fit"
}

Scoring guidance per dimension:
{rubric_guidance}

Be objective and consistent. Base scores strictly on evidence in the candidate profile.
"""

_RECOMMENDATION_THRESHOLDS = {
    8.0: HireRecommendation.STRONG_HIRE,
    6.5: HireRecommendation.HIRE,
    5.0: HireRecommendation.MAYBE,
}


def _get_recommendation(total: float) -> HireRecommendation:
    for threshold, rec in sorted(_RECOMMENDATION_THRESHOLDS.items(), reverse=True):
        if total >= threshold:
            return rec
    return HireRecommendation.NO_HIRE


def score_candidate(
    jd: JDRequirements,
    profile: CandidateProfile,
    file_name: str,
    model: str = None,
    api_key: str = None,
) -> CandidateScore:
    """
    Score a candidate against a JD using the 5-dimension rubric.

    Args:
        jd: Parsed JD requirements
        profile: Parsed candidate profile
        file_name: Original resume filename
        model: OpenRouter model string
        api_key: OpenRouter API key

    Returns:
        CandidateScore with dimension scores, total, and recommendation
    """
    rubric_guidance = "\n".join(
        f"- {r['dimension']} (weight {int(r['weight']*100)}%): {r['description']}"
        for r in RUBRIC
    )

    system_prompt = _SYSTEM_PROMPT.replace("{rubric_guidance}", rubric_guidance)

    user_content = f"""
JOB DESCRIPTION REQUIREMENTS:
- Job Title: {jd.job_title}
- Domain: {jd.domain}
- Seniority: {jd.seniority_level}
- Min Experience: {jd.min_experience_years} years
- Required Skills: {', '.join(jd.required_skills)}
- Preferred Skills: {', '.join(jd.preferred_skills)}
- Education: {jd.education_requirements}
- Certifications: {', '.join(jd.certifications) if jd.certifications else 'None specified'}
- Key Responsibilities: {'; '.join(jd.key_responsibilities[:5])}

CANDIDATE PROFILE:
- Name: {profile.name}
- Current Role: {profile.current_role or 'Not specified'}
- Experience: {profile.experience_years} years in {', '.join(profile.experience_domains) or 'Not specified'}
- Skills: {', '.join(profile.skills)}
- Education: {profile.education}
- Certifications: {', '.join(profile.certifications) if profile.certifications else 'None'}
- Projects: {'; '.join(profile.projects[:5]) if profile.projects else 'None listed'}
- Summary: {profile.summary or 'Not provided'}

Score this candidate against the JD using the 5-dimension rubric. Return JSON only.
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]

    raw = chat_completion(messages, model=model, api_key=api_key)
    data = extract_json(raw)

    # Build DimensionScore objects with weighted scores
    dimension_scores = []
    total = 0.0
    for s in data.get("scores", []):
        raw_score = float(s.get("raw_score", 0))
        weight = float(s.get("weight", 0))
        weighted = round(raw_score * weight, 3)
        total += weighted
        dimension_scores.append(
            DimensionScore(
                dimension=s["dimension"],
                weight=weight,
                raw_score=round(raw_score, 1),
                weighted_score=weighted,
                justification=s.get("justification", ""),
            )
        )

    total = round(total, 2)
    recommendation = _get_recommendation(total)

    return CandidateScore(
        candidate_name=profile.name,
        file_name=file_name,
        profile=profile,
        scores=dimension_scores,
        total_score=total,
        recommendation=recommendation,
        overall_justification=data.get("overall_justification", ""),
        strengths=data.get("strengths", []),
        gaps=data.get("gaps", []),
    )
