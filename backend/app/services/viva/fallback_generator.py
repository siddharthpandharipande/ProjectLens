"""Deterministic Fallback Viva Question Generator (Phase 8).

Generates grounded, personalized viva questions and structured answers using
factual project analysis signals without requiring upstream LLM API access.
Guarantees 100% offline resilience and zero crashes when Gemini is unavailable.
"""

from typing import List, Dict, Any, Optional
import uuid


def generate_qid() -> str:
    return f"vq_{uuid.uuid4().hex[:12]}"


class FallbackVivaGenerator:
    """Deterministic rule-based generator for personalized viva questions."""

    @classmethod
    def generate_questions(
        cls,
        context: Dict[str, Any],
        mode: str = "complete_viva",
        difficulty: str = "all",
        question_count: int = 10,
    ) -> List[Dict[str, Any]]:
        """Generate tailored viva questions from deterministic project evidence."""
        title = (context.get("title") or "").strip() or "this software project"
        languages = [str(l) for l in context.get("languages", {}).keys() if l and str(l).strip()]
        primary_lang = languages[0] if languages else "the selected programming language"
        secondary_lang = languages[1] if len(languages) > 1 else None
        frameworks = [str(f) for f in context.get("frameworks", []) if f and str(f).strip()]
        primary_fw = frameworks[0] if frameworks else "the chosen framework"
        key_files = [str(f) for f in context.get("key_files", []) if f and str(f).strip()]
        key_file_1 = key_files[0] if len(key_files) > 0 else "main application entrypoint"
        key_file_2 = key_files[1] if len(key_files) > 1 else "core business logic module"

        quality = context.get("code_quality") or {}
        try:
            avg_complexity = float(quality.get("avg_complexity", 1.0) or 1.0)
        except (ValueError, TypeError):
            avg_complexity = 1.0

        has_tests = bool(context.get("has_tests", False))
        has_docker = bool(context.get("has_docker", False))
        has_db = bool(context.get("has_database_files", False))

        docs = context.get("documentation") or {}
        missing_sections = [
            str(s) for s in docs.get("sections_missing", [])
            if s and str(s).strip()
        ]
        inno = context.get("innovation") or {}
        domain = (inno.get("domain") or "").strip() or "Software Engineering"
        problem = inno.get("problem_statement")
        abstract = inno.get("abstract")
        description = inno.get("description")

        pool: List[Dict[str, Any]] = []

        # ── 1. Project Fundamentals ──
        problem_desc = (
            problem if problem and problem != "Not identified from the available project documents."
            else (abstract or description or "the challenge of automating workflows and streamlining data processing")
        )
        pool.append({
            "category": "Project Fundamentals",
            "difficulty": "beginner",
            "question": f"Can you summarize the primary problem '{title}' solves and identify its intended end-users?",
            "examiner_rationale": "Examiners start with fundamentals to confirm the student understands user requirements and project scope.",
            "key_points": [
                "Clear problem definition and target domain",
                "Core user persona and their primary workflow",
                "Why existing generic solutions were insufficient"
            ],
            "suggested_answer": (
                f"The project '{title}' operates in the {domain} domain. It addresses "
                f"{problem_desc}. "
                f"The system provides an integrated software platform that minimizes manual overhead for users."
            ),
            "evidence_reference": "Project Documentation / Overview",
            "source": "deterministic_fallback",
        })

        pool.append({
            "category": "Project Fundamentals",
            "difficulty": "intermediate",
            "question": "What functional and non-functional requirements governed the system boundaries of this project?",
            "examiner_rationale": "Validates whether the student designed the system around formal engineering requirements or informal ad-hoc code.",
            "key_points": [
                "Primary functional capabilities (CRUD, calculations, reporting)",
                "Non-functional constraints: response latency, data security, modularity",
                "How non-functional requirements influenced architecture"
            ],
            "suggested_answer": (
                f"Functional requirements included primary application workflows, while non-functional requirements focused on "
                f"maintainability (keeping average cyclomatic complexity near {avg_complexity:.1f}), fast response latency, "
                f"and modular code separation across components."
            ),
            "evidence_reference": "Software Requirements Specification",
            "source": "deterministic_fallback",
        })

        # ── 2. Technical Architecture ──
        pool.append({
            "category": "Technical Architecture",
            "difficulty": "intermediate",
            "question": f"How is the architectural separation of concerns structured across '{title}'?",
            "examiner_rationale": "Tests whether the candidate understands layered architecture, MVC, or service-repository patterns.",
            "key_points": [
                "Separation of presentation, business logic, and persistence",
                "How client requests navigate the stack to source components",
                "Coupling and cohesion between modules"
            ],
            "suggested_answer": (
                f"The application enforces separation of concerns by isolating data models, route handlers, and service logic. "
                f"For example, components like '{key_file_1}' coordinate inputs and delegate heavy processing to underlying modules, "
                f"ensuring loose coupling and testability."
            ),
            "evidence_reference": f"Source File: {key_file_1}",
            "source": "deterministic_fallback",
        })

        pool.append({
            "category": "Technical Architecture",
            "difficulty": "advanced",
            "question": f"How does '{title}' handle cross-cutting concerns such as error propagation, input validation, and configuration management?",
            "examiner_rationale": "Probes enterprise software design maturity beyond basic happy-path implementation.",
            "key_points": [
                "Centralized exception handling vs local try-catch blocks",
                "Schema-based input validation at boundaries",
                "Environment variable encapsulation"
            ],
            "suggested_answer": (
                f"Cross-cutting concerns are managed through centralized configurations and validation schemas. Inputs are validated "
                f"before entering business logic, and unexpected failures are intercepted by structured error handlers rather than "
                f"crashing the process or exposing raw stack traces."
            ),
            "evidence_reference": "Application Configuration & Middleware",
            "source": "deterministic_fallback",
        })

        # ── 3. Technology Stack ──
        pool.append({
            "category": "Technology Stack",
            "difficulty": "beginner",
            "question": f"Why did your team select {primary_lang}" + (f" and {primary_fw}" if frameworks else "") + f" for building '{title}'?",
            "examiner_rationale": "Faculty evaluate whether tech stack choices were justified by technical trade-offs or personal familiarity.",
            "key_points": [
                f"Technical strengths of {primary_lang} for this project",
                "Ecosystem libraries and package support",
                "Trade-offs evaluated against alternative stacks"
            ],
            "suggested_answer": (
                f"{primary_lang} was chosen due to its rich ecosystem, strong type/library tooling, and rapid prototyping capabilities. "
                + (f"Paired with {primary_fw}, it provided built-in routing, high throughput, and clean modular development." if frameworks else "")
            ),
            "evidence_reference": f"Detected Language: {primary_lang}",
            "source": "deterministic_fallback",
        })

        if secondary_lang:
            pool.append({
                "category": "Technology Stack",
                "difficulty": "intermediate",
                "question": f"How do the {primary_lang} and {secondary_lang} layers communicate in this system?",
                "examiner_rationale": "Examines multi-tier data serialization and protocol interoperability.",
                "key_points": [
                    "Serialization format (JSON, REST, WebSockets)",
                    "Protocol consistency and CORS / networking handling",
                    "Error status code propagation across layers"
                ],
                "suggested_answer": (
                    f"Communication between {primary_lang} and {secondary_lang} components occurs via structured JSON APIs over HTTP. "
                    f"Payloads adhere to explicit schemas to prevent runtime schema drift."
                ),
                "evidence_reference": f"Detected Languages: {primary_lang}, {secondary_lang}",
                "source": "deterministic_fallback",
            })

        # ── 4. Implementation and Coding ──
        pool.append({
            "category": "Implementation and Coding",
            "difficulty": "intermediate",
            "question": f"In '{key_file_1}', how did you handle state management, edge cases, and asynchronous operations?",
            "examiner_rationale": "Checks whether the student actually wrote and understands the code in key project files.",
            "key_points": [
                "Walkthrough of execution path in the file",
                "Boundary conditions and null checks",
                "Resource cleanup (file handles, database connections)"
            ],
            "suggested_answer": (
                f"In '{key_file_1}', operations validate prerequisites first, execute transactions within scoped contexts, "
                f"and ensure resources are deterministically released upon completion or failure."
            ),
            "evidence_reference": f"Source File: {key_file_1}",
            "source": "deterministic_fallback",
        })

        pool.append({
            "category": "Implementation and Coding",
            "difficulty": "advanced",
            "question": f"What algorithms or data structures in '{key_file_2}' presented performance bottlenecks during development?",
            "examiner_rationale": "Tests algorithmic analysis (Big-O time/space) and profiling awareness.",
            "key_points": [
                "Time complexity of primary search/lookup operations",
                "In-memory data structures chosen (hash maps, lists, trees)",
                "Techniques applied to avoid nested loop overhead"
            ],
            "suggested_answer": (
                f"In '{key_file_2}', operations were optimized by replacing O(n^2) linear traversals with O(1) dictionary lookups, "
                f"preventing latency spikes when processing larger input payloads."
            ),
            "evidence_reference": f"Source File: {key_file_2}",
            "source": "deterministic_fallback",
        })

        # ── 5. Innovation and Uniqueness ──
        pool.append({
            "category": "Innovation and Uniqueness",
            "difficulty": "intermediate",
            "question": f"What makes '{title}' technically distinct from standard tutorials or open-source boilerplates in the {domain} domain?",
            "examiner_rationale": "Distinguishes original student contribution from cloned template projects.",
            "key_points": [
                "Unique workflow integration or domain customization",
                "Features developed beyond boilerplate templates",
                "Specific algorithmic or UI/UX improvements"
            ],
            "suggested_answer": (
                f"While '{title}' leverages standard frameworks, its distinctiveness lies in its customized data models, "
                f"tailored domain rules for {domain}, and integrated verification pipeline rather than just generic template CRUD."
            ),
            "evidence_reference": "Innovation Profile & Cohort Analysis",
            "source": "deterministic_fallback",
        })

        # ── 6. Testing and Validation ──
        if has_tests:
            pool.append({
                "category": "Testing and Validation",
                "difficulty": "intermediate",
                "question": "How did you design your automated test suite, and what code coverage levels did you achieve?",
                "examiner_rationale": "Assesses testing methodology, unit vs integration test balance, and edge case coverage.",
                "key_points": [
                    "Test structure (unit tests, integration tests)",
                    "Mocking external dependencies or databases",
                    "Critical boundary conditions tested"
                ],
                "suggested_answer": (
                    "The test suite covers core business logic through isolated unit tests with mocked boundaries, "
                    "ensuring regression stability before code integration."
                ),
                "evidence_reference": "Detected Test Files in Repository",
                "source": "deterministic_fallback",
            })
        else:
            pool.append({
                "category": "Testing and Validation",
                "difficulty": "advanced",
                "question": "No automated test suite was detected in the project archive. How did you verify system correctness and handle edge cases?",
                "examiner_rationale": "Challenging question addressing a concrete implementation omission.",
                "key_points": [
                    "Honest acknowledgment of absent automated test suite",
                    "Manual testing methodology: postman collections, unit assertions, sanity checks",
                    "How an automated test framework would be introduced"
                ],
                "suggested_answer": (
                    "We validated functionality through manual end-to-end integration testing and boundary checks. In production, "
                    "we would introduce an automated testing framework (e.g. Pytest or Jest) to automate regression suites and verify coverage."
                ),
                "evidence_reference": "Weakness Signal: Absent Automated Test Suite",
                "source": "deterministic_fallback",
            })

        # ── 7. Critical Thinking and Problem Solving ──
        pool.append({
            "category": "Critical Thinking and Problem Solving",
            "difficulty": "advanced",
            "question": "If user traffic or database size increased by 100x tomorrow, which component of your architecture would fail first?",
            "examiner_rationale": "Tests whether the student can analyze architectural limits and scalability bottlenecks critically.",
            "key_points": [
                "Identification of the primary bottleneck (database queries, unindexed lookups, memory usage)",
                "Remediation strategy (caching, connection pooling, pagination, read replicas)",
                "Stateless design vs stateful bottlenecks"
            ],
            "suggested_answer": (
                "Under 100x load, synchronous database queries and unindexed lookups would create I/O bottlenecks. "
                "To mitigate this, we would implement cursor pagination, database indexes on foreign keys, a Redis caching layer for hot data, "
                "and horizontal worker scaling behind a reverse proxy."
            ),
            "evidence_reference": "System Scalability & Performance Analysis",
            "source": "deterministic_fallback",
        })

        pool.append({
            "category": "Critical Thinking and Problem Solving",
            "difficulty": "intermediate",
            "question": "Describe the most difficult software bug or integration roadblock your team encountered, and how you resolved it.",
            "examiner_rationale": "Assesses real debugging capability and genuine hands-on engineering involvement.",
            "key_points": [
                "Specific technical description of the problem",
                "Diagnostic tools or logging used to trace root cause",
                "The engineering solution implemented"
            ],
            "suggested_answer": (
                "A key challenge was asynchronous state race conditions and data serialization discrepancies between layers. "
                "We resolved this by inspecting network traces, enforcing strict Pydantic/TypeScript validation contracts, "
                "and implementing deterministic transactional rollback on failure."
            ),
            "evidence_reference": "Development History & Code Evolution",
            "source": "deterministic_fallback",
        })

        # ── 8. Project-Specific Technical Deep Dive ──
        if has_db:
            pool.append({
                "category": "Project-Specific Technical Deep Dive",
                "difficulty": "advanced",
                "question": "How did you design your database schema, ensure referential integrity, and prevent N+1 query performance problems?",
                "examiner_rationale": "Examiners drill down into relational modeling, foreign keys, and query efficiency.",
                "key_points": [
                    "Foreign key cascades and index placement",
                    "ACID transaction boundaries",
                    "Eager loading / joins vs lazy loading"
                ],
                "suggested_answer": (
                    "We normalized the schema to 3NF, indexed foreign key columns, and used scoped transactions with eager joins "
                    "where relationships are traversed to prevent N+1 query overhead."
                ),
                "evidence_reference": "Database Schema & Entity Models",
                "source": "deterministic_fallback",
            })
        else:
            pool.append({
                "category": "Project-Specific Technical Deep Dive",
                "difficulty": "intermediate",
                "question": f"Average cyclomatic complexity is calculated at {avg_complexity:.1f}. How did you ensure maintainability across functions?",
                "examiner_rationale": "Static code analysis verification of code quality.",
                "key_points": [
                    "Keeping functions focused on a single responsibility",
                    "Avoiding deep nesting (>3 levels)",
                    "Extracting helper routines for reusable logic"
                ],
                "suggested_answer": (
                    f"We decomposed large monolithic routines into single-purpose modular functions. This kept average cyclomatic "
                    f"complexity at a healthy {avg_complexity:.1f}, making the code readable and easy to audit."
                ),
                "evidence_reference": f"Code Quality AST Metrics (Avg Complexity: {avg_complexity:.1f})",
                "source": "deterministic_fallback",
            })

        # ── 9. Future Scope and Improvements ──
        pool.append({
            "category": "Future Scope and Improvements",
            "difficulty": "beginner",
            "question": f"If you had another two months to develop '{title}', what two major technical capabilities would you add next?",
            "examiner_rationale": "Checks product roadmap vision and technical ambition.",
            "key_points": [
                "Realistic high-value technical additions",
                "How they integrate with existing architecture",
                "Security or deployment enhancements (e.g. CI/CD, OAuth2)"
            ],
            "suggested_answer": (
                f"Next development steps would include implementing full CI/CD deployment pipelines"
                + (", Docker containerization" if not has_docker else "")
                + ", role-based access control, and automated monitoring with real-time alerting."
            ),
            "evidence_reference": "Project Limitations & Future Scope",
            "source": "deterministic_fallback",
        })

        if missing_sections:
            pool.append({
                "category": "Future Scope and Improvements",
                "difficulty": "intermediate",
                "question": f"Your project documentation omits '{missing_sections[0]}'. How would you document this aspect for production handoff?",
                "examiner_rationale": "Challenges the student on software documentation standards.",
                "key_points": [
                    f"Importance of {missing_sections[0]} in software engineering",
                    "What technical diagrams and specifications would be included",
                    "How clear docs assist onboarding developers"
                ],
                "suggested_answer": (
                    f"For production handoff, we would author a dedicated '{missing_sections[0]}' specification, including "
                    f"system topology diagrams, environment variable definitions, and step-by-step deployment runbooks."
                ),
                "evidence_reference": f"Documentation Gap: Missing {missing_sections[0]}",
                "source": "deterministic_fallback",
            })

        # Filter by mode
        if mode == "quick_prep":
            priority_cats = [
                "Project Fundamentals",
                "Technical Architecture",
                "Technology Stack",
                "Implementation and Coding",
                "Critical Thinking and Problem Solving",
            ]
            filtered = [q for q in pool if q["category"] in priority_cats]
        elif mode == "technical_deep_dive":
            deep_cats = [
                "Technical Architecture",
                "Technology Stack",
                "Implementation and Coding",
                "Project-Specific Technical Deep Dive",
                "Testing and Validation",
            ]
            filtered = [q for q in pool if q["category"] in deep_cats]
        elif mode == "examiner_challenge":
            challenge_diffs = ["intermediate", "advanced"]
            filtered = [q for q in pool if q["difficulty"] in challenge_diffs]
        else:  # complete_viva
            filtered = pool

        # Filter by difficulty if user requested specific
        if difficulty in ("beginner", "intermediate", "advanced"):
            diff_filtered = [q for q in filtered if q["difficulty"] == difficulty]
            if len(diff_filtered) >= 3:
                filtered = diff_filtered

        # Assign unique IDs and ensure question_count
        result = []
        for q in filtered[:question_count]:
            item = dict(q)
            item["id"] = generate_qid()
            result.append(item)

        # If filtered list had fewer than question_count, fill from pool
        if len(result) < question_count:
            existing_qs = {r["question"] for r in result}
            for q in pool:
                if q["question"] not in existing_qs:
                    item = dict(q)
                    item["id"] = generate_qid()
                    result.append(item)
                    if len(result) >= question_count:
                        break

        return result

