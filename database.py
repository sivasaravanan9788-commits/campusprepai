import sqlite3
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IS_VERCEL = os.environ.get("VERCEL", "0") == "1" or os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None

if IS_VERCEL:
    DB_PATH = "/tmp/campusprep.db"
else:
    DB_PATH = os.path.join(BASE_DIR, "campusprep.db")

def get_db_connection():
    if not os.path.exists(DB_PATH):
        init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create Companies Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        logo_accent TEXT NOT NULL,
        description TEXT NOT NULL,
        primary_domains TEXT NOT NULL
    );
    """)

    # Create Questions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_slug TEXT NOT NULL,
        domain TEXT NOT NULL,
        difficulty TEXT NOT NULL,
        question_text TEXT NOT NULL,
        key_terms TEXT NOT NULL,
        sample_hint TEXT NOT NULL,
        FOREIGN KEY (company_slug) REFERENCES companies (slug)
    );
    """)

    # Create Interview Sessions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interview_sessions (
        session_id TEXT PRIMARY KEY,
        company_slug TEXT NOT NULL,
        domain TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total_questions INTEGER DEFAULT 5,
        current_question_index INTEGER DEFAULT 0
    );
    """)

    # Create Session Turns Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS session_turns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        question_id INTEGER NOT NULL,
        answer_text TEXT NOT NULL,
        duration_seconds REAL NOT NULL,
        wpm REAL NOT NULL,
        filler_count INTEGER NOT NULL,
        technical_score REAL NOT NULL,
        critique TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES interview_sessions (session_id),
        FOREIGN KEY (question_id) REFERENCES questions (id)
    );
    """)

    # Seed Companies if empty
    cursor.execute("SELECT COUNT(*) FROM companies")
    if cursor.fetchone()[0] == 0:
        companies_data = [
            (
                "zoho",
                "Zoho Corporation",
                "#00f0ff",
                "Focuses on deep Data Structures & Algorithms, C/C++ memory management, low-level system design, and logical problem solving.",
                json.dumps(["DSA", "Core CS/OS", "System Architecture", "DBMS"])
            ),
            (
                "tcs",
                "Tata Consultancy Services (TCS)",
                "#38bdf8",
                "Evaluates core computer science fundamentals, OS thread management, SQL database queries, and structured problem analysis.",
                json.dumps(["Core CS/OS", "DBMS", "DSA", "Web"])
            ),
            (
                "cognizant",
                "Cognizant (CTS)",
                "#6366f1",
                "Emphasis on Object-Oriented Programming (Java/Python), RESTful Web Services, SQL database normalization, and Agile workflows.",
                json.dumps(["Web", "DBMS", "Core CS/OS", "HR/STAR"])
            ),
            (
                "infosys",
                "Infosys",
                "#a855f7",
                "Focuses on algorithmic efficiency, system design scalability, modern web architecture, AI/ML concepts, and HR communication.",
                json.dumps(["DSA", "System Architecture", "AI/ML", "HR/STAR"])
            )
        ]
        cursor.executemany("""
        INSERT INTO companies (slug, name, logo_accent, description, primary_domains)
        VALUES (?, ?, ?, ?, ?)
        """, companies_data)

    # Seed Questions if empty
    cursor.execute("SELECT COUNT(*) FROM questions")
    if cursor.fetchone()[0] == 0:
        questions_data = [
            # Zoho Questions
            (
                "zoho", "DSA", "Medium",
                "How do you detect a cycle in a singly linked list? Explain Floyd's Cycle-Finding Algorithm (Tortoise and Hare) and state its time and space complexity.",
                json.dumps(["floyd", "tortoise", "hare", "two pointers", "fast pointer", "slow pointer", "o(n)", "o(1) space"]),
                "Mention two pointers moving at different speeds (1 step vs 2 steps) meeting inside the loop."
            ),
            (
                "zoho", "Core CS/OS", "Hard",
                "Explain Virtual Memory, Paging, and Page Fault handling in operating systems. How does TLB (Translation Lookaside Buffer) optimize address translation?",
                json.dumps(["virtual memory", "paging", "page fault", "tlb", "mmu", "frame", "page table", "cache"]),
                "Discuss logical-to-physical address translation, page faults, and TLB cache hit/miss ratio."
            ),
            (
                "zoho", "System Architecture", "Hard",
                "Design a Rate Limiter for an API gateway. Compare the Token Bucket algorithm with the Leaky Bucket algorithm.",
                json.dumps(["rate limiter", "token bucket", "leaky bucket", "redis", "burst traffic", "sliding window", "capacity"]),
                "Contrast token refilling vs fixed drip rate, and mention distributed state storage like Redis."
            ),
            (
                "zoho", "DBMS", "Medium",
                "Explain Database Normalization up to 3NF and BCNF. Why might we intentionally denormalize a database in read-heavy production systems?",
                json.dumps(["1nf", "2nf", "3nf", "bcnf", "functional dependency", "denormalization", "joins", "read performance"]),
                "Define lossy vs lossless decomposition, functional dependencies, and reducing heavy SQL joins."
            ),

            # TCS Questions
            (
                "tcs", "Core CS/OS", "Easy",
                "What is Process vs Thread? Explain Deadlock conditions (Coffman conditions) and how Banker's Algorithm prevents it.",
                json.dumps(["process", "thread", "shared memory", "mutual exclusion", "hold and wait", "no preemption", "circular wait", "banker"]),
                "Detail shared address space of threads vs isolated process memory, plus the 4 Coffman conditions."
            ),
            (
                "tcs", "DBMS", "Medium",
                "Differentiate between INNER JOIN, LEFT OUTER JOIN, and FULL OUTER JOIN. How do database indexes (B-Trees) speed up lookup queries?",
                json.dumps(["inner join", "left join", "full join", "b-tree", "index", "binary search", "disk i/o"]),
                "Explain matching rows vs non-matching nulls, and how B-Trees reduce O(N) full table scans to O(log N)."
            ),
            (
                "tcs", "DSA", "Medium",
                "Write the pseudocode or algorithm to find the QuickSort pivot partition. What is the worst-case time complexity and how can randomized pivot selection mitigate it?",
                json.dumps(["quicksort", "pivot", "partition", "o(n log n)", "o(n^2)", "divide and conquer", "recursion"]),
                "Explain partitioning around a pivot, unbalanced recursion trees producing O(N^2), and random pivot selection."
            ),
            (
                "tcs", "Web", "Easy",
                "Explain the HTTP request-response cycle. What is the difference between GET, POST, PUT, and DELETE methods?",
                json.dumps(["http", "get", "post", "put", "delete", "request headers", "status code", "idempotent"]),
                "Discuss statelessness, request headers, payload safety, and idempotency of PUT vs POST."
            ),

            # Cognizant Questions
            (
                "cognizant", "Web", "Medium",
                "Explain CORS (Cross-Origin Resource Sharing), preflight requests (OPTIONS method), and JWT authentication flow in modern REST APIs.",
                json.dumps(["cors", "preflight", "options", "jwt", "bearer token", "header", "signature", "payload"]),
                "Discuss browser security origin check, preflight headers, and signing tokens with secret keys."
            ),
            (
                "cognizant", "Core CS/OS", "Medium",
                "What are SOLID principles in Object-Oriented Software Design? Explain Single Responsibility and Dependency Inversion with practical code examples.",
                json.dumps(["solid", "single responsibility", "open closed", "liskov", "interface segregation", "dependency inversion", "coupling"]),
                "Explain loose coupling, abstraction over implementation, and single reason for class modification."
            ),
            (
                "cognizant", "DBMS", "Medium",
                "What is ACID property in Database Transactions? How do databases ensure Atomicity and Isolation levels?",
                json.dumps(["atomicity", "consistency", "isolation", "durability", "commit", "rollback", "write-ahead log", "locking"]),
                "Define Atomicity (all or nothing), Consistency, Isolation (dirty reads), and Durability via WAL."
            ),
            (
                "cognizant", "HR/STAR", "Easy",
                "Describe a situation where you had to work under a tight deadline or resolve a conflict within a team project. Use the STAR methodology (Situation, Task, Action, Result).",
                json.dumps(["situation", "task", "action", "result", "collaboration", "deadline", "communication", "impact"]),
                "Structure response cleanly using Situation -> Task -> Action -> Result with quantitative impact."
            ),

            # Infosys Questions
            (
                "infosys", "DSA", "Medium",
                "How would you find the longest substring without repeating characters? Explain the Sliding Window technique with two pointers and a Hash Set/Map.",
                json.dumps(["sliding window", "two pointers", "hash set", "hash map", "longest substring", "o(n)", "space complexity"]),
                "Describe expanding right boundary, tracking duplicate characters, and shrinking left boundary."
            ),
            (
                "infosys", "System Architecture", "Medium",
                "Explain Microservices Architecture vs Monolithic Architecture. What role does an API Gateway, Message Queue (Kafka/RabbitMQ), and Service Discovery play?",
                json.dumps(["microservices", "monolith", "api gateway", "message queue", "kafka", "decoupling", "scalability", "load balancing"]),
                "Discuss independent deployments, asynchronous messaging, service registry, and centralized routing."
            ),
            (
                "infosys", "AI/ML", "Medium",
                "Explain Overfitting vs Underfitting in Machine Learning models. How do Regularization (L1/L2), Cross-Validation, and Dropout layers prevent overfitting?",
                json.dumps(["overfitting", "underfitting", "bias", "variance", "regularization", "l1", "l2", "cross-validation", "dropout"]),
                "Discuss high bias vs high variance, penalty weights in loss functions, and random neuron suppression."
            ),
            (
                "infosys", "HR/STAR", "Easy",
                "Why do you want to join Infosys? How do your technical projects align with our enterprise technology solution tracks?",
                json.dumps(["infosys", "growth", "continuous learning", "projects", "innovation", "teamwork", "values"]),
                "Mention Infosys initiatives, alignment of project tech stack, willingness to upskill, and long-term commitment."
            )
        ]
        cursor.executemany("""
        INSERT INTO questions (company_slug, domain, difficulty, question_text, key_terms, sample_hint)
        VALUES (?, ?, ?, ?, ?, ?)
        """, questions_data)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
