"""
Enhanced Resume Extraction Module for Berojgar

This module provides advanced resume parsing capabilities using NLP techniques
to extract structured information from resumes for better ATS compatibility checking.
"""

import os
import re
import logging
import pdfplumber
import spacy
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from PyPDF2 import PdfReader
import pandas as pd
from fuzzywuzzy import fuzz
from collections import Counter

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

# Initialize spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # If model not found, download it
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("resume_extraction.log"), logging.StreamHandler()]
)
logger = logging.getLogger("enhanced_resume_extraction")

# Common skills database
COMMON_SKILLS = [
    # Programming languages
    "Python", "JavaScript", "Java", "C++", "C#", "Ruby", "PHP", "Swift", "Kotlin", "Go",
    "TypeScript", "Rust", "Scala", "Perl", "R", "MATLAB", "Objective-C", "Dart", "Groovy",
    
    # Web technologies
    "HTML", "CSS", "React", "Angular", "Vue.js", "Node.js", "Express", "Django", "Flask",
    "Spring", "ASP.NET", "Laravel", "Ruby on Rails", "jQuery", "Bootstrap", "Tailwind",
    
    # Data science & ML
    "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Keras", "scikit-learn",
    "Data Science", "Data Analysis", "NLP", "Computer Vision", "AI", "Artificial Intelligence",
    "Statistics", "Big Data", "Data Mining", "Data Visualization", "Tableau", "Power BI",
    
    # Databases
    "SQL", "MySQL", "PostgreSQL", "MongoDB", "Oracle", "SQLite", "NoSQL", "Redis",
    "Elasticsearch", "Cassandra", "DynamoDB", "Firebase", "GraphQL",
    
    # DevOps & Cloud
    "AWS", "Azure", "GCP", "Google Cloud", "Docker", "Kubernetes", "Jenkins", "CI/CD",
    "Git", "GitHub", "GitLab", "Terraform", "Ansible", "Puppet", "Chef", "Prometheus",
    "Grafana", "ELK Stack", "Serverless", "Microservices",
    
    # Mobile
    "Android", "iOS", "React Native", "Flutter", "Xamarin", "Cordova", "Ionic",
    
    # Other technical skills
    "Agile", "Scrum", "Jira", "REST API", "GraphQL", "WebSockets", "Testing", "QA",
    "Selenium", "JUnit", "TestNG", "Cypress", "Jest", "Mocha", "Chai", "Security",
    "Blockchain", "Cryptography", "UI/UX", "Design Patterns", "OOP", "Functional Programming",
    
    # Soft skills
    "Communication", "Teamwork", "Problem Solving", "Leadership", "Time Management",
    "Critical Thinking", "Creativity", "Adaptability", "Project Management"
]

# Common education degrees
EDUCATION_DEGREES = [
    "Bachelor", "BS", "B.S.", "B.A.", "BA", "BSc", "B.Sc.",
    "Master", "MS", "M.S.", "M.A.", "MA", "MSc", "M.Sc.", "MBA",
    "PhD", "Ph.D.", "Doctorate", "MD", "Doctor",
    "Associate", "AS", "A.S.", "A.A.", "AA",
    "Certificate", "Certification", "Diploma"
]

# Common job titles
COMMON_JOB_TITLES = [
    "Software Engineer", "Software Developer", "Web Developer", "Frontend Developer", 
    "Backend Developer", "Full Stack Developer", "Data Scientist", "Data Analyst",
    "Machine Learning Engineer", "DevOps Engineer", "Cloud Engineer", "System Administrator",
    "Network Engineer", "Database Administrator", "Product Manager", "Project Manager",
    "UX Designer", "UI Designer", "QA Engineer", "Test Engineer", "Security Engineer",
    "Mobile Developer", "Android Developer", "iOS Developer", "Game Developer",
    "Blockchain Developer", "AI Engineer", "Research Scientist", "Technical Writer"
]

