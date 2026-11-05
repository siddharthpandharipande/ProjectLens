"""Google Gemini Viva Question Generator (Phase 8).

Integrates with the official Google Gen AI SDK (`google-genai`) to generate
personalized, examiner-style viva questions with detailed suggested answers
based on extracted project evidence.
"""

import json
import logging
import re
import time
from typing import List, Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)

GEMINI_VIVA_SYSTEM_INSTRUCTION = """You are an expert college software engineering viva panel examiner.
Your job is to prepare college students for their final project defense by generating personalized,
rigorous examiner-style questions and comprehensive suggested answers.

You receive factual, PII-free project evidence including detected languages, frameworks,
database files, code complexity metrics, documentation claims, and identified weaknesses.

CORE GUIDELINES:
1. Ground questions in the ACTUAL project evidence (technologies, files, metrics, domain).
2. Avoid generic textbook questions. Every question must feel like an examiner has inspected this specific project.
3. Include challenging examiner rationale: Explain why faculty ask this during oral defense.
4. Key points expected: 2 to 4 concise bullet points of what a good candidate must say.
5. Suggested answer: Provide a technically sound, well-structured answer the student can study.
6. Clearly state the evidence reference (e.g., file name, doc heading, metric, or note on missing evidence).
7. Never invent features, libraries, or capabilities not supported by the project evidence.
8. When an evidence gap is noted (e.g., no unit tests, compressed git history), ask constructive examiner challenge questions probing how the student validated their work.
9. Return ONLY a valid JSON object matching the requested schema. No markdown fences, no explanatory text outside the JSON.
"""


