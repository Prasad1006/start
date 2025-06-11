# backend/main.py (Updated for new onboarding flow)

import os
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from jose import jwt, JWTError
import requests
import clerk_client
from clerk_client.api import users_api
from .database import users_collection

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# --- Configuration & Auth Setup ---
app = FastAPI()
CLERK_API_KEY = os.getenv("CLERK_API_KEY")
CLERK_JWT_ISSUER = os.getenv("CLERK_JWT_ISSUER")

if not CLERK_API_KEY or not CLERK_JWT_ISSUER:
    raise Exception("FATAL ERROR: Clerk environment variables are not set.")

clerk_client.configuration.api_key['Authorization'] = CLERK_API_KEY
JWKS_URL = f"{CLERK

---

### **Step 1: Create the Data Source (`skills.json`)**

This file will act as our "database" of skills and will drive the entire dynamic onboarding experience.

**Action:** In your `frontend` folder, create a new subfolder named `data`. Inside that new folder, create a file named `skills.json`.

**File: `frontend/data/skills.json`**

```json
{
  "BTech": {
    "Computer Science Engineering": {
      "domains": {
        "Web Development": {
          "skills": [ "HTML/CSS/JavaScript", "React.js", "Node.js/Express.js", "Django/Flask", "MongoDB/SQL" ]
        },
        "Artificial Intelligence": {
          "skills": [ "Python for AI/ML", "NumPy & Pandas", "scikit-learn", "TensorFlow", "PyTorch", "Natural Language Processing" ]
        },
        "Cybersecurity": {
          "skills": [ "Ethical Hacking", "Network Security", "Cryptography", "Kali Linux", "Metasploit", "Wireshark" ]
        },
        "Cloud Computing": {
          "skills": [ "AWS Fundamentals", "Docker & Containers", "Kubernetes", "Serverless Architecture (Vercel/Lambda)", "CI/CD" ]
        }
      }
    },
    "Electronics and Communication Engineering": {
      "domains": {
        "VLSI Design": {
          "skills": [ "Verilog/VHDL", "Digital Electronics", "Logic Synthesis", "ModelSim", "Xilinx Vivado" ]
        },
        "Embedded Systems": {
          "skills": [ "Microcontrollers (8051, ARM, Raspberry Pi)", "Embedded C", "Arduino", "IoT Protocols (MQTT)", "Keil/STM32CubeIDE" ]
        },
        "Signal Processing": {
          "skills": [ "MATLAB/Simulink", "Digital Signal Processing", "Image & Video Processing", "Python (scipy.signal)" ]
        }
      }
    },
    "Electrical Engineering": {
      "domains": {
        "Power Systems": {
          "skills": [ "Power System Analysis", "Switchgear & Protection", "ETAP", "MATPOWER", "Renewable Energy Systems" ]
        },
        "Control Systems": {
          "skills": [ "PID Control", "State-Space Analysis", "PLC & SCADA", "MATLAB Simulink", "Robotics" ]
        }
      }
    },
    "Mechanical Engineering": {
      "domains": {
        "Design and Manufacturing": {
          "skills": [ "AutoCAD/SolidWorks", "CATIA", "CAM/CNC Programming", "3D Printing", "Finite Element Analysis (FEA)" ]
        },
        "Thermal Engineering": {
          "skills": [ "Heat Transfer", "Thermodynamics", "IC Engines", "ANSYS Fluent", "HVAC Design" ]
        }
      }
    },
    "Civil Engineering": {
      "domains": {
        "Structural Engineering": {
          "skills": [ "STAAD Pro/ETABS", "Structural Analysis", "Reinforced Concrete Design", "AutoCAD", "SAP2000" ]
        },
        "Transportation Engineering": {
          "skills": [ "Highway Design", "Traffic Engineering", "AutoCAD Civil 3D", "Pavement Design" ]
        }
      }
    }
  }
}