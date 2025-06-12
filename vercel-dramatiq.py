# vercel-dramatiq.py (NEW FILE IN ROOT)
from dramatiq.cli import main
from backend.tasks import generate_roadmap_task # Make sure our actor is imported

if __name__ == "__main__":
    main()