# Main extraction function
def extract_resume_info(file_path):
    """
    Extract detailed information from resume using NLP techniques
    
    Args:
        file_path (str): Path to the resume file (PDF, DOC, DOCX)
        
    Returns:
        dict: Structured resume information
    """
    try:
        # Check file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Extract text based on file type
        if file_ext == '.pdf':
            text = extract_text_from_pdf(file_path)
        elif file_ext in ['.doc', '.docx']:
            # For simplicity, we'll use a placeholder for DOC/DOCX extraction
            # In a real implementation, you would use a library like python-docx
            text = "DOC/DOCX extraction not implemented"
            logger.warning("DOC/DOCX extraction not fully implemented")
        else:
            logger.error(f"Unsupported file format: {file_ext}")
            return {"error": f"Unsupported file format: {file_ext}"}
        
        # Process the extracted text
        if not text:
            logger.error("No text extracted from resume")
            return {"error": "No text extracted from resume"}
        
        # Parse the text with spaCy for NER
        doc = nlp(text)
        
        # Extract structured information
        resume_data = {
            "raw_text": text,
            "word_count": len(text.split()),
            "has_bullet_points": '•' in text or '*' in text or '-' in text,
            "has_tables": detect_tables(text),
            "has_images": False,  # Placeholder, would require more complex analysis
            "has_dates": bool(re.search(r'\b(19|20)\d{2}\b', text)),  # Simple date detection
            "sections": identify_resume_sections(text)
        }
        
        # Extract specific information
        resume_data["name"] = extract_name(doc, text)
        resume_data["email"] = extract_email(text)
        resume_data["phone"] = extract_phone(text)
        resume_data["skills"] = extract_skills(text)
        resume_data["education"] = extract_education(text)
        resume_data["experience"] = extract_experience(text)
        resume_data["experience_text"] = extract_experience_text(text)
        resume_data["education_text"] = extract_education_text(text)
        resume_data["summary"] = extract_summary(text)
        resume_data["job_role"] = extract_job_role(text)
        
        # Calculate ATS-specific metrics
        resume_data["keyword_density"] = calculate_keyword_density(text)
        resume_data["format_score"] = calculate_format_score(resume_data)
        resume_data["content_score"] = calculate_content_score(resume_data)
        
        logger.info(f"Successfully extracted resume information from {file_path}")
        return resume_data
        
    except Exception as e:
        logger.error(f"Error extracting resume information: {str(e)}")
        return {"error": f"Error extracting resume information: {str(e)}"}

# Helper functions for text extraction
def extract_text_from_pdf(file_path):
    """
    Extract text from PDF file using multiple methods for better results
    
    Args:
        file_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text
    """
    text = ""
    
    # Try pdfplumber first (better for maintaining layout)
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
                text += "\n\n"
    except Exception as e:
        logger.warning(f"pdfplumber extraction failed: {str(e)}")
        
    # If pdfplumber didn't work well, try PyPDF2 as backup
    if not text.strip():
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    text += pdf_reader.pages[page_num].extract_text() or ""
                    text += "\n\n"
        except Exception as e:
            logger.warning(f"PyPDF2 extraction failed: {str(e)}")
    
    return text

