def calculate_compatibility(found_skills, role_skills):
    if not role_skills:
        return 0
    
    score = (len(found_skills) / len(role_skills)) * 100
    return round(score, 2)