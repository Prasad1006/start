# backend/pydantic_models.py (NEW FILE)
from pydantic import BaseModel, Field
from typing import List

class OnboardingData(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, pattern="^[a-zA-Z0-9_]+$")
    headline: str
    primaryGoal: str
    preferredLanguages: List[str]
    stream: str
    branch: str
    selectedDomains: List[str]
    skillsToLearn: List[str] = []
    skillsToTeach: List[str] = []

class LearningTrack(BaseModel):
    skill: str
    skill_slug: str
    progress_summary: str
    progress_percent: int
    generated: bool

class DashboardData(BaseModel):
    name: str
    points: int
    isTutor: bool
    learningTracks: List[LearningTrack]