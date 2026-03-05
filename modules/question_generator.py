import random
import re

def _extract_project_lines(resume_text):
    lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
    project_lines = []
    keywords = ("project", "developed", "built", "designed", "implemented", "created", "led")

    for line in lines:
        if len(line) < 20:
            continue
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in keywords):
            project_lines.append(line)

    return project_lines[:10]


def _extract_achievement_lines(resume_text):
    lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
    achievements = []
    for line in lines:
        if len(line) < 15:
            continue
        if re.search(r"\d+%|\b\d+\b", line):
            achievements.append(line)
    return achievements[:10]


def _build_fallback_questions(role, found_skills, role_skills):
    focus_skills = found_skills + [skill for skill in role_skills if skill not in found_skills]
    if not focus_skills:
        focus_skills = ["problem solving", "communication", "teamwork", "execution"]

    fallback = []
    for skill in focus_skills:
        fallback.extend(
            [
                f"How do you measure success when working on tasks related to {skill}?",
                f"Describe a decision you made while working with {skill}. What tradeoff did you evaluate?",
                f"What common mistakes happen in {skill}, and how do you avoid them?",
                f"How would you explain a {skill} concept to a non-technical stakeholder?",
                f"Tell me about a time your {skill} approach failed. What did you change after that?",
            ]
        )

    fallback.extend(
        [
            f"What does high performance look like in the {role} role to you?",
            f"How do you stay updated with trends relevant to {role}?",
            f"Tell me about a time you improved a process in a {role}-like task.",
            "How do you break down ambiguous requirements into clear action items?",
            "How do you validate that your final output is reliable before submission?",
            "Describe a situation where you had to learn a new tool very quickly.",
            "What is your approach to documenting your work for handover or review?",
            "How do you handle disagreements about implementation approach?",
            "Describe a time you had limited data/information. How did you proceed?",
            "When under pressure, what steps do you take to maintain quality?",
        ]
    )

    return fallback


def generate_questions(resume_text, role, found_skills, role_skills=None, total_questions=50):
    role_skills = role_skills or []
    found_skills = found_skills or []
    questions = []

    # Base interview questions
    questions.append("Tell me about yourself and your background.")
    questions.append(f"What interests you about the {role} role?")
    questions.append("Can you walk me through one project you are most proud of?")

    # Deep-dive questions for each matched skill from resume
    for skill in found_skills:
        questions.append(f"You mentioned {skill} in your resume. How have you applied it in a real project?")
        questions.append(f"What is the most challenging task you handled using {skill}?")

    # Identify skill gaps and ask readiness questions
    missing_skills = [skill for skill in role_skills if skill not in found_skills]
    for skill in missing_skills:
        questions.append(
            f"This role values {skill}. What is your current proficiency, and how would you ramp up quickly if needed?"
        )

    # Resume line-based follow-up questions
    for line in _extract_project_lines(resume_text):
        questions.append(f"In your resume you wrote: '{line}'. Can you explain your exact contribution here?")

    for line in _extract_achievement_lines(resume_text):
        questions.append(
            f"You highlighted this outcome: '{line}'. What actions did you take to achieve this measurable result?"
        )

    # Behavioral and situational coverage
    questions.extend(
        [
            "Describe a challenging problem you faced and how you solved it.",
            "Tell me about a time you received critical feedback. How did you respond?",
            "How do you prioritize tasks when multiple deadlines overlap?",
            "Describe a time you collaborated with a difficult stakeholder or teammate.",
            "How do you ensure quality and accuracy in your work?",
            "If selected, what would your 30-60-90 day plan look like?",
            "What are your long-term career goals, and how does this role fit them?",
        ]
    )

    # Deduplicate while preserving order
    deduplicated_questions = []
    seen = set()
    for question in questions:
        normalized = question.strip().lower()
        if normalized and normalized not in seen:
            deduplicated_questions.append(question)
            seen.add(normalized)

    fallback_questions = _build_fallback_questions(role, found_skills, role_skills)
    for question in fallback_questions:
        normalized = question.strip().lower()
        if normalized and normalized not in seen:
            deduplicated_questions.append(question)
            seen.add(normalized)

    # Guarantee enough questions even for short resumes
    counter = 1
    while len(deduplicated_questions) < total_questions:
        candidate = f"For the {role} role, share one example of impact from your past work. ({counter})"
        counter += 1
        normalized = candidate.lower()
        if normalized not in seen:
            deduplicated_questions.append(candidate)
            seen.add(normalized)

    random.shuffle(deduplicated_questions)
    return deduplicated_questions[:total_questions]