# Section identification
def identify_resume_sections(text):
    """
    Identify common resume sections
    
    Args:
        text (str): Resume text
        
    Returns:
        dict: Detected sections and their presence
    """
    sections = {
        "summary": False,
        "experience": False,
        "education": False,
        "skills": False,
        "projects": False,
        "certifications": False,
        "languages": False,
        "interests": False
    }
    
    # Check for common section headers
    summary_patterns = [r'\bSUMMARY\b', r'\bPROFILE\b', r'\bOBJECTIVE\b', r'\bABOUT ME\b']
    experience_patterns = [r'\bEXPERIENCE\b', r'\bWORK EXPERIENCE\b', r'\bEMPLOYMENT\b', r'\bWORK HISTORY\b']
    education_patterns = [r'\bEDUCATION\b', r'\bACADEMIC\b', r'\bQUALIFICATIONS\b', r'\bDEGREES\b']
    skills_patterns = [r'\bSKILLS\b', r'\bCOMPETENCIES\b', r'\bABILITIES\b', r'\bCAPABILITIES\b']
    projects_patterns = [r'\bPROJECTS\b', r'\bPORTFOLIO\b', r'\bWORKS\b']
    certifications_patterns = [r'\bCERTIFICATIONS\b', r'\bCERTIFICATES\b', r'\bLICENSES\b']
    languages_patterns = [r'\bLANGUAGES\b', r'\bLINGUISTIC SKILLS\b']
    interests_patterns = [r'\bINTERESTS\b', r'\bHOBBIES\b', r'\bACTIVITIES\b']
    
    # Check each pattern
    for pattern in summary_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            sections["summary"] = True
            break
            
    for pattern in experience_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            sections["experience"] = True
            break
            
    for pattern in education_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            sections["education"] = True
            break
            
    for pattern in skills_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            sections["skills"] = True
            break
            
    for pattern in projects_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            sections["projects"] = True
            break
            
    for pattern in certifications_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            sections["certifications"] = True
            break
            
    for pattern in languages_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            sections["languages"] = True
            break
            
    for pattern in interests_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            sections["interests"] = True
            break
            
    return sections

# Information extraction functions
def extract_name(doc, text):
    """
    Extract candidate name using NER
    
    Args:
        doc (spacy.Doc): Processed spaCy document
        text (str): Raw resume text
        
    Returns:
        str: Extracted name or 'Not found'
    """
    # Try to find name using spaCy's NER
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            # Check if it's likely a name (near the beginning of the resume)
            if ent.start_char < len(text) / 4:  # In first quarter of text
                return ent.text
    
    # Fallback: Look for a name-like pattern at the beginning
    lines = text.split('\n')
    for line in lines[:10]:  # Check first 10 lines
        line = line.strip()
        if line and len(line.split()) <= 4 and len(line.split()) >= 2:
            # Check if it doesn't look like a section header or contact info
            if not any(word.lower() in line.lower() for word in ["resume", "cv", "curriculum", "vitae", "email", "phone", "address", "linkedin"]):
                return line
    
    return "Not found"

def extract_email(text):
    """
    Extract email address from text
    
    Args:
        text (str): Resume text
        
    Returns:
        str: Extracted email or 'Not found'
    """
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(email_pattern, text)
    return match.group(0) if match else "Not found"

