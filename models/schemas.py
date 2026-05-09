"""
Pydantic schemas for the HR Resume Shortlisting Agent.
All LLM outputs are validated against these models.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class HireRecommendation(str, Enum):
    STRONG_HIRE = "Strong Hire"
    HIRE = "Hire"
    MAYBE = "Maybe"
    NO_HIRE = "No Hire"


class JDRequirements(BaseModel):
    job_title: str = Field(description="The job title being hired for")
    required_skills: List[str] = Field(default=[], description="Must-have technical and soft skills")
    preferred_skills: List[str] = Field(default=[], description="Nice-to-have skills")
    min_experience_years: int = Field(default=0, description="Minimum years of relevant experience")
    education_requirements: str = Field(default="Not specified", description="Minimum education level")
    key_responsibilities: List[str] = Field(default=[], description="Main job responsibilities")
    certifications: List[str] = Field(default=[], description="Required or preferred certifications")
    domain: str = Field(default="General", description="Primary domain/industry of the role")
    seniority_level: str = Field(default="Mid", description="Junior/Mid/Senior/Lead/Principal")


class DimensionScore(BaseModel):
    dimension: str
    weight: float         # As a fraction, e.g. 0.30
    raw_score: float      # 0–10
    weighted_score: float # raw_score * weight
    justification: str


class CandidateProfile(BaseModel):
    name: str = Field(default="Unknown Candidate")
    email: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None)
    skills: List[str] = Field(default=[])
    experience_years: float = Field(default=0)
    experience_domains: List[str] = Field(default=[])
    education: str = Field(default="Not specified")
    certifications: List[str] = Field(default=[])
    projects: List[str] = Field(default=[])
    summary: Optional[str] = Field(default=None)
    current_role: Optional[str] = Field(default=None)


class CandidateScore(BaseModel):
    candidate_name: str
    file_name: str
    profile: CandidateProfile
    scores: List[DimensionScore]
    total_score: float          # 0–10
    recommendation: HireRecommendation
    overall_justification: str
    strengths: List[str] = Field(default=[])
    gaps: List[str] = Field(default=[])
    is_overridden: bool = False
    override_reason: Optional[str] = None
    original_total_score: Optional[float] = None
    original_recommendation: Optional[str] = None


class ShortlistReport(BaseModel):
    job_title: str
    jd_summary: JDRequirements
    candidates: List[CandidateScore]
    generated_at: str
    total_analyzed: int
    recommended_count: int
