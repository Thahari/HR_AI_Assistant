def extract_skills_from_resume(resume_text, role_skills):
    found_skills = []

    for skill in role_skills:
        if skill.lower() in resume_text.lower():
            found_skills.append(skill)

    return found_skills