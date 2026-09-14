import os
import uuid
import json
import re

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from database import init_db, get_db_connection

app = FastAPI(
    title="CampusPrep AI API",
    version="1.0.0",
    description="Backend service for Campus Placement Preparation Assistant"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure database is initialized on startup
@app.on_event("startup")
def startup_event():
    init_db()

# --- Pydantic Models ---
class ResumeScanRequest(BaseModel):
    resume_text: str
    target_company: Optional[str] = "zoho"

class SessionInitiateRequest(BaseModel):
    company_slug: str
    domain: Optional[str] = None

class SessionTurnRequest(BaseModel):
    session_id: str
    question_id: int
    answer_text: str
    duration_seconds: Optional[float] = 20.0

# --- Domain Competencies Directory ---
DOMAIN_KEYWORDS = {
    "DSA": ["algorithm", "data structure", "array", "linked list", "tree", "graph", "hash map", "binary search", "recursion", "dynamic programming", "time complexity", "o(n)", "space complexity"],
    "Core CS/OS": ["operating system", "process", "thread", "virtual memory", "paging", "deadlock", "tlb", "mutex", "concurrency", "cpu scheduling", "cache"],
    "DBMS": ["sql", "database", "normalization", "3nf", "bcnf", "acid", "index", "b-tree", "join", "transaction", "primary key", "foreign key"],
    "System Architecture": ["microservices", "api gateway", "load balancing", "caching", "redis", "rate limiter", "scalability", "message queue", "kafka", "rest api"],
    "Web": ["javascript", "typescript", "react", "html", "css", "cors", "jwt", "http", "options", "restful", "node.js", "frontend", "backend"],
    "AI/ML": ["python", "machine learning", "deep learning", "neural network", "regularization", "overfitting", "underfitting", "tensorflow", "pytorch", "scikit-learn", "model"],
    "Cloud/DevOps": ["docker", "kubernetes", "aws", "gcp", "ci/cd", "git", "linux", "cloud", "terraform"]
}

FILLER_WORDS = ["um", "uh", "like", "basically", "you know", "actually", "literally", "sort of", "kind of", "mean"]

# --- API Endpoints ---

@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "service": "CampusPrep AI",
        "version": "1.0.0",
        "database": "SQLite connected"
    }

@app.get("/api/v1/courses")
def get_courses():
    courses_data = [
        {
            "category": "Data Structures & Algorithms (DSA)",
            "icon": "fa-code",
            "courses": [
                {
                    "title": "take U forward (Striver's A2Z DSA Course)",
                    "provider": "Striver / take U forward",
                    "url": "https://www.youtube.com/playlist?list=PLgUwDviBIf0oF6QL8m22w1hIDC1vJ_BHz",
                    "coverage": "Arrays, Recursion, Binary Trees, Graphs, and Dynamic Programming tailored for campus technical interviews.",
                    "tag": "DSA Core"
                },
                {
                    "title": "NeetCode (DSA Algorithms Playlist)",
                    "provider": "NeetCode",
                    "url": "https://www.youtube.com/playlist?list=PLot-Xpze53lf5C3HSjCnyFghlW0G1QKXo",
                    "coverage": "Core LeetCode patterns, two-pointer methods, and time/space complexity optimization.",
                    "tag": "LeetCode Patterns"
                }
            ]
        },
        {
            "category": "Core CS Fundamentals (OS, DBMS, Networks)",
            "icon": "fa-microchip",
            "courses": [
                {
                    "title": "Gate Smashers (Operating Systems)",
                    "provider": "Gate Smashers",
                    "url": "https://www.youtube.com/playlist?list=PLxCzCOWd7aiGz9donHRrE9I3Mwn6XdP8p",
                    "coverage": "CPU Scheduling, Process Synchronization, Deadlocks, and Paging.",
                    "tag": "Operating Systems"
                },
                {
                    "title": "Gate Smashers (Database Management Systems)",
                    "provider": "Gate Smashers",
                    "url": "https://www.youtube.com/playlist?list=PLxCzCOWd7aiFAN6I8CuViBuCdJgiOkT2Y",
                    "coverage": "ER Diagrams, Relational Algebra, Normalization (1NF–BCNF), and ACID transactions.",
                    "tag": "DBMS"
                },
                {
                    "title": "NetworkChuck (Free CCNA / Computer Networks)",
                    "provider": "NetworkChuck",
                    "url": "https://www.youtube.com/playlist?list=PLIhvC56v63IJVXv0GJcl9vO5bdU5420Sm",
                    "coverage": "OSI model, TCP/IP handshake, DNS, routing, and subnets.",
                    "tag": "Computer Networks"
                }
            ]
        },
        {
            "category": "System Design",
            "icon": "fa-network-wired",
            "courses": [
                {
                    "title": "Gaurav Sen (System Design Primer)",
                    "provider": "Gaurav Sen",
                    "url": "https://www.youtube.com/playlist?list=PLMCXHnjXnTnvo6alSjVkgxV-VH6EPyvoX",
                    "coverage": "Horizontal scaling, Load Balancers, Caching strategies, Database Sharding, and Microservices.",
                    "tag": "System Design Primer"
                },
                {
                    "title": "ByteByteGo (Software Architecture & System Design)",
                    "provider": "ByteByteGo",
                    "url": "https://www.youtube.com/@ByteByteGo",
                    "coverage": "High-level diagrams explaining real-world systems (e.g., YouTube, WhatsApp, Rate Limiters).",
                    "tag": "Real-World Architecture"
                }
            ]
        },
        {
            "category": "Behavioral & HR Rounds (STAR Method)",
            "icon": "fa-user-tie",
            "courses": [
                {
                    "title": "CareerVidz (HR Interview Questions & Answers)",
                    "provider": "CareerVidz",
                    "url": "https://www.youtube.com/playlist?list=PL9A1BD522E90479A9",
                    "coverage": "Structuring 'Tell me about yourself', handling conflict questions, and executing the STAR technique.",
                    "tag": "HR & STAR Technique"
                }
            ]
        }
    ]
    return {"categories": courses_data}