class GeminiVivaGenerator:
    """Invokes Google Gemini API to generate personalized viva questions."""

    @classmethod
    def is_available(cls) -> bool:
        """Check whether Google Gemini is configured and enabled."""
        return settings.gemini_configured

    @classmethod
    def generate_questions(
        cls,
        context: Dict[str, Any],
        mode: str = "complete_viva",
        difficulty: str = "all",
        question_count: int = 10,
    ) -> Optional[List[Dict[str, Any]]]:
        """Generate structured viva questions using Google Gemini API.

        Returns None if Gemini is unavailable, unconfigured, or fails after retries.
        """
        api_key = settings.gemini_api_key
        if not api_key:
            logger.info("Gemini API key is not configured. Skipping Gemini viva generation.")
            return None

        try:
            from google import genai
            from google.genai import types
        except ImportError:
            logger.warning("google-genai package is not installed.")
            return None

        prompt = cls._build_prompt(context, mode, difficulty, question_count)
        model_name = settings.effective_gemini_model

        max_retries = max(1, settings.GEMINI_MAX_RETRIES)
        for attempt in range(max_retries + 1):
            try:
                client = genai.Client(api_key=api_key)
                logger.info(
                    "Generating viva questions via Gemini (model: %s, mode: %s, target: %d, attempt: %d)",
                    model_name,
                    mode,
                    question_count,
                    attempt + 1,
                )

                config = types.GenerateContentConfig(
                    system_instruction=GEMINI_VIVA_SYSTEM_INSTRUCTION,
                    temperature=0.3,
                    response_mime_type="application/json",
                )

                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config,
                )

                raw_text = response.text or ""
                questions = cls._parse_response(raw_text)
                if questions and len(questions) > 0:
                    logger.info("Successfully generated %d viva questions via Gemini.", len(questions))
                    return questions

            except Exception as exc:
                logger.warning(
                    "Gemini viva generation attempt %d failed: %s (%s)",
                    attempt + 1,
                    type(exc).__name__,
                    str(exc),
                )
                if attempt < max_retries:
                    time.sleep(1.5 * (attempt + 1))
                else:
                    logger.error("All Gemini API retries exhausted.")

        return None

    @classmethod
    def regenerate_single_question(
        cls,
        context: Dict[str, Any],
        category: str,
        difficulty: str,
        existing_questions: List[str],
    ) -> Optional[Dict[str, Any]]:
        """Generate a single replacement question for a specific category and difficulty."""
        api_key = settings.gemini_api_key
        if not api_key:
            return None

        try:
            from google import genai
            from google.genai import types
        except ImportError:
            return None

        model_name = settings.effective_gemini_model
        title = (context.get("title") or "").strip() or "Software Project"
        clean_weaknesses = [str(w) for w in context.get("identified_weaknesses", []) if w and str(w).strip()]
        clean_key_files = [str(f) for f in context.get("key_files", []) if f and str(f).strip()]
        clean_frameworks = [str(fw) for fw in context.get("frameworks", []) if fw and str(fw).strip()]
        clean_languages = [str(l) for l in context.get("languages", {}).keys() if l and str(l).strip()]
        inno = context.get("innovation") or {}
        domain = inno.get("domain") or "Software Engineering"

        prompt = (
            f"Project: {title}\n"
            f"Domain: {domain}\n"
            f"Languages: {clean_languages or ['None detected']}\n"
            f"Frameworks: {clean_frameworks or ['None detected']}\n"
            f"Key Files: {clean_key_files or ['None recorded']}\n"
            f"Weaknesses: {clean_weaknesses or ['None flagged']}\n\n"
            f"Task: Generate ONE viva question specifically for:\n"
            f"Category: {category}\n"
            f"Difficulty: {difficulty}\n"
            f"Do NOT duplicate these existing questions: {existing_questions[:5]}\n\n"
            "Return JSON matching this exact structure:\n"
            "{\n"
            '  "question": "...",\n'
            f'  "category": "{category}",\n'
            f'  "difficulty": "{difficulty}",\n'
            '  "examiner_rationale": "...",\n'
            '  "key_points": ["...", "..."],\n'
            '  "suggested_answer": "...",\n'
            '  "evidence_reference": "..."\n'
            "}"
        )

        try:
            client = genai.Client(api_key=api_key)
            config = types.GenerateContentConfig(
                system_instruction=GEMINI_VIVA_SYSTEM_INSTRUCTION,
                temperature=0.4,
                response_mime_type="application/json",
            )
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,
            )
            data = cls._parse_single_question(response.text or "")
            if data and data.get("question"):
                data["category"] = category
                data["difficulty"] = difficulty
                return data
        except Exception as exc:
            logger.warning("Single question Gemini regeneration failed: %s", exc)

        return None

    @classmethod
    def _build_prompt(
        cls,
        context: Dict[str, Any],
        mode: str,
        difficulty: str,
        question_count: int,
    ) -> str:
        """Construct a compact, evidence-rich prompt for Gemini with full null safety."""
        title = (context.get("title") or "").strip() or "Software Engineering Project"
        languages = [str(l) for l in context.get("languages", {}).keys() if l and str(l).strip()]
        frameworks = [str(f) for f in context.get("frameworks", []) if f and str(f).strip()]
        key_files = [str(f) for f in context.get("key_files", []) if f and str(f).strip()]
        quality = context.get("code_quality")
        docs = context.get("documentation")
        git = context.get("git_history")
        inno = context.get("innovation")
        weaknesses = [str(w) for w in context.get("identified_weaknesses", []) if w and str(w).strip()]

        mode_instructions = {
            "quick_prep": (
                "Mode: Quick Preparation. Focus on core high-priority viva questions: "
                "Project Fundamentals, Technical Architecture, Technology Stack, and main implementation hurdles."
            ),
            "complete_viva": (
                "Mode: Complete Viva. Cover all 9 categories with balanced difficulty across beginner, "
                "intermediate, and advanced levels."
            ),
            "technical_deep_dive": (
                "Mode: Technical Deep Dive. Focus deeply on source code implementation, data structures, "
                "APIs, database models, complexity, and specific files."
            ),
            "examiner_challenge": (
                "Mode: Examiner Challenge. Ask tough, provocative questions about architectural trade-offs, "
                "scalability limits, missing automated tests, single-day commits, security vulnerabilities, "
                "and design limitations."
            ),
        }.get(mode, "Mode: Complete Viva.")

        difficulty_constraint = (
            f"Target difficulty: {difficulty} only."
            if difficulty in ("beginner", "intermediate", "advanced")
            else "Distribute difficulties realistically across beginner, intermediate, and advanced."
        )

        prompt = f"""EVALUATION EVIDENCE FOR PROJECT DEFENSE:
- Project Title: {title}
- Detected Languages: {languages or 'None identified (No recognized code files)'}
- Detected Frameworks / Libraries: {frameworks or 'None explicitly identified'}
- Representative Implementation Files: {key_files or 'None recorded'}
- Has Database Components: {bool(context.get('has_database_files', False))}
- Has Container / Docker: {bool(context.get('has_docker', False))}
- Has Automated Tests: {bool(context.get('has_tests', False))}
"""
        if quality:
            loc = quality.get("total_loc", 0)
            avg_c = quality.get("avg_complexity", 0.0)
            max_c = quality.get("max_complexity", 0)
            smells = [str(s) for s in quality.get("smells_detected", []) if s and str(s).strip()]
            prompt += f"- Code Quality: LOC={loc}, Avg Complexity={avg_c:.1f}, Max Complexity={max_c}\n"
            if smells:
                prompt += f"  Code Smells Detected: {'; '.join(smells[:3])}\n"
        else:
            prompt += "- Code Quality: Not available (No source code analyzed)\n"

        if docs:
            words = docs.get("total_words", 0)
            sec_p = [str(s) for s in docs.get("sections_present", []) if s and str(s).strip()]
            sec_m = [str(s) for s in docs.get("sections_missing", []) if s and str(s).strip()]
            prompt += f"- Documentation: Word Count={words}, Sections Present={sec_p or 'None verified'}, Sections Missing={sec_m or 'None'}\n"
        else:
            prompt += "- Documentation: Not available (No documentation files extracted)\n"

        if git:
            commits = git.get("total_commits", 0)
            authors = git.get("total_authors", 0)
            anom = git.get("has_velocity_anomaly", False)
            prompt += f"- Git History: Commits={commits}, Authors={authors}, Velocity Anomaly={anom}\n"
        else:
            prompt += "- Git History: Not available (No Git repository metadata detected)\n"

        if inno:
            dom = inno.get("domain") or "Software Engineering"
            prob = inno.get("problem_statement") or "Not identified from available documents"
            sol = inno.get("proposed_solution") or "Not identified from available documents"
            prompt += f"- Domain & Problem: Domain='{dom}', Problem='{prob}', Solution='{sol}'\n"
            if inno.get("abstract"):
                prompt += f"- Abstract: {inno.get('abstract')}\n"
            if inno.get("description"):
                prompt += f"- Description: {inno.get('description')}\n"
            features = [str(f) for f in inno.get("distinctive_features", []) if f and str(f).strip()]
            if features:
                prompt += f"- Claimed Distinctive Features: {', '.join(features[:4])}\n"
        else:
            prompt += "- Domain & Innovation: Standard Software Engineering Project (No innovation profile extracted)\n"

        if weaknesses:
            prompt += f"- Identified Project Weaknesses / Viva Blind Spots: {'; '.join(weaknesses)}\n"
        else:
            prompt += "- Identified Project Weaknesses: No critical weaknesses flagged\n"

        prompt += f"""
TASK:
Generate exactly {question_count} personalized viva questions with suggested answers.
{mode_instructions}
{difficulty_constraint}

Categories to draw from:
1. Project Fundamentals
2. Technical Architecture
3. Technology Stack
4. Implementation and Coding
5. Innovation and Uniqueness
6. Testing and Validation
7. Critical Thinking and Problem Solving
8. Project-Specific Technical Deep Dive
9. Future Scope and Improvements

OUTPUT FORMAT:
Return a JSON object with a 'questions' array:
{{
  "questions": [
    {{
      "category": "Technology Stack",
      "difficulty": "intermediate",
      "question": "Why did you choose [Framework] over alternative architectures for this project?",
      "examiner_rationale": "Examiners want to verify whether technology choices were deliberate or arbitrary.",
      "key_points": [
        "Trade-offs compared to alternatives",
        "Performance and developer ecosystem fit",
        "How it addressed project requirements"
      ],
      "suggested_answer": "In our project, we selected [Framework] because...",
      "evidence_reference": "Framework Evidence / package.json"
    }}
  ]
}}
"""
        return prompt

    @classmethod
    def _parse_response(cls, raw_text: str) -> List[Dict[str, Any]]:
        """Safely extract and parse JSON array of questions from response text."""
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned.strip(), flags=re.MULTILINE)

        candidates: List[Any] = []
        try:
            data = json.loads(cleaned)
            if isinstance(data, dict) and "questions" in data and isinstance(data["questions"], list):
                candidates = data["questions"]
            elif isinstance(data, list):
                candidates = data
        except json.JSONDecodeError:
            # Fallback regex extraction of JSON object
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    obj = json.loads(match.group(0))
                    if isinstance(obj, dict) and "questions" in obj and isinstance(obj["questions"], list):
                        candidates = obj["questions"]
                except Exception:
                    pass

        # Filter out invalid or non-dict items
        valid_questions: List[Dict[str, Any]] = []
        for q in candidates:
            if isinstance(q, dict) and q.get("question") and isinstance(q.get("question"), str):
                valid_questions.append(q)

        return valid_questions

    @classmethod
    def _parse_single_question(cls, raw_text: str) -> Optional[Dict[str, Any]]:
        """Parse a single question JSON object."""
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned.strip(), flags=re.MULTILINE)
        try:
            data = json.loads(cleaned)
            if isinstance(data, dict) and data.get("question") and isinstance(data.get("question"), str):
                return data
        except Exception:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    obj = json.loads(match.group(0))
                    if isinstance(obj, dict) and obj.get("question") and isinstance(obj.get("question"), str):
                        return obj
                except Exception:
                    pass
        return None