def extract_phone(text):
    """
    Extract phone number from text
    
    Args:
        text (str): Resume text
        
    Returns:
        str: Extracted phone number or 'Not found'
    """
    # Various phone number patterns
    patterns = [
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # 123-456-7890 or 123.456.7890 or 1234567890
        r'\b\(\d{3}\)[-. ]?\d{3}[-.]?\d{4}\b',  # (123) 456-7890 or (123)456-7890
        r'\b\+\d{1,3}[-. ]?\d{3}[-. ]?\d{3}[-. ]?\d{4}\b'  # +1 123-456-7890 or +91 123.456.7890
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    
    return "Not found"

def extract_skills(text):
    """
    Extract skills from resume text
    
    Args:
        text (str): Resume text
        
    Returns:
        list: List of extracted skills
    """
    skills = []
    text_lower = text.lower()
    
    # Check for common skills
    for skill in COMMON_SKILLS:
        # Check for exact matches or variations
        skill_lower = skill.lower()
        if skill_lower in text_lower:
            # Avoid adding duplicates or substrings of already added skills
            if not any(skill_lower in existing_skill.lower() for existing_skill in skills):
                skills.append(skill)
    
    # Look for skill section
    skill_section = extract_section(text, ["skills", "technical skills", "competencies", "technologies"])
    if skill_section:
        # Extract bullet points or comma-separated values
        bullet_skills = re.findall(r'[•\-*]\s*([^•\-*\n]+)', skill_section)
        for skill_text in bullet_skills:
            # Split by commas if multiple skills in one bullet
            for skill in skill_text.split(','):
                skill = skill.strip()
                if skill and len(skill) > 2 and not any(skill.lower() in s.lower() for s in skills):
                    skills.append(skill)
    
    # Limit to top 20 skills
    return skills[:20]

def extract_education(text):
    """
    Extract highest education level
    
    Args:
        text (str): Resume text
        
    Returns:
        str: Highest education level or 'Unknown'
    """
    education_section = extract_section(text, ["education", "academic", "qualifications"])
    if not education_section:
        education_section = text  # If no specific section, search the entire text
    
    # Look for degree mentions
    phd_pattern = r'\b(ph\.?d|doctor|doctorate)\b'
    masters_pattern = r'\b(master|ms|m\.s\.|m\.a\.|mba|m\.b\.a)\b'
    bachelors_pattern = r'\b(bachelor|bs|b\.s\.|b\.a\.|b\.e\.|btech|b\.tech)\b'
    associate_pattern = r'\b(associate|a\.a\.|a\.s\.)\b'
    
    if re.search(phd_pattern, education_section, re.IGNORECASE):
        return "PhD"
    elif re.search(masters_pattern, education_section, re.IGNORECASE):
        return "Masters"
    elif re.search(bachelors_pattern, education_section, re.IGNORECASE):
        return "Bachelors"
    elif re.search(associate_pattern, education_section, re.IGNORECASE):
        return "Associate"
    else:
        return "Unknown"

def extract_experience(text):
    """
    Extract years of experience
    
    Args:
        text (str): Resume text
        
    Returns:
        int: Years of experience or 0 if not found
    """
    # Look for explicit mentions of years of experience
    experience_patterns = [
        r'\b(\d+)\+?\s*years?\s*of\s*experience\b',
        r'\bexperience\s*:\s*(\d+)\+?\s*years?\b',
        r'\bexperienced\s*\w+\s*with\s*(\d+)\+?\s*years?\b'
    ]
    
    for pattern in experience_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                pass
    
    # If no explicit mention, try to calculate from work history
    experience_section = extract_section(text, ["experience", "employment", "work history"])
    if experience_section:
        # Look for year ranges like 2018-2023, 2018-present, etc.
        year_ranges = re.findall(r'\b(19|20)\d{2}\s*[-–—]\s*((19|20)\d{2}|present|current|now)\b', experience_section, re.IGNORECASE)
        if year_ranges:
            total_years = 0
            current_year = datetime.now().year
            
            for year_range in year_ranges:
                start_year = int(year_range[0])
                end_year_str = year_range[1]
                
                # Handle 'present' or similar
                if re.match(r'present|current|now', end_year_str, re.IGNORECASE):
                    end_year = current_year
                else:
                    try:
                        end_year = int(end_year_str)
                    except ValueError:
                        end_year = current_year
                
                # Calculate duration
                if start_year <= end_year and start_year >= 1950 and end_year <= current_year:
                    total_years += (end_year - start_year)
            
            return min(total_years, 40)  # Cap at 40 years to avoid unrealistic values
    
    # If all else fails, make an educated guess based on the number of job entries
    job_entries = count_job_entries(text)
    if job_entries > 0:
        # Assume average of 2 years per job
        return min(job_entries * 2, 40)
    
    return 0

def extract_experience_text(text):
    """
    Extract the experience section text
    
    Args:
        text (str): Resume text
        
    Returns:
        str: Experience section text or empty string
    """
    return extract_section(text, ["experience", "employment", "work history"])

def extract_education_text(text):
    """
    Extract the education section text
    
    Args:
        text (str): Resume text
        
    Returns:
        str: Education section text or empty string
    """
    return extract_section(text, ["education", "academic", "qualifications"])

def extract_summary(text):
    """
    Extract the summary/objective section
    
    Args:
        text (str): Resume text
        
    Returns:
        str: Summary section text or empty string
    """
    return extract_section(text, ["summary", "profile", "objective", "about me"])

def extract_job_role(text):
    """
    Extract the candidate's job role
    
    Args:
        text (str): Resume text
        
    Returns:
        str: Job role or 'Unknown'
    """
    # First check the beginning of the resume for a job title
    lines = text.split('\n')
    for line in lines[:15]:  # Check first 15 lines
        for job_title in COMMON_JOB_TITLES:
            if job_title.lower() in line.lower():
                return job_title
    
    # Check summary section
    summary = extract_summary(text)
    if summary:
        for job_title in COMMON_JOB_TITLES:
            if job_title.lower() in summary.lower():
                return job_title
    
    # Check the entire text
    for job_title in COMMON_JOB_TITLES:
        if job_title.lower() in text.lower():
            return job_title
    
    return "Unknown"

# Helper functions
def extract_section(text, section_headers):
    """
    Extract a specific section from the resume text
    
    Args:
        text (str): Resume text
        section_headers (list): List of possible section headers
        
    Returns:
        str: Section text or empty string
    """
    # Create regex pattern for section headers
    pattern = r'\b(' + '|'.join(section_headers) + r')\b[:\s]*\n'
    matches = re.finditer(pattern, text, re.IGNORECASE)
    
    for match in matches:
        section_start = match.end()
        section_name = match.group(1)
        
        # Find the next section header
        next_section_match = re.search(r'\n\s*[A-Z][A-Z\s]+[:\s]*\n', text[section_start:], re.MULTILINE)
        
        if next_section_match:
            section_end = section_start + next_section_match.start()
            return text[section_start:section_end].strip()
        else:
            # If no next section, take the rest of the text
            return text[section_start:].strip()
    
    return ""

def detect_tables(text):
    """
    Detect if the resume likely contains tables
    
    Args:
        text (str): Resume text
        
    Returns:
        bool: True if tables are detected
    """
    # Look for patterns that suggest tables
    table_patterns = [
        r'\|[^|]+\|[^|]+\|',  # | Cell 1 | Cell 2 |
        r'\+[-+]+\+',  # +----+----+
        r'\s*\w+\s*\|\s*\w+\s*\|'  # Word | Word |
    ]
    
    for pattern in table_patterns:
        if re.search(pattern, text):
            return True
    
    # Check for consistent spacing that might indicate a table
    lines = text.split('\n')
    space_aligned_lines = 0
    
    for i in range(len(lines) - 1):
        current_line = lines[i]
        next_line = lines[i + 1]
        
        # Count spaces in both lines
        current_spaces = [m.start() for m in re.finditer(r'\s{2,}', current_line)]
        next_spaces = [m.start() for m in re.finditer(r'\s{2,}', next_line)]
        
        # Check if spaces align
        if len(current_spaces) > 1 and len(next_spaces) > 1:
            matches = 0
            for cs in current_spaces:
                for ns in next_spaces:
                    if abs(cs - ns) <= 2:  # Allow 2 characters of variance
                        matches += 1
                        break
            
            if matches >= 2:  # At least 2 aligned spaces
                space_aligned_lines += 1
                if space_aligned_lines >= 3:  # 3 consecutive aligned lines
                    return True
        else:
            space_aligned_lines = 0
    
    return False

def count_job_entries(text):
    """
    Count the number of job entries in the resume
    
    Args:
        text (str): Resume text
        
    Returns:
        int: Number of job entries
    """
    experience_section = extract_section(text, ["experience", "employment", "work history"])
    if not experience_section:
        return 0
    
    # Look for company names or job titles
    company_patterns = [
        r'\n\s*([A-Z][A-Za-z\s,\.]+)\s*[,|]\s*(19|20)\d{2}',  # Company, 2020
        r'\n\s*([A-Z][A-Za-z\s,\.]+)\s*\|\s*',  # Company | 
        r'\n\s*([A-Z][A-Za-z\s,\.]+)\s*[-–—]\s*',  # Company - 
        r'\n\s*([A-Z][A-Za-z\s,\.&]+)\s*$'  # Company at end of line
    ]
    
    companies = []
    for pattern in company_patterns:
        matches = re.findall(pattern, experience_section)
        if matches:
            companies.extend(matches if isinstance(matches[0], str) else [m[0] for m in matches])
    
    # Remove duplicates and count
    unique_companies = set()
    for company in companies:
        # Clean up and normalize
        company = company.strip()
        if len(company) > 3 and not company.lower() in ["resume", "experience", "work history", "employment"]:
            unique_companies.add(company.lower())
    
    return len(unique_companies) or len(re.findall(r'\n\s*\d{4}\s*[-–—]\s*\d{4}|\n\s*\d{4}\s*[-–—]\s*present', experience_section, re.IGNORECASE))

# ATS-specific analysis functions
def calculate_keyword_density(text):
    """
    Calculate keyword density in the resume
    
    Args:
        text (str): Resume text
        
    Returns:
        float: Keyword density score (0-1)
    """
    # Tokenize and remove stopwords
    stop_words = set(stopwords.words('english'))
    tokens = word_tokenize(text.lower())
    filtered_tokens = [word for word in tokens if word.isalnum() and word not in stop_words]
    
    # Count occurrences of each word
    word_counts = Counter(filtered_tokens)
    total_words = len(filtered_tokens)
    
    # Calculate density of important keywords
    important_keywords = [skill.lower() for skill in COMMON_SKILLS]
    important_keywords.extend([title.lower() for title in COMMON_JOB_TITLES])
    
    keyword_count = sum(word_counts[word] for word in word_counts if word in important_keywords)
    
    if total_words > 0:
        return min(1.0, keyword_count / total_words)
    else:
        return 0.0

def calculate_format_score(resume_data):
    """
    Calculate format score for ATS compatibility
    
    Args:
        resume_data (dict): Extracted resume data
        
    Returns:
        float: Format score (0-1)
    """
    score = 0.0
    
    # Check for proper sections
    sections = resume_data.get("sections", {})
    if sections.get("summary", False):
        score += 0.2
    if sections.get("experience", False):
        score += 0.3
    if sections.get("education", False):
        score += 0.2
    if sections.get("skills", False):
        score += 0.3
    
    # Check for contact information
    if resume_data.get("email", "Not found") != "Not found":
        score += 0.1
    if resume_data.get("phone", "Not found") != "Not found":
        score += 0.1
    
    # Check for proper formatting
    if resume_data.get("has_bullet_points", False):
        score += 0.1
    if not resume_data.get("has_tables", False):  # Tables can cause ATS issues
        score += 0.1
    
    # Normalize score to 0-1 range
    return min(1.0, score)

def calculate_content_score(resume_data):
    """
    Calculate content quality score for ATS compatibility
    
    Args:
        resume_data (dict): Extracted resume data
        
    Returns:
        float: Content score (0-1)
    """
    score = 0.0
    
    # Check for skills
    skills = resume_data.get("skills", [])
    if len(skills) >= 10:
        score += 0.3
    elif len(skills) >= 5:
        score += 0.2
    elif len(skills) > 0:
        score += 0.1
    
    # Check for experience
    experience = resume_data.get("experience", 0)
    if experience >= 5:
        score += 0.3
    elif experience >= 2:
        score += 0.2
    elif experience > 0:
        score += 0.1
    
    # Check for education
    education = resume_data.get("education", "Unknown")
    if education in ["PhD", "Masters"]:
        score += 0.2
    elif education == "Bachelors":
        score += 0.15
    elif education != "Unknown":
        score += 0.1
    
    # Check for measurable achievements (numbers in experience section)
    experience_text = resume_data.get("experience_text", "")
    if re.search(r'\d+%|\d+\s*million|\$\d+|increased|decreased|improved|reduced|\d+\s*people', experience_text, re.IGNORECASE):
        score += 0.2
    
    # Check for action verbs
    action_verbs = ["managed", "developed", "created", "implemented", "designed", "led", "built", "achieved", "improved", "increased"]
    if any(verb in experience_text.lower() for verb in action_verbs):
        score += 0.1
    
    # Normalize score to 0-1 range
    return min(1.0, score)