@app.get("/api/v1/companies")
def get_companies():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT slug, name, logo_accent, description, primary_domains FROM companies")
    rows = cursor.fetchall()
    conn.close()

    companies = []
    for row in rows:
        companies.append({
            "slug": row["slug"],
            "name": row["name"],
            "logo_accent": row["logo_accent"],
            "description": row["description"],
            "primary_domains": json.loads(row["primary_domains"])
        })
    return {"companies": companies}

@app.post("/api/v1/resumes/scan")
def scan_resume(req: ResumeScanRequest):
    text = req.resume_text.lower()
    if not text.strip():
        raise HTTPException(status_code=400, detail="Resume text cannot be empty.")

    target = req.target_company.lower() if req.target_company else "zoho"

    # Evaluate domain scores
    domain_scores = {}
    found_competencies = []
    missing_competencies = []

    total_keywords_checked = 0
    total_keywords_found = 0

    for domain, keywords in DOMAIN_KEYWORDS.items():
        matched = [kw for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', text)]
        missing = [kw for kw in keywords if kw not in matched]
        
        score = round((len(matched) / len(keywords)) * 100) if keywords else 0
        domain_scores[domain] = {
            "score": score,
            "matched": matched,
            "missing": missing[:3]  # top 3 missing
        }

        found_competencies.extend(matched)
        missing_competencies.extend(missing[:2])
        
        total_keywords_checked += len(keywords)
        total_keywords_found += len(matched)

    # Base ATS match calculation with company weighting
    base_match = (total_keywords_found / total_keywords_checked) * 100 if total_keywords_checked > 0 else 0

    # Adjust for target company priority
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT primary_domains FROM companies WHERE slug = ?", (target,))
    company_row = cursor.fetchone()
    conn.close()

    if company_row:
        priority_domains = json.loads(company_row["primary_domains"])
        priority_scores = [domain_scores.get(d, {}).get("score", 0) for d in priority_domains]
        company_focused_match = (sum(priority_scores) / len(priority_scores)) if priority_scores else base_match
        ats_score = round(0.4 * base_match + 0.6 * company_focused_match)
    else:
        ats_score = round(base_match)

    ats_score = max(25, min(98, ats_score))  # normalize score range

    # Recommendations
    recommendations = []
    if domain_scores.get("DSA", {}).get("score", 0) < 50:
        recommendations.append({
            "priority": "HIGH",
            "domain": "DSA",
            "title": "Strengthen Core Algorithmic Depth",
            "action": "Include explicit references to Time/Space Complexity analysis (Big-O), Floyd's Cycle Detection, or Dynamic Programming implementations."
        })
    if domain_scores.get("Core CS/OS", {}).get("score", 0) < 50:
        recommendations.append({
            "priority": "HIGH",
            "domain": "Core CS/OS",
            "title": "Highlight OS & Concurrency Fundamentals",
            "action": "Add keywords like Virtual Memory, Thread Synchronization, Paging, and Deadlock prevention."
        })
    if domain_scores.get("System Architecture", {}).get("score", 0) < 50:
        recommendations.append({
            "priority": "MEDIUM",
            "domain": "System Architecture",
            "title": "Add Distributed System Concepts",
            "action": "Mention REST APIs, Microservices, Caching (Redis), and Message Queue integration."
        })
    if domain_scores.get("DBMS", {}).get("score", 0) < 50:
        recommendations.append({
            "priority": "MEDIUM",
            "domain": "DBMS",
            "title": "Demonstrate Database Optimization",
            "action": "Highlight SQL join optimization, Database Normalization (3NF/BCNF), and indexing strategies."
        })

    if not recommendations:
        recommendations.append({
            "priority": "LOW",
            "domain": "General",
            "title": "Excellent Keyword Alignment",
            "action": "Quantify your achievements with metrics (e.g., 'Optimized query latency by 40%')."
        })

    return {
        "ats_match_percentage": ats_score,
        "target_company": target,
        "domain_matrix": domain_scores,
        "found_competencies_count": len(found_competencies),
        "missing_competencies": list(set(missing_competencies))[:8],
        "recommendations": recommendations
    }

@app.post("/api/v1/interviews/sessions/initiate")
def initiate_interview_session(req: SessionInitiateRequest):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verify company exists
    cursor.execute("SELECT slug, name FROM companies WHERE slug = ?", (req.company_slug.lower(),))
    company = cursor.fetchone()
    if not company:
        conn.close()
        raise HTTPException(status_code=404, detail="Company track not found.")

    # Fetch initial question
    if req.domain:
        cursor.execute(
            "SELECT id, domain, difficulty, question_text, key_terms, sample_hint FROM questions WHERE company_slug = ? AND domain = ? ORDER BY RANDOM() LIMIT 1",
            (req.company_slug.lower(), req.domain)
        )
    else:
        cursor.execute(
            "SELECT id, domain, difficulty, question_text, key_terms, sample_hint FROM questions WHERE company_slug = ? ORDER BY RANDOM() LIMIT 1",
            (req.company_slug.lower(),)
        )

    q = cursor.fetchone()
    if not q:
        # Fallback to any company question
        cursor.execute("SELECT id, domain, difficulty, question_text, key_terms, sample_hint FROM questions ORDER BY RANDOM() LIMIT 1")
        q = cursor.fetchone()

    session_id = str(uuid.uuid4())

    cursor.execute(
        "INSERT INTO interview_sessions (session_id, company_slug, domain, total_questions, current_question_index) VALUES (?, ?, ?, 5, 1)",
        (session_id, req.company_slug.lower(), q["domain"])
    )
    conn.commit()
    conn.close()

    return {
        "session_id": session_id,
        "company_slug": company["slug"],
        "company_name": company["name"],
        "current_step": 1,
        "total_questions": 5,
        "question": {
            "id": q["id"],
            "category": q["domain"],
            "difficulty": q["difficulty"],
            "prompt": q["question_text"],
            "hint": q["sample_hint"]
        }
    }

@app.post("/api/v1/interviews/sessions/turn")
def execute_interview_turn(req: SessionTurnRequest):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check session
    cursor.execute("SELECT session_id, company_slug, current_question_index, total_questions FROM interview_sessions WHERE session_id = ?", (req.session_id,))
    session = cursor.fetchone()
    if not session:
        conn.close()
        raise HTTPException(status_code=404, detail="Interview session not found.")

    # Fetch question details
    cursor.execute("SELECT id, company_slug, domain, difficulty, question_text, key_terms, sample_hint FROM questions WHERE id = ?", (req.question_id,))
    q = cursor.fetchone()
    if not q:
        conn.close()
        raise HTTPException(status_code=404, detail="Question ID not found.")

    answer_text = req.answer_text.strip()
    duration_seconds = max(5.0, req.duration_seconds or 20.0)

    # 1. Calculate WPM (Speaking Pace)
    words = re.findall(r'\b\w+\b', answer_text)
    word_count = len(words)
    wpm = round((word_count / duration_seconds) * 60, 1)

    # 2. Detect Filler Words
    fillers_found = []
    for filler in FILLER_WORDS:
        matches = re.findall(r'\b' + re.escape(filler) + r'\b', answer_text.lower())
        if matches:
            fillers_found.extend(matches)
    filler_count = len(fillers_found)

    # 3. Technical Keyword Resonance
    key_terms = json.loads(q["key_terms"]) if q["key_terms"] else []
    matched_terms = [kt for kt in key_terms if re.search(r'\b' + re.escape(kt) + r'\b', answer_text.lower())]
    missing_terms = [kt for kt in key_terms if kt not in matched_terms]

    keyword_ratio = len(matched_terms) / len(key_terms) if key_terms else 0.5

    # 4. Technical Score (1 to 10)
    length_bonus = min(2.0, word_count / 30.0)
    filler_penalty = min(2.5, filler_count * 0.5)
    
    raw_score = (keyword_ratio * 7.5) + length_bonus - filler_penalty
    technical_score = round(max(2.0, min(10.0, raw_score)), 1)

    # 5. Continuous Critique & Feedback
    strengths = []
    improvements = []

    if matched_terms:
        strengths.append(f"Demonstrated technical terminology: {', '.join(matched_terms[:4])}.")
    if wpm >= 110 and wpm <= 160:
        strengths.append(f"Optimal speaking pace ({wpm} WPM). Clear, steady delivery.")
    elif wpm > 160:
        improvements.append(f"Speaking pace is rapid ({wpm} WPM). Moderate your tempo for clarity.")
    elif wpm < 90:
        improvements.append(f"Speaking pace is slow ({wpm} WPM). Elaborate further on your technical explanation.")

    if filler_count > 0:
        improvements.append(f"Detected {filler_count} filler words ({', '.join(set(fillers_found))}). Pause deliberately instead of using vocal fillers.")

    if missing_terms:
        improvements.append(f"Incorporate missing key concepts: {', '.join(missing_terms[:3])}.")

    critique_summary = f"Score: {technical_score}/10. "
    if strengths:
        critique_summary += " " + " ".join(strengths)
    if improvements:
        critique_summary += " " + " ".join(improvements)

    # Record Turn in DB
    cursor.execute("""
    INSERT INTO session_turns (session_id, question_id, answer_text, duration_seconds, wpm, filler_count, technical_score, critique)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (req.session_id, req.question_id, answer_text, duration_seconds, wpm, filler_count, technical_score, critique_summary))

    # Advance session question index
    next_index = session["current_question_index"] + 1
    cursor.execute("UPDATE interview_sessions SET current_question_index = ? WHERE session_id = ?", (next_index, req.session_id))
    conn.commit()

    # Determine if interview session complete or select next question
    is_completed = next_index > session["total_questions"]
    next_question = None

    if not is_completed:
        # Fetch next question for the company
        cursor.execute(
            "SELECT id, domain, difficulty, question_text, key_terms, sample_hint FROM questions WHERE company_slug = ? AND id != ? ORDER BY RANDOM() LIMIT 1",
            (session["company_slug"], req.question_id)
        )
        nq = cursor.fetchone()
        if not nq:
            cursor.execute("SELECT id, domain, difficulty, question_text, key_terms, sample_hint FROM questions ORDER BY RANDOM() LIMIT 1")
            nq = cursor.fetchone()

        if nq:
            next_question = {
                "id": nq["id"],
                "category": nq["domain"],
                "difficulty": nq["difficulty"],
                "prompt": nq["question_text"],
                "hint": nq["sample_hint"]
            }

    # Fetch cumulative stats for session
    cursor.execute("SELECT AVG(technical_score) as avg_score, AVG(wpm) as avg_wpm, SUM(filler_count) as total_fillers FROM session_turns WHERE session_id = ?", (req.session_id,))
    agg = cursor.fetchone()
    conn.close()

    cumulative_stats = {
        "average_score": round(agg["avg_score"] or technical_score, 1),
        "average_wpm": round(agg["avg_wpm"] or wpm, 1),
        "total_fillers": agg["total_fillers"] or filler_count
    }

    return {
        "turn_evaluation": {
            "wpm": wpm,
            "filler_count": filler_count,
            "fillers_detected": list(set(fillers_found)),
            "technical_score": technical_score,
            "matched_keywords": matched_terms,
            "missing_keywords": missing_terms,
            "critique": critique_summary,
            "strengths": strengths,
            "improvements": improvements
        },
        "cumulative_stats": cumulative_stats,
        "is_completed": is_completed,
        "current_step": next_index,
        "total_questions": session["total_questions"],
        "next_question": next_question
    }

# --- Static File Serving ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "static")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def read_root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "CampusPrep AI API is running."}
