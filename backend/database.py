# Add this endpoint to your existing main.py file

class LearningTrack(BaseModel):
    skill: str
    skill_slug: str
    progress_summary: str
    progress_percent: int

class DashboardData(BaseModel):
    points: int
    isTutor: bool
    learningTracks: List[LearningTrack]

@app.get("/api/dashboard", response_model=DashboardData)
async def get_dashboard_data(current_user: dict = Depends(get_current_user)):
    """
    Fetches and aggregates all data needed for the main user dashboard.
    """
    username = current_user.get("username")
    if not username:
        raise HTTPException(status_code=403, detail="Username not found in token")

    try:
        user_profile = users_collection.find_one({"username": username})
        if not user_profile:
            # This should theoretically never be hit if the gatekeeper is working,
            # but it's good practice to have this check.
            raise HTTPException(status_code=404, detail="User profile not found.")

        # 1. Get points and tutor status
        points = user_profile.get("points", 0)
        is_tutor = user_profile.get("tutorProfile", {}).get("isTutor", False)

        # 2. Fetch and process learning roadmaps into learning tracks
        learning_tracks = []
        roadmaps_cursor = roadmaps_collection.find({"username": username})
        for roadmap in roadmaps_cursor:
            total_weeks = len(roadmap.get("weeklyPlan", []))
            completed_weeks = sum(1 for week in roadmap.get("weeklyPlan", []) if week.get("status") == "COMPLETED")
            
            progress_percent = (completed_weeks / total_weeks * 100) if total_weeks > 0 else 0
            
            learning_tracks.append({
                "skill": roadmap.get("skill"),
                "skill_slug": roadmap.get("skill").lower().replace(" ", "-"), # e.g., "Python for Data Science" -> "python-for-data-science"
                "progress_summary": f"{completed_weeks}/{total_weeks} Modules Complete",
                "progress_percent": int(progress_percent)
            })

        # Assemble the final data object
        dashboard_data = {
            "points": points,
            "isTutor": is_tutor,
            "learningTracks": learning_tracks
        }
        return dashboard_data

    except Exception as e:
        print(f"!!! ERROR fetching dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Could not fetch dashboard data.")