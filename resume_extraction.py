import pdfplumber
import re

# Example skill set (you can expand this list)
skill_keywords = ['python', 'java', 'sql', 'machine learning', 'deep learning', 'nlp', 'data analysis', 'aws', 'docker']

def extract_resume_info(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()

    text = text.lower()

    # Extract email
    email = re.search(r'[\w\.-]+@[\w\.-]+', text)
    email = email.group(0) if email else None

    # Extract phone number
    phone = re.search(r'\d{10}', text)
    phone = phone.group(0) if phone else None

    # Extract name (first non-empty line with 2+ words, no @ or digits)
    name = None
    lines = text.splitlines()
    for line in lines:
        line = line.strip()
        if len(line.split()) >= 2 and '@' not in line and not any(char.isdigit() for char in line):
            name = line.title()
            break

    # Extract education
    education = None
    if 'bachelor' in text:
        education = 'Bachelors'
    elif 'master' in text:
        education = 'Masters'
    elif 'phd' in text:
        education = 'PhD'

    # Extract experience (naive approach: years)
    experience = None
    exp_match = re.search(r'(\d+)\s+years?', text)
    if exp_match:
        experience = int(exp_match.group(1))

    # Extract skills
    extracted_skills = []
    for skill in skill_keywords:
        if skill in text:
            extracted_skills.append(skill)

    resume_info = {
        'Name': name,
        'email': email,
        'phone': phone,
        'education': education,
        'experience': experience,
        'skills': extracted_skills  # Now skills are extracted and added here
    }

    return resume_info
