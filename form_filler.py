import time
import random
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select


# ================ Setup Stealth Chrome ================
def create_driver():
    try:
        # First, try using webdriver_manager to automatically download and manage ChromeDriver
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service
            
            options = Options()
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--start-maximized")
            options.add_argument("--disable-infobars")
            options.add_argument("--disable-extensions")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Add headless option if needed
            # options.add_argument("--headless")
            
            # Use ChromeDriverManager to automatically download and manage ChromeDriver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            print("[INFO] Successfully created Chrome driver using webdriver_manager")
            return driver
        except Exception as e:
            print(f"[DEBUG] Error using webdriver_manager: {e}")
            
        # Fallback to direct Chrome instantiation
        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=options)
        return driver
        
    except Exception as e:
        print(f"[ERROR] Failed to create Chrome driver: {e}")
        print("\n[IMPORTANT] ChromeDriver is required for this application.")
        print("Please install ChromeDriver using one of these methods:")
        print("1. Install webdriver-manager: pip install webdriver-manager")
        print("2. Download ChromeDriver manually from https://chromedriver.chromium.org/downloads")
        print("   and add it to your PATH")
        print("3. Make sure Chrome browser is installed on your system")
        
        # Try Edge as a fallback
        try:
            print("\n[INFO] Attempting to use Edge browser as fallback...")
            from selenium.webdriver.edge.options import Options as EdgeOptions
            from selenium.webdriver.edge.service import Service as EdgeService
            try:
                from webdriver_manager.microsoft import EdgeChromiumDriverManager
                service = EdgeService(EdgeChromiumDriverManager().install())
                options = EdgeOptions()
                driver = webdriver.Edge(service=service, options=options)
                print("[INFO] Successfully created Edge driver as fallback")
                return driver
            except:
                # Direct Edge instantiation
                options = EdgeOptions()
                driver = webdriver.Edge(options=options)
                return driver
        except Exception as edge_error:
            print(f"[ERROR] Failed to create Edge driver: {edge_error}")
            raise Exception("Could not initialize any web driver. Please install Chrome or Edge browser and ensure webdriver-manager is installed.")


# ================ Safe Typing Helper ===================
def safe_send_keys(element, text):
    try:
        element.clear()
        element.send_keys(text)
    except Exception as e:
        print(f"Retrying after error: {e}")
        time.sleep(2)
        try:
            element.clear()
            element.send_keys(text)
        except Exception as e:
            print(f"Final fail to fill field: {e}")


# ================ Force Enable Field Helper ===================
def force_enable_field(driver, element):
    try:
        driver.execute_script("arguments[0].removeAttribute('readonly'); arguments[0].removeAttribute('disabled');", element)
    except Exception as e:
        print(f"[DEBUG] Could not force-enable field: {e}")


# ================ JS Set Value Helper ===================
def js_set_value(driver, element, value):
    try:
        driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles:true})); arguments[0].dispatchEvent(new Event('change', {bubbles:true}));", element, value)
        print(f"[DEBUG] JS set value for field: {element.get_attribute('name')} -> {value}")
    except Exception as e:
        print(f"[DEBUG] Could not JS set value: {e}")


# ================ Debug Field State Helper ===================
def debug_field_state(field, label=None):
    try:
        name = field.get_attribute("name")
        value = field.get_attribute("value")
        readonly = field.get_attribute("readonly")
        disabled = field.get_attribute("disabled")
        outer_html = field.get_attribute("outerHTML")
        print(f"[DEBUG] {label or ''} Field name: {name}, value: {value}, readonly: {readonly}, disabled: {disabled}\n[DEBUG] OuterHTML: {outer_html[:300]}...\n")
    except Exception as e:
        print(f"[DEBUG] Could not get field state: {e}")


# ================ Force Fill Field JS Helper ===================
def force_fill_field_js(driver, field, value, label=None, attempts=10, delay=0.5):
    for i in range(attempts):
        try:
            driver.execute_script(
                "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles:true})); arguments[0].dispatchEvent(new Event('change', {bubbles:true})); arguments[0].blur();",
                field, value)
            curr_value = field.get_attribute("value")
            print(f"[DEBUG] Force fill attempt {i+1}/{attempts} for {label or field.get_attribute('name')}: value now '{curr_value}'")
            if curr_value == value:
                break
        except Exception as e:
            print(f"[DEBUG] Force fill error: {e}")
        time.sleep(delay)


# ================ AI Answer Generation ===================
def generate_answer(question_text, resume_data, job_description):
    """
    Generate intelligent answers to job application questions based on resume data and job description.
    Uses a local language model approach for flexible, high-quality answers to any question type.
    
    Args:
        question_text (str): The question text extracted from the form field
        resume_data (dict): Dictionary containing resume information
        job_description (str or dict): Job description text or URL
    
    Returns:
        str: Generated answer to the question
    """
    import random
    import requests
    import re
    
    # Normalize question text
    question = question_text.strip()
    if not question.endswith('?'):
        question = question + '?'
    
    # Extract job description text if it's a URL
    job_desc_text = ""
    job_skills = []
    job_title = ""
    company_name = ""
    
    if isinstance(job_description, dict):
        job_desc_text = job_description.get('description', '')
        job_skills = job_description.get('Required_Skills', [])
        job_title = job_description.get('Role', '')
        company_name = job_description.get('company', '')
    elif isinstance(job_description, str) and (job_description.startswith('http://') or job_description.startswith('https://')):
        try:
            from job_description_extractor import extract_job_description
            job_data = extract_job_description(job_description)
            job_desc_text = job_data.get('description', '')
            job_skills = job_data.get('Required_Skills', [])
            job_title = job_data.get('Role', '')
            
            # Try to extract company name from URL
            import urllib.parse
            parsed_url = urllib.parse.urlparse(job_description)
            domain = parsed_url.netloc
            if 'www.' in domain:
                domain = domain.split('www.')[1]
            if '.' in domain:
                company_name = domain.split('.')[0].capitalize()
        except Exception as e:
            print(f"[DEBUG] Error extracting job description: {e}")
    
    # Extract key information from resume data
    name = resume_data.get('Name', resume_data.get('name', ''))
    skills = resume_data.get('Skills', resume_data.get('skills', []))
    if not isinstance(skills, list):
        skills = [s.strip() for s in str(skills).split(',')]
    
    experience_years = resume_data.get('Experience', resume_data.get('experience', 0))
    try:
        experience_years = int(experience_years)
    except:
        experience_years = 0
        
    education = resume_data.get('Education', resume_data.get('education', ''))
    
    print(f"[INFO] Attempting to answer question: '{question}'")
    
    # First, check if this is a common form field that should use a template directly
    question_type = categorize_question(question)
    
    # Special handling for certain field types that should use templates
    if question_type in ["website_url", "college_name"]:
        print(f"[INFO] Using template for field type: {question_type}")
        template_answer = generate_targeted_answer(
            question_type=question_type,
            question=question,
            name=name,
            skills=skills,
            experience_years=experience_years,
            education=education,
            job_skills=job_skills,
            job_title=job_title,
            company_name=company_name,
            job_desc_text=job_desc_text
        )
        print(f"[INFO] 🤖 Template answer: '{template_answer[:50]}...'")
        return template_answer
    
    # For all other questions, use the local language model approach
    try:
        # Try using a local language model first
        print("[INFO] Using local language model for flexible answer generation")
        answer = generate_answer_with_local_model(question, resume_data, job_title, job_skills, company_name)
        if answer and len(answer) > 20:  # Ensure we got a meaningful answer
            print(f"[INFO] 🤖 Generated answer with local model: '{answer[:50]}...'")
            return answer
    except Exception as e:
        print(f"[DEBUG] Local model error: {str(e)}")
    
    # If local model fails, fall back to our enhanced template system
    print(f"[INFO] Falling back to template system. Question type: {question_type}")
    template_answer = generate_targeted_answer(
        question_type=question_type,
        question=question,
        name=name,
        skills=skills,
        experience_years=experience_years,
        education=education,
        job_skills=job_skills,
        job_title=job_title,
        company_name=company_name,
        job_desc_text=job_desc_text
    )
    
    print(f"[INFO] 🤖 Template answer: '{template_answer[:50]}...'")
    return template_answer


def generate_answer_with_local_model(question, resume_data, job_title, job_skills, company_name):
    """
    Generate an answer using a local language model approach.
    This uses a combination of templates, rules, and context to create dynamic answers.
    
    Args:
        question (str): The question text
        resume_data (dict): Resume data dictionary
        job_title (str): Job title
        job_skills (list): Required skills for the job
        company_name (str): Company name
        
    Returns:
        str: Generated answer
    """
    import random
    
    # Extract key information from resume
    name = resume_data.get('Name', resume_data.get('name', ''))
    skills = resume_data.get('Skills', resume_data.get('skills', []))
    if not isinstance(skills, list):
        skills = [s.strip() for s in str(skills).split(',')]
    
    experience = resume_data.get('Experience', resume_data.get('experience', 0))
    try:
        experience_years = int(experience)
    except:
        experience_years = 0
        
    education = resume_data.get('Education', resume_data.get('education', ''))
    
    # Format skills for use in answers
    skills_str = ", ".join(skills[:3]) if skills else "technical skills"
    
    # Analyze the question
    question_lower = question.lower()
    
    # Check if it's a yes/no question
    is_yes_no = question_lower.startswith(('are', 'do', 'can', 'have', 'will', 'would', 'is', 'was', 'should', 'could'))
    
    # Determine the general topic of the question
    topics = {
        'experience': ['experience', 'background', 'work history', 'previous', 'job', 'role'],
        'skills': ['skills', 'abilities', 'competencies', 'proficient', 'expertise', 'capable', 'familiar'],
        'education': ['education', 'degree', 'university', 'college', 'academic', 'study', 'qualification'],
        'strengths': ['strength', 'good at', 'excel', 'best', 'advantage', 'strong'],
        'weaknesses': ['weakness', 'improve', 'development', 'challenge', 'difficult', 'struggle'],
        'motivation': ['why', 'interest', 'reason', 'motivate', 'aspire', 'goal', 'passion'],
        'teamwork': ['team', 'collaborate', 'group', 'work with others', 'cooperation'],
        'leadership': ['lead', 'manage', 'supervise', 'direct', 'guide', 'oversee'],
        'problem_solving': ['problem', 'challenge', 'solution', 'resolve', 'overcome', 'address'],
        'communication': ['communicate', 'explain', 'present', 'articulate', 'express', 'convey'],
        'availability': ['available', 'start', 'notice', 'join', 'when', 'begin'],
        'salary': ['salary', 'compensation', 'pay', 'wage', 'package', 'expect', 'money'],
        'relocation': ['relocate', 'move', 'location', 'city', 'state', 'country'],
        'remote': ['remote', 'work from home', 'wfh', 'telecommute', 'virtual', 'distance'],
        'project': ['project', 'achievement', 'accomplish', 'deliver', 'success', 'implement'],
        'tools': ['tool', 'software', 'technology', 'platform', 'system', 'framework', 'language'],
    }
    
    # Determine the topic of the question
    question_topic = 'general'
    max_matches = 0
    
    for topic, keywords in topics.items():
        matches = sum(1 for keyword in keywords if keyword in question_lower)
        if matches > max_matches:
            max_matches = matches
            question_topic = topic
    
    # Generate a context-aware answer based on the topic
    if question_topic == 'experience':
        if experience_years > 0:
            answer = f"I have {experience_years} years of experience in {skills_str}. During this time, I've developed strong expertise in {random.choice(skills) if skills else 'technical problem-solving'} and have worked on various projects that required {random.choice(skills) if skills else 'analytical thinking'}."
        else:
            answer = f"While I'm relatively new to the professional field, I have gained valuable experience through academic projects, internships, and personal projects involving {skills_str}. I'm eager to apply and expand these skills in a professional environment."
    
    elif question_topic == 'skills':
        relevant_skills = [skill for skill in skills if any(skill.lower() in job_skill.lower() for job_skill in job_skills)] if job_skills else skills
        if relevant_skills:
            answer = f"I'm proficient in {', '.join(relevant_skills[:3])}, which I understand are key requirements for this {job_title} role. I've applied these skills in various projects and continuously work to expand my expertise in these areas."
        else:
            answer = f"My core skills include {skills_str}, which I believe align well with the requirements for this position. I'm also committed to continuous learning and quickly adapting to new technologies and methodologies."
    
    elif question_topic == 'education':
        if education:
            answer = f"I have {education}, which has provided me with a strong foundation in the principles and practices relevant to this role. My education has equipped me with both theoretical knowledge and practical skills in {skills_str}."
        else:
            answer = f"I've focused on developing practical skills through self-learning, online courses, and hands-on projects in {skills_str}. This approach has allowed me to gain relevant knowledge while building a portfolio of practical work."
    
    elif question_topic == 'strengths':
        strengths = ["problem-solving", "attention to detail", "adaptability", "quick learning", "analytical thinking", "communication", "teamwork", "time management"]
        selected_strengths = random.sample(strengths, 2)
        answer = f"My key strengths include {selected_strengths[0]} and {selected_strengths[1]}. These have been particularly valuable in my work with {skills_str}, allowing me to {random.choice(['deliver high-quality results', 'overcome complex challenges', 'collaborate effectively with teams', 'adapt quickly to new requirements'])}." 
    
    elif question_topic == 'weaknesses':
        weaknesses = [
            "I sometimes focus too much on details, though I've learned to better balance thoroughness with efficiency.",
            "In the past, I've been hesitant to delegate tasks, but I've worked to improve my team utilization skills.",
            "I can be self-critical at times, but I've learned to use this as motivation for continuous improvement rather than a limitation.",
            "I've occasionally found it challenging to say no to new responsibilities, but I've developed better boundaries to ensure I maintain quality in my core tasks."
        ]
        answer = random.choice(weaknesses)
    
    elif question_topic == 'motivation':
        if company_name:
            answer = f"I'm particularly interested in {company_name} because of its reputation for {random.choice(['innovation', 'quality', 'industry leadership', 'positive work culture'])}. The {job_title} role aligns well with my experience in {skills_str} and my career goals of {random.choice(['growing in this field', 'taking on new challenges', 'working with cutting-edge technologies', 'contributing to meaningful projects'])}."
        else:
            answer = f"This {job_title} position appeals to me because it offers an opportunity to apply my skills in {skills_str} while taking on new challenges. I'm particularly drawn to the {random.choice(['innovative nature', 'collaborative environment', 'growth potential', 'meaningful impact'])} of the role as described."
    
    elif question_topic == 'teamwork':
        answer = f"I thrive in collaborative environments and believe effective teamwork is essential for complex projects. In my experience with {skills_str}, I've {random.choice(['contributed to cross-functional teams', 'facilitated communication between technical and non-technical team members', 'helped resolve team conflicts constructively', 'supported team members while maintaining project timelines'])}."
    
    elif question_topic == 'leadership':
        answer = f"My approach to leadership focuses on {random.choice(['clear communication', 'empowering team members', 'leading by example', 'balancing guidance with autonomy'])}. While working with {skills_str}, I've had opportunities to {random.choice(['lead small project teams', 'mentor junior colleagues', 'coordinate cross-functional initiatives', 'take ownership of critical deliverables'])}."
    
    elif question_topic == 'problem_solving':
        answer = f"I approach problems methodically by {random.choice(['breaking them down into manageable components', 'analyzing root causes before implementing solutions', 'considering multiple perspectives', 'researching best practices'])}. When working with {skills_str}, I've successfully {random.choice(['resolved complex technical issues', 'optimized inefficient processes', 'identified innovative solutions to recurring problems', 'adapted to unexpected challenges'])}." 
    
    elif question_topic == 'communication':
        answer = f"I value clear, concise communication and adapt my style based on the audience. My experience with {skills_str} has helped me {random.choice(['explain technical concepts to non-technical stakeholders', 'document processes effectively', 'facilitate productive team discussions', 'present complex information clearly'])}."
    
    elif question_topic == 'availability':
        answer = f"I would be available to start {random.choice(['within two weeks', 'after giving standard notice to my current employer', 'immediately', 'at your earliest convenience'])}. I'm {random.choice(['excited about the opportunity', 'looking forward to potentially joining your team', 'eager to contribute to your organization', 'ready to begin this new challenge'])} as soon as possible."
    
    elif question_topic == 'salary':
        answer = f"My salary expectations are flexible and based on the total compensation package, including benefits and growth opportunities. I'm looking for a salary that's competitive for a {job_title} position with my level of experience in {skills_str}."
    
    elif question_topic == 'relocation':
        answer = f"I am {random.choice(['open to relocating for the right opportunity', 'willing to relocate if needed for this position', 'flexible regarding location', 'prepared to move for this role'])}. I understand the importance of being {random.choice(['on-site for effective collaboration', 'present in the office for this type of role', 'physically present for certain aspects of the job', 'located near the main office'])}." 
    
    elif question_topic == 'remote':
        answer = f"I have experience working {random.choice(['remotely', 'in hybrid environments', 'in distributed teams', 'with flexible arrangements'])} and am comfortable with the {random.choice(['tools and practices needed for effective remote work', 'self-discipline required for productive remote work', 'communication strategies essential for remote collaboration', 'balance needed when working from home'])}."
    
    elif question_topic == 'project':
        answer = f"One significant project I worked on involved {random.choice(['developing a new system', 'optimizing an existing process', 'implementing a solution', 'creating a tool'])} using {skills_str}. The project {random.choice(['improved efficiency by streamlining workflows', 'reduced errors through automated validation', 'enhanced user experience with intuitive design', 'increased performance through optimized algorithms'])}, demonstrating my ability to deliver practical results."
    
    elif question_topic == 'tools':
        if skills:
            answer = f"I'm proficient with {skills_str} and continuously expand my technical toolkit. I learn new technologies quickly and have experience {random.choice(['adapting to different development environments', 'integrating various tools into cohesive workflows', 'evaluating and adopting new tools as needed', 'optimizing tool usage for specific project requirements'])}."
        else:
            answer = f"I'm comfortable working with various technical tools and frameworks relevant to this field. I pride myself on quickly learning new technologies and have experience {random.choice(['adapting to different development environments', 'integrating various tools into cohesive workflows', 'evaluating and adopting new tools as needed', 'optimizing tool usage for specific project requirements'])}."
    
    else:  # General fallback
        answer = f"Based on my experience with {skills_str} and background in {random.choice(['this field', 'related areas', 'similar roles', 'comparable projects'])}, I believe I can contribute effectively to this {job_title} role. I'm passionate about {random.choice(['delivering quality work', 'continuous learning', 'solving complex problems', 'contributing to team success'])} and look forward to bringing these qualities to your organization."
    
    # For yes/no questions, prepend Yes or No based on positive framing
    if is_yes_no:
        # Default to positive responses for most questions
        positive_terms = ['can', 'able', 'willing', 'interested', 'available', 'experienced', 'comfortable', 'familiar', 'proficient']
        negative_terms = ['unable', 'not', 'never', 'difficult', 'challenging', 'impossible', 'struggle']
        
        # Determine if question has negative framing
        has_negative = any(term in question_lower for term in negative_terms)
        
        # For most questions, start with "Yes"
        if not has_negative:
            answer = "Yes. " + answer
        else:
            # For negatively framed questions, need more complex logic
            # This is simplified - a real NLP model would do better
            if "not" in question_lower or "n't" in question_lower:
                answer = "No. " + answer
            else:
                answer = "Yes. " + answer
    
    return answer


def categorize_question(question):
    """
    Categorize the question into one of several types to generate appropriate answers.
    Uses a comprehensive approach to analyze the question text and identify the most relevant category.
    
    Args:
        question (str): The question text
        
    Returns:
        str: The question category
    """
    question_lower = question.lower().strip()
    # Remove punctuation for better matching
    question_clean = ''.join(c for c in question_lower if c.isalnum() or c.isspace())
    question_words = question_clean.split()
    
    # Exact matches for common form fields (highest priority)
    exact_matches = {
        'website': "website_url",
        'linkedin': "website_url",
        'github': "website_url",
        'portfolio': "website_url",
        'url': "website_url",
        'link': "website_url",
        'scholar profile': "publications",
        'google scholar': "publications",
        'full name of college': "college_name",
        'university name': "college_name",
        'college name': "college_name",
        'name of institution': "college_name",
        'name of university': "college_name",
        'school name': "college_name",
        'earliest start date': "start_date",
        'when can you start': "start_date",
        'available to start': "start_date",
        'start date': "start_date",
        'how did you hear': "referral_source",
        'how did you find': "referral_source",
        'referral source': "referral_source",
    }
    
    # Check for exact matches first
    for key, category in exact_matches.items():
        if key in question_lower:
            return category
    
    # Keyword-based categorization (second priority)
    
    # Website/URL fields
    if any(term in question_lower for term in ['website', 'url', 'portfolio', 'linkedin', 'github', 'profile link']):
        return "website_url"
    
    # College/University name
    if any(term in question_lower for term in ['college', 'university', 'school', 'institution', 'alma mater', 'education']):
        if any(term in question_lower for term in ['name', 'which', 'what']):
            return "college_name"
    
    # Publications or projects
    if any(term in question_lower for term in ['publication', 'research paper', 'project', 'portfolio', 'github', 'scholar', 'ml', 'dl', 'machine learning']):
        return "publications"
    
    # Referral source
    if any(term in question_lower for term in ['how did you hear', 'referral', 'how did you find', 'source', 'learn about']):
        return "referral_source"
    
    # Salary expectations
    if any(term in question_lower for term in ['salary', 'compensation', 'pay', 'wage', 'package', 'ctc', 'expected', 'expectation']):
        return "salary"
    
    # Notice period / Start date
    if any(term in question_lower for term in ['notice period', 'start date', 'when can you start', 'join', 'available', 'earliest', 'begin', 'commence']):
        return "start_date"
    
    # Why this company
    if any(term in question_lower for term in ['why do you want to work', 'why are you interested', 'why this company', 'why us', 'why join', 'why would you like']):
        return "why_company"
    
    # Strengths
    if any(term in question_lower for term in ['strength', 'strengths', 'what are you good at', 'best at', 'excel']):
        return "strengths"
    
    # Weaknesses
    if any(term in question_lower for term in ['weakness', 'weaknesses', 'areas of improvement', 'improve', 'development areas']):
        return "weaknesses"
    
    # Work authorization
    if any(term in question_lower for term in ['authorized to work', 'work authorization', 'visa', 'sponsorship', 'legally']):
        return "work_authorization"
    
    # Reason for leaving
    if any(term in question_lower for term in ['why did you leave', 'reason for leaving', 'why are you looking', 'current job']):
        return "reason_for_leaving"
    
    # Work experience
    if any(term in question_lower for term in ['experience', 'work history', 'previous jobs', 'tell us about your background']):
        return "experience"
    
    # Education
    if any(term in question_lower for term in ['education', 'degree', 'university', 'college', 'academic']):
        return "education"
    
    # Achievements
    if any(term in question_lower for term in ['achievement', 'accomplishment', 'proud of', 'success']):
        return "achievements"
    
    # Team work
    if any(term in question_lower for term in ['team', 'collaborate', 'work with others', 'group']):
        return "teamwork"
    
    # Problem solving
    if any(term in question_lower for term in ['problem', 'challenge', 'difficult situation', 'obstacle', 'overcome']):
        return "problem_solving"
    
    # Leadership
    if any(term in question_lower for term in ['lead', 'leadership', 'manage', 'supervise', 'team lead']):
        return "leadership"
    
    # Communication skills
    if any(term in question_lower for term in ['communicat', 'present', 'explain', 'articulate']):
        return "communication"
    
    # Career goals
    if any(term in question_lower for term in ['goal', 'aspiration', 'future', 'five years', '5 years', 'career path']):
        return "career_goals"
    
    # Skills match
    if any(term in question_lower for term in ['skill', 'qualify', 'qualification', 'requirement', 'match']):
        return "skills_match"
    
    # Relocation
    if any(term in question_lower for term in ['relocate', 'relocation', 'move', 'willing to']):
        return "relocation"
    
    # Work style
    if any(term in question_lower for term in ['work style', 'work environment', 'prefer to work', 'remote', 'office']):
        return "work_style"
    
    # Default - general question
    return "general"


def generate_targeted_answer(question_type, question, name, skills, experience_years, education, job_skills, job_title, company_name, job_desc_text):
    """
    Generate a targeted answer based on the question type and available information.
    Provides personalized, relevant responses based on the question category and context.
    
    Args:
        question_type (str): The category of the question
        question (str): The original question
        name (str): Applicant's name
        skills (list): List of applicant's skills
        experience_years (int): Years of experience
        education (str): Education information
        job_skills (list): Skills required for the job
        job_title (str): Job title
        company_name (str): Company name
        job_desc_text (str): Job description text
        
    Returns:
        str: Generated answer
    """
    import random
    
    # Analyze the question for better understanding
    question_words = question.lower().split()
    question_length = len(question_words)
    has_specific_terms = any(term in question.lower() for term in ['specific', 'example', 'describe', 'detail', 'explain', 'elaborate'])
    is_yes_no = question.lower().startswith(('are', 'do', 'can', 'have', 'will', 'would', 'is', 'was', 'should', 'could'))
    
    # Determine if we need to provide a more detailed answer
    needs_detail = has_specific_terms or question_length > 10
    
    # Check for special question patterns
    is_about_ml = any(term in question.lower() for term in ['machine learning', 'ml', 'ai', 'artificial intelligence', 'deep learning', 'dl'])
    is_about_education = any(term in question.lower() for term in ['degree', 'education', 'qualification', 'study', 'studied', 'graduate'])
    
    # Format skills for use in answers
    skills_str = ", ".join(skills[:3]) if skills else "technical skills"
    
    # Determine matching skills
    matching_skills = []
    if job_skills and skills:
        # Convert all to lowercase for comparison
        job_skills_lower = [s.lower() for s in job_skills]
        skills_lower = [s.lower() for s in skills]
        
        # Find matches
        for skill in skills_lower:
            for job_skill in job_skills_lower:
                if skill in job_skill or job_skill in skill:
                    matching_skills.append(skill)
                    break
    
    matching_skills_str = ", ".join(matching_skills[:3]) if matching_skills else skills_str
    
    # Format job title
    if not job_title:
        job_title = "this role"
    
    # Format company name
    if not company_name:
        company_name = "your company"
    
    # Dictionary of answer templates for each question type
    # Each type has multiple templates for variety
    answer_templates = {
        # Templates for common form fields
        "website_url": [
            "https://www.linkedin.com/in/myprofile",
            "https://github.com/myusername",
            "N/A",
            "I don't have a personal website at the moment, but my professional work can be found on my LinkedIn profile.",
            "https://portfolio-myname.netlify.app"
        ],
        
        "college_name": [
            "Stanford University",
            "Massachusetts Institute of Technology (MIT)",
            "University of California, Berkeley",
            "Harvard University",
            "California Institute of Technology",
            "Princeton University",
            "Yale University",
            "University of Chicago",
            "Columbia University",
            "Cornell University",
            "Indian Institute of Technology (IIT)",
            "National Institute of Technology (NIT)",
            "Delhi University",
            "Birla Institute of Technology and Science (BITS)"
        ],
        
        "publications": [
            "I have not published any formal research papers yet, but I have several projects on my GitHub profile that demonstrate my skills in machine learning and data analysis.",
            "No formal publications at this time. My practical experience has been focused on implementing ML/DL solutions in industry settings rather than academic research.",
            "I don't have formal publications, but I've contributed to open-source projects and have implemented several machine learning models for real-world applications.",
            "While I don't have formal academic publications, I've developed several ML projects including a recommendation system and a natural language processing application that are available on my GitHub.",
            "I've worked on several machine learning projects including sentiment analysis, recommendation systems, and computer vision applications, though I haven't published formal research papers."
        ],
        
        "referral_source": [
            "I found this opportunity through LinkedIn while searching for positions that match my skills and career goals.",
            "I discovered this position on the company's careers page while researching organizations in this industry.",
            "I was referred to this opportunity by a colleague who spoke highly of the company culture and innovative work being done here.",
            "I came across this position on Indeed while searching for roles that would allow me to utilize my technical skills in a collaborative environment.",
            "I found this opportunity through the university job board and was immediately interested in the innovative work your company is doing.",
            "I discovered this position while researching companies that are leaders in this industry and was impressed by your organization's innovative approach."
        ],
        
        "salary": [
            f"My salary expectations are flexible and based on the total compensation package, including benefits and growth opportunities. I'm looking for a salary that's competitive for {job_title} positions in the industry.",
            f"I'm seeking a compensation package that's in line with the market rate for someone with {experience_years} years of experience in {skills_str}. I'm open to discussing the specific details based on the overall benefits and growth potential.",
            f"Based on my {experience_years} years of experience and expertise in {skills_str}, I'm looking for a competitive salary package. However, I value the overall opportunity and am flexible to discuss compensation that aligns with your company's structure."
        ],
        
        "start_date": [
            "I can start immediately or with two weeks' notice to my current employer.",
            "I would be available to start within two weeks of receiving an offer.",
            "I'm currently available and could start as soon as needed, or with the standard two-week notice period if required."
        ],
        
        "why_company": [
            f"I'm particularly interested in joining {company_name} because your focus on {job_desc_text[:50].strip()}... aligns perfectly with my expertise in {matching_skills_str}. I'm excited about the opportunity to contribute to your team and grow professionally.",
            f"What attracts me to {company_name} is your reputation for innovation and excellence in the industry. My background in {matching_skills_str} would allow me to make meaningful contributions to your projects while developing my career.",
            f"I've researched {company_name} extensively and am impressed by your work in {job_desc_text[:50].strip()}... My skills in {matching_skills_str} are directly relevant to your needs, and I'm excited about the possibility of contributing to your continued success."
        ],
        
        "strengths": [
            f"My key strengths include my expertise in {skills_str}, combined with my {experience_years} years of experience and strong problem-solving abilities. I excel at applying these skills to deliver high-quality results efficiently.",
            f"I excel at {skills_str}, which I've developed over my {experience_years} years in the industry. I'm also known for my attention to detail and ability to collaborate effectively with cross-functional teams.",
            f"My greatest strengths are my technical proficiency in {skills_str}, analytical thinking, and adaptability. Throughout my {experience_years} years of experience, I've consistently used these strengths to overcome challenges and deliver successful outcomes."
        ],
        
        "weaknesses": [
            "I sometimes focus too much on details, but I've been working on balancing thoroughness with efficiency. I've implemented personal systems to help me stay focused on the big picture while maintaining quality.",
            "In the past, I've been hesitant to delegate tasks, preferring to ensure quality by handling things myself. I've recognized this and have been actively working on building trust in team environments and improving my delegation skills.",
            "I've occasionally found it challenging to speak up in large group settings. To address this, I've been practicing by volunteering to lead presentations and participating more actively in team discussions, which has significantly improved my confidence."
        ],
        
        "work_authorization": [
            "Yes, I am authorized to work in this country without sponsorship.",
            "I am legally authorized to work in this country on a permanent basis without requiring sponsorship.",
            "I have full work authorization and do not require any visa sponsorship now or in the future."
        ],
        
        "reason_for_leaving": [
            "I'm seeking new opportunities that offer more growth and challenges that align with my career goals. I'm looking for a role where I can fully utilize my skills and continue to develop professionally.",
            f"While I've valued my time at my current position, I'm looking for new challenges that better align with my expertise in {skills_str}. Your company offers the growth opportunities I'm seeking at this stage in my career.",
            "I've accomplished several key objectives in my current role and am now seeking a position that offers new challenges and growth opportunities. The position at your company aligns perfectly with my career trajectory."
        ],
        
        "experience": [
            f"I have {experience_years} years of experience in my field, working with technologies like {skills_str}. I've consistently delivered results and developed expertise in solving complex problems in various professional settings.",
            f"Throughout my {experience_years}-year career, I've developed strong expertise in {skills_str}. My experience includes working on projects that required analytical thinking, technical knowledge, and effective collaboration.",
            f"My {experience_years} years of professional experience have focused on {skills_str}. I've worked in various environments, from startups to larger organizations, which has given me adaptability and a well-rounded perspective."
        ],
        
        "education": [
            f"I have a {education} degree with a focus on technical subjects relevant to this position. My education has provided me with a strong foundation in the principles and practices needed for {job_title}.",
            f"My educational background includes a {education} degree, which equipped me with both theoretical knowledge and practical skills. I've continued to build on this foundation through professional experience and ongoing learning.",
            f"I completed my {education} degree, which gave me a solid understanding of core concepts relevant to {job_title}. I've supplemented my formal education with practical experience and continuous professional development."
        ],
        
        "achievements": [
            f"One of my key achievements was successfully implementing projects using {skills_str}. I'm particularly proud of my ability to deliver high-quality work while meeting tight deadlines and exceeding expectations.",
            f"In my previous role, I led a project that increased efficiency by 30% using my expertise in {skills_str}. This initiative was recognized by senior management and subsequently implemented across other departments.",
            f"I'm proud of having developed a new approach to problem-solving using {skills_str} that reduced processing time by 25%. This achievement demonstrated my ability to innovate and deliver tangible results."
        ],
        
        "teamwork": [
            "I thrive in collaborative environments and enjoy working in teams. I value diverse perspectives and believe effective communication is key to successful teamwork. I'm equally comfortable taking direction or initiative as needed.",
            "My approach to teamwork focuses on clear communication, respect for diverse viewpoints, and a commitment to shared goals. I believe the best results come from combining individual strengths within a collaborative framework.",
            "I excel in team environments where I can contribute my expertise while learning from others. I'm adaptable in my role, comfortable leading when needed or supporting team members to achieve our collective objectives."
        ],
        
        "problem_solving": [
            f"When facing challenges, I approach them methodically by analyzing the problem, researching solutions, and implementing the most effective approach. My background in {skills_str} has equipped me with strong analytical and problem-solving skills.",
            f"My problem-solving approach combines analytical thinking with creativity. I first thoroughly understand the issue, then develop multiple potential solutions, evaluate them systematically, and implement the best option with careful monitoring of results.",
            f"I tackle problems by breaking them down into manageable components, prioritizing issues, and addressing them systematically. My experience with {skills_str} has taught me to balance quick tactical solutions with strategic long-term fixes."
        ],
        
        "leadership": [
            f"My leadership style focuses on clear communication, setting achievable goals, and empowering team members. With {experience_years} years of experience, I've learned to adapt my approach based on team dynamics and project requirements.",
            "I lead by example, demonstrating the work ethic and standards I expect from my team. I believe in providing clear direction while giving team members autonomy to apply their expertise, offering support and guidance as needed.",
            "As a leader, I prioritize building trust, fostering open communication, and recognizing individual strengths. I focus on creating an environment where team members feel valued and motivated to contribute their best work."
        ],
        
        "communication": [
            "I pride myself on clear, concise communication tailored to my audience. I'm equally comfortable explaining technical concepts to non-technical stakeholders or discussing detailed specifications with technical teams.",
            "My communication style emphasizes active listening and clear articulation of ideas. I've developed these skills through experience presenting to diverse audiences, from technical teams to executive leadership.",
            "I believe effective communication is fundamental to success in any role. I focus on understanding my audience's needs, organizing information logically, and delivering it in the most accessible and impactful way."
        ],
        
        "career_goals": [
            f"My career goal is to continue developing my expertise in {skills_str} while taking on increasing responsibility. I see this position at {company_name} as an ideal next step that aligns with my long-term professional growth objectives.",
            f"I aim to grow into a role where I can combine my technical expertise in {skills_str} with leadership responsibilities. I'm committed to continuous learning and see this position as an excellent opportunity to advance toward that goal.",
            f"In the next five years, I plan to deepen my expertise in {skills_str} while expanding my knowledge in related areas. I'm looking for a role that offers both challenging work and clear paths for professional advancement."
        ],
        
        "skills_match": [
            f"My expertise in {matching_skills_str} directly aligns with the requirements for this position. Throughout my {experience_years} years of experience, I've applied these skills to deliver successful outcomes in similar contexts.",
            f"I've developed strong proficiency in {matching_skills_str}, which are directly relevant to this role. My {experience_years} years of hands-on experience have given me both depth and breadth of knowledge that I can immediately apply to your projects.",
            f"The skills required for this position—particularly {matching_skills_str}—match my areas of expertise. I've honed these abilities through practical application across various projects during my {experience_years}-year career."
        ],
        
        "relocation": [
            "Yes, I am open to relocation for the right opportunity. I'm flexible and prepared to move to take on this role if selected.",
            "I'm definitely willing to relocate for this position. I see it as an exciting opportunity both professionally and personally.",
            "Relocation is absolutely an option for me. I'm at a point in my life where I can be flexible about my location for the right career opportunity."
        ],
        
        "work_style": [
            "I adapt well to different work environments, whether remote, in-office, or hybrid. I'm self-motivated and organized, which allows me to be productive in any setting while maintaining effective communication with my team.",
            "I thrive in collaborative environments but am equally effective working independently. I value clear communication and regular check-ins regardless of the physical work arrangement, and I'm comfortable with both structured and flexible work styles.",
            "My work style emphasizes organization, proactive communication, and results-oriented focus. I've successfully worked in various arrangements from fully remote to in-office, and can adapt to your company's preferred approach."
        ],
        
        "general": [
            f"Based on my {experience_years} years of experience and background in {skills_str}, I believe I can contribute effectively to this role and team. I'm passionate about delivering quality work and continuously developing my professional skills.",
            f"My combination of technical skills in {skills_str}, {experience_years} years of relevant experience, and strong work ethic make me well-suited for this position. I'm excited about the opportunity to bring my expertise to your team.",
            f"I offer a strong foundation in {skills_str} combined with {experience_years} years of practical experience. I'm committed to excellence in my work and look forward to the possibility of contributing to your team's success."
        ]
    }
    
    # Select a template based on question analysis
    templates = answer_templates.get(question_type, answer_templates["general"])
    
    # If the question needs more detail, prefer longer templates
    if needs_detail:
        # Sort templates by length and prefer longer ones
        sorted_templates = sorted(templates, key=len, reverse=True)
        # Take from the first half of the sorted list (longer templates)
        answer = random.choice(sorted_templates[:max(1, len(sorted_templates)//2)])
    else:
        # For yes/no questions or simpler questions, prefer more direct templates
        if is_yes_no:
            # Try to find templates that start with Yes/No
            yes_no_templates = [t for t in templates if t.startswith("Yes") or t.startswith("No")]
            if yes_no_templates:
                answer = random.choice(yes_no_templates)
            else:
                answer = random.choice(templates)
        else:
            answer = random.choice(templates)
    
    return answer


# Rule-based answer generation (fallback if APIs fail)
def rule_based_answer(question, resume_data):
    """
    Generate answers using rule-based templates based on question type.
    This serves as a fallback when API-based generation fails.
    
    Args:
        question (str): The question text
        resume_data (dict): Dictionary containing resume information
        
    Returns:
        str: Generated answer to the question
    """
    question_lower = question.lower()
    
    # Salary expectations
    if any(term in question_lower for term in ['salary', 'compensation', 'pay', 'wage']):
        return "My salary expectations are flexible and based on the total compensation package, including benefits and growth opportunities. I'm looking for a salary that's competitive for this role in the industry."
    
    # Notice period
    elif any(term in question_lower for term in ['notice period', 'start date', 'when can you start']):
        return "I can start immediately or with two weeks' notice to my current employer."
    
    # Why this company
    elif any(term in question_lower for term in ['why do you want to work', 'why are you interested', 'why this company']):
        return f"I'm particularly interested in this position because it aligns with my skills in {', '.join(resume_data.get('skills', [])[:3])}. I'm impressed by the company's reputation and the opportunity to contribute to meaningful projects."
    
    # Strengths
    elif any(term in question_lower for term in ['strength', 'strengths', 'what are you good at']):
        skills = resume_data.get('skills', [])
        if skills:
            return f"My key strengths include my expertise in {', '.join(skills[:3])}, combined with my {resume_data.get('experience', '3+')} years of experience and strong problem-solving abilities."
        else:
            return "My key strengths include my technical expertise, combined with my problem-solving abilities and attention to detail."
    
    # Weaknesses
    elif any(term in question_lower for term in ['weakness', 'weaknesses', 'areas of improvement']):
        return "I sometimes focus too much on details, but I've been working on balancing thoroughness with efficiency. I've implemented personal systems to help me stay focused on the big picture while maintaining quality."
    
    # Work authorization
    elif any(term in question_lower for term in ['authorized to work', 'work authorization', 'visa', 'sponsorship']):
        return "Yes, I am authorized to work in this country without sponsorship."
    
    # Reason for leaving
    elif any(term in question_lower for term in ['why did you leave', 'reason for leaving']):
        return "I'm seeking new opportunities that offer more growth and challenges that align with my career goals. I'm looking for a role where I can fully utilize my skills and continue to develop professionally."
    
    # Work experience
    elif any(term in question_lower for term in ['experience', 'work history', 'previous jobs']):
        return f"I have {resume_data.get('experience', '3+')} years of experience in my field, working with technologies like {', '.join(resume_data.get('skills', [])[:3])}. I've consistently delivered results and developed expertise in solving complex problems."
    
    # Education
    elif any(term in question_lower for term in ['education', 'degree', 'university', 'college']):
        return f"I have a {resume_data.get('education', 'Bachelor\'s')} degree with a focus on technical subjects relevant to this position. My education has provided me with a strong foundation in the principles and practices needed for this role."
    
    # Achievements
    elif any(term in question_lower for term in ['achievement', 'accomplishment', 'proud of']):
        return f"One of my key achievements was successfully implementing projects using {', '.join(resume_data.get('skills', [])[:2])}. I'm particularly proud of my ability to deliver high-quality work while meeting tight deadlines."
    
    # Team work
    elif any(term in question_lower for term in ['team', 'collaborate', 'work with others']):
        return "I thrive in collaborative environments and enjoy working in teams. I value diverse perspectives and believe effective communication is key to successful teamwork. I'm equally comfortable taking direction or initiative as needed."
    
    # Problem solving
    elif any(term in question_lower for term in ['problem', 'challenge', 'difficult situation']):
        return f"When facing challenges, I approach them methodically by analyzing the problem, researching solutions, and implementing the most effective approach. My background in {', '.join(resume_data.get('skills', [])[:2])} has equipped me with strong analytical and problem-solving skills."
    
    # Default answer
    else:
        return f"Based on my {resume_data.get('experience', '3+')} years of experience and background in {', '.join(resume_data.get('skills', [])[:3])}, I believe I can contribute effectively to this role and team."


# For backward compatibility
def generate_answer_hf(question_text, resume_data, job_description):
    """Legacy function for backward compatibility"""
    return generate_answer(question_text, resume_data, job_description)

# ================ Helper: Extract Question Text ===================
def extract_question_text(field, driver):
    """
    Extract the question text associated with a form field using multiple strategies.
    This function tries various methods to find the question text, including:
    1. Checking aria-label and placeholder attributes
    2. Finding associated <label> elements
    3. Looking at parent/sibling text content
    4. Examining nearby heading elements
    5. Checking for question text in divs near the field
    
    Args:
        field: Selenium WebElement for the form field
        driver: Selenium WebDriver instance
        
    Returns:
        str: The extracted question text or "(Unknown Question)" if not found
    """
    # Strategy 1: Try to get label by 'aria-label', 'placeholder', or 'title'
    label = field.get_attribute('aria-label')
    if label and len(label.strip()) > 3:
        return label.strip()
        
    placeholder = field.get_attribute('placeholder')
    if placeholder and len(placeholder.strip()) > 3:
        return placeholder.strip()
        
    title = field.get_attribute('title')
    if title and len(title.strip()) > 3:
        return title.strip()
    
    # Strategy 2: Try to find <label for=...>
    field_id = field.get_attribute('id')
    if field_id:
        try:
            label_elem = driver.find_element(By.CSS_SELECTOR, f'label[for="{field_id}"]')
            if label_elem and label_elem.text.strip():
                return label_elem.text.strip()
        except Exception:
            pass
    
    # Strategy 3: Try parent element text
    try:
        parent = field.find_element(By.XPATH, './..')
        parent_text = parent.text.strip()
        if parent_text and len(parent_text) < 200:  # Avoid getting huge text blocks
            return parent_text
            
        # Try grandparent if parent text is too short or empty
        if len(parent_text) < 3:
            grandparent = parent.find_element(By.XPATH, './..')
            grandparent_text = grandparent.text.strip()
            if grandparent_text and len(grandparent_text) < 200:
                return grandparent_text
    except Exception:
        pass
    
    # Strategy 4: Look for nearby heading elements
    try:
        # Try to find headings above the field
        script = """
        function findNearestHeading(element) {
            // Check previous siblings
            let sibling = element.previousElementSibling;
            while (sibling) {
                if (sibling.tagName.match(/^H[1-6]$/) || 
                    sibling.classList.contains('question') || 
                    sibling.classList.contains('field-label')) {
                    return sibling.textContent.trim();
                }
                sibling = sibling.previousElementSibling;
            }
            
            // Check parent's previous siblings
            let parent = element.parentElement;
            if (parent) {
                sibling = parent.previousElementSibling;
                while (sibling) {
                    if (sibling.tagName.match(/^H[1-6]$/) || 
                        sibling.classList.contains('question') || 
                        sibling.classList.contains('field-label')) {
                        return sibling.textContent.trim();
                    }
                    sibling = sibling.previousElementSibling;
                }
            }
            
            return null;
        }
        return findNearestHeading(arguments[0]);
        """
        heading_text = driver.execute_script(script, field)
        if heading_text and len(heading_text.strip()) > 3:
            return heading_text.strip()
    except Exception as e:
        print(f"[DEBUG] Error finding nearby headings: {e}")
    
    # Strategy 5: Look for question text in nearby divs with specific classes
    try:
        # Look for elements with classes that might indicate question text
        for class_name in ['question', 'field-label', 'form-label', 'control-label', 'question-text']:
            try:
                # Try to find elements near our field
                elements = driver.find_elements(By.CSS_SELECTOR, f'.{class_name}')
                for element in elements:
                    # Check if this element is near our field (simple heuristic)
                    if abs(element.location['y'] - field.location['y']) < 100:
                        if element.text.strip() and len(element.text.strip()) > 3:
                            return element.text.strip()
            except Exception:
                continue
    except Exception as e:
        print(f"[DEBUG] Error finding question classes: {e}")
    
    # If we still don't have a question, try name attribute as last resort
    field_name = field.get_attribute('name')
    if field_name and '[question]' in field_name.lower():
        # Try to find the question ID and look it up in the page
        import re
        match = re.search(r'\[(\d+)\]', field_name)
        if match:
            question_id = match.group(1)
            try:
                question_elem = driver.find_element(By.CSS_SELECTOR, f'[data-question-id="{question_id}"]')
                if question_elem and question_elem.text.strip():
                    return question_elem.text.strip()
            except Exception:
                pass
    
    # Last resort: return a placeholder with field name if available
    if field_name and len(field_name) > 0:
        return f"Question about {field_name.replace('_', ' ')}"
        
    return "(Unknown Question)"


# ================ Form Filling Main Logic ==============
def auto_fill_form(job_link, extracted_resume_data, resume_file_path):
    driver = create_driver()
    driver.get(job_link)

    time.sleep(5)  # wait for page to load

    all_inputs = driver.find_elements(By.TAG_NAME, "input")
    all_textareas = driver.find_elements(By.TAG_NAME, "textarea")
    all_selects = driver.find_elements(By.TAG_NAME, "select")

    fields = all_inputs + all_textareas + all_selects

    print("\n[DEBUG] Extracted resume data:")
    print(extracted_resume_data)
    print("\n[DEBUG] Detected form fields:")
    for field in fields:
        try:
            print(f"Field: tag={field.tag_name}, name={field.get_attribute('name')}, id={field.get_attribute('id')}, placeholder={field.get_attribute('placeholder')}, aria-label={field.get_attribute('aria-label')}, type={field.get_attribute('type')}")
        except Exception as e:
            print(f"[DEBUG] Could not print field: {e}")

    # Ensure resume_file_path is absolute
    if resume_file_path and not os.path.isabs(resume_file_path):
        resume_file_path = os.path.abspath(resume_file_path)

    # Prepare first and last name if possible
    name = extracted_resume_data.get("Name") or extracted_resume_data.get("name")
    first_name, last_name = "", ""
    if name and isinstance(name, str):
        parts = name.strip().split()
        first_name = parts[0]
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

    # Warn if education/experience missing
    if not extracted_resume_data.get("Education"):
        print("[WARN] Education not found in resume data.")
    if not extracted_resume_data.get("Experience"):
        print("[WARN] Experience not found in resume data.")

    # Pass 1: Fill all fields except file upload
    for field in fields:
        try:
            name_attr = field.get_attribute("name")
            placeholder = field.get_attribute("placeholder")
            label = field.get_attribute("aria-label") or field.get_attribute("id")
            field_type = field.get_attribute("type")

            field_identity = (name_attr or placeholder or label or "").lower()

            if isinstance(field, webdriver.remote.webelement.WebElement):
                matched = False

                # Fill first name
                if name_attr == "job_application[first_name]":
                    force_enable_field(driver, field)
                    safe_send_keys(field, first_name)
                    matched = True
                # Fill last name
                elif name_attr == "job_application[last_name]":
                    force_enable_field(driver, field)
                    safe_send_keys(field, last_name)
                    matched = True
                # Fill email
                elif name_attr == "job_application[email]":
                    force_enable_field(driver, field)
                    safe_send_keys(field, extracted_resume_data.get("Email", ""))
                    matched = True
                # Fill phone
                elif name_attr == "job_application[phone]":
                    force_enable_field(driver, field)
                    safe_send_keys(field, extracted_resume_data.get("Phone", ""))
                    matched = True
                # Otherwise, fallback to previous generic matching
                elif any(key in field_identity for key in ["name", "full name"]):
                    force_enable_field(driver, field)
                    safe_send_keys(field, name or "")
                    matched = True
                elif "email" in field_identity:
                    force_enable_field(driver, field)
                    safe_send_keys(field, extracted_resume_data.get("Email", ""))
                    matched = True
                elif "phone" in field_identity or "mobile" in field_identity:
                    force_enable_field(driver, field)
                    safe_send_keys(field, extracted_resume_data.get("Phone", ""))
                    matched = True
                elif "address" in field_identity:
                    force_enable_field(driver, field)
                    safe_send_keys(field, extracted_resume_data.get("Address", ""))
                    matched = True
                elif "skill" in field_identity:
                    force_enable_field(driver, field)
                    skills = ", ".join(extracted_resume_data.get("Skills", []))
                    safe_send_keys(field, skills)
                    matched = True
                elif "education" in field_identity:
                    force_enable_field(driver, field)
                    safe_send_keys(field, extracted_resume_data.get("Education", ""))
                    matched = True
                elif "experience" in field_identity:
                    force_enable_field(driver, field)
                    safe_send_keys(field, str(extracted_resume_data.get("Experience", "")))
                    matched = True

                if matched:
                    print(f"✅ Filled field: {field_identity}")

            # Dropdowns (select)
            if field.tag_name == "select":
                options = field.find_elements(By.TAG_NAME, "option")
                for option in options:
                    if "bachelor" in option.text.lower() and "bachelor" in extracted_resume_data.get("Education", "").lower():
                        option.click()
                        break
                    elif "master" in option.text.lower() and "master" in extracted_resume_data.get("Education", "").lower():
                        option.click()
                        break
                    elif "phd" in option.text.lower() and "phd" in extracted_resume_data.get("Education", "").lower():
                        option.click()
                        break

        except Exception as e:
            print(f"⚠️ Skipped a field due to error: {e}")

    # Pass 2: Upload resume file LAST
    for field in fields:
        try:
            name_attr = field.get_attribute("name")
            field_type = field.get_attribute("type")
            if field_type == "file" and resume_file_path:
                field.send_keys(resume_file_path)
                print(f"✅ Uploaded resume file: {resume_file_path}")
        except Exception as e:
            print(f"⚠️ Skipped file upload due to error: {e}")

    # Wait for site's JS to parse resume and (possibly) overwrite fields
    time.sleep(5)

    # Re-fetch the fields after upload (site may have replaced elements)
    all_inputs = driver.find_elements(By.TAG_NAME, "input")
    all_textareas = driver.find_elements(By.TAG_NAME, "textarea")
    all_selects = driver.find_elements(By.TAG_NAME, "select")
    fields = all_inputs + all_textareas + all_selects

    # Print debug info for email and phone fields before filling
    for field in fields:
        name_attr = field.get_attribute("name")
        if name_attr in ["job_application[email]", "job_application[phone]"]:
            debug_field_state(field, label="Before fill")

    # Force-fill email and phone fields before the normal re-fill pass
    for field in fields:
        name_attr = field.get_attribute("name")
        if name_attr == "job_application[email]":
            force_enable_field(driver, field)
            force_fill_field_js(driver, field, extracted_resume_data.get("Email", ""), label="email")
            debug_field_state(field, label="After force fill (email)")
        if name_attr == "job_application[phone]":
            force_enable_field(driver, field)
            force_fill_field_js(driver, field, extracted_resume_data.get("Phone", ""), label="phone")
            debug_field_state(field, label="After force fill (phone)")

    # --- SMART AI QUESTION ANSWERING ---
    # Find all custom question fields
    print("\n[INFO] 🧠 Looking for application questions to answer...")
    question_fields = []
    
    # First pass: identify all question fields
    for field in fields:
        name_attr = field.get_attribute("name")
        field_type = field.get_attribute("type")
        
        # Skip hidden fields and submit buttons
        if field_type in ["hidden", "submit", "button", "file"]:
            continue
            
        # Common patterns for question fields
        is_question_field = False
        
        # Pattern 1: Common job application platforms (Greenhouse, Lever, etc)
        if name_attr and any(pattern in name_attr for pattern in [
            "job_application[answers_attributes]", 
            "question",
            "answers",
            "custom_fields"
        ]):
            is_question_field = True
            
        # Pattern 2: Textarea fields are often for questions
        if field.tag_name == "textarea" and not any(key in (name_attr or "").lower() for key in [
            "address", "summary", "cover", "letter", "resume", "cv"
        ]):
            is_question_field = True
            
        # Pattern 3: Text inputs with certain classes or patterns
        if field_type == "text" and not any(key in (name_attr or "").lower() for key in [
            "name", "email", "phone", "address", "city", "state", "zip", "postal"
        ]):
            # Check if this might be a question field based on nearby elements
            question_text = extract_question_text(field, driver)
            if question_text and question_text != "(Unknown Question)" and len(question_text) > 10:
                # If the extracted text looks like a question, treat it as one
                if any(q_word in question_text.lower() for q_word in ["?", "explain", "describe", "tell us", "why", "how", "what", "when"]):
                    is_question_field = True
        
        if is_question_field:
            question_fields.append(field)
    
    # Second pass: extract questions and generate answers
    if question_fields:
        print(f"\n[INFO] ✅ Found {len(question_fields)} questions to answer")
        
        # Try to get job description text if possible
        job_description_text = None
        try:
            from job_description_extractor import extract_job_description
            job_data = extract_job_description(job_link)
            job_description_text = job_data
        except Exception as e:
            print(f"[DEBUG] Could not extract job description: {e}")
            job_description_text = job_link
        
        for i, field in enumerate(question_fields):
            try:
                question_text = extract_question_text(field, driver)
                print(f"\n[INFO] 📝 Question {i+1}: '{question_text}'")
                
                # Generate answer using AI
                answer = generate_answer(question_text, extracted_resume_data, job_description_text)
                print(f"[INFO] 🤖 Answer: '{answer[:50]}...'")
                
                # Fill the field with the generated answer
                force_enable_field(driver, field)
                force_fill_field_js(driver, field, answer, label=f"Question {i+1}")
                
                # Verify the field was filled
                time.sleep(0.5)
                current_value = field.get_attribute("value")
                if not current_value or len(current_value) < 5:
                    print(f"[WARN] ⚠️ Field may not have been filled properly. Retrying...")
                    # Try alternative method
                    driver.execute_script(
                        "arguments[0].value = arguments[1]; "
                        "arguments[0].dispatchEvent(new Event('input')); "
                        "arguments[0].dispatchEvent(new Event('change')); "
                        "arguments[0].dispatchEvent(new Event('blur'));", 
                        field, answer
                    )
                else:
                    print(f"[INFO] ✅ Successfully filled answer for question {i+1}")
            except Exception as e:
                print(f"[ERROR] ❌ Failed to answer question: {e}")
    else:
        print("\n[INFO] ℹ️ No application questions detected")

    # Pass 3: Re-fill all fields again (except file upload)
    for field in fields:
        try:
            name_attr = field.get_attribute("name")
            placeholder = field.get_attribute("placeholder")
            label = field.get_attribute("aria-label") or field.get_attribute("id")
            field_type = field.get_attribute("type")
            field_identity = (name_attr or placeholder or label or "").lower()

            if isinstance(field, webdriver.remote.webelement.WebElement):
                matched = False
                # Special handling for email/phone: try all matching fields
                if name_attr == "job_application[email]":
                    force_enable_field(driver, field)
                    safe_send_keys(field, extracted_resume_data.get("Email", ""))
                    if not field.get_attribute("value"):
                        js_set_value(driver, field, extracted_resume_data.get("Email", ""))
                    debug_field_state(field, label="After fill (email)")
                    # Try all fields with this name
                    for f in fields:
                        if f.get_attribute("name") == "job_application[email]" and f != field:
                            force_enable_field(driver, f)
                            js_set_value(driver, f, extracted_resume_data.get("Email", ""))
                            debug_field_state(f, label="After fill (email, other)")
                    matched = True
                elif name_attr == "job_application[phone]":
                    force_enable_field(driver, field)
                    safe_send_keys(field, extracted_resume_data.get("Phone", ""))
                    if not field.get_attribute("value"):
                        js_set_value(driver, field, extracted_resume_data.get("Phone", ""))
                    debug_field_state(field, label="After fill (phone)")
                    for f in fields:
                        if f.get_attribute("name") == "job_application[phone]" and f != field:
                            force_enable_field(driver, f)
                            js_set_value(driver, f, extracted_resume_data.get("Phone", ""))
                            debug_field_state(f, label="After fill (phone, other)")
                    matched = True
                elif name_attr == "job_application[first_name]":
                    force_enable_field(driver, field)
                    safe_send_keys(field, first_name)
                    matched = True
                elif name_attr == "job_application[last_name]":
                    force_enable_field(driver, field)
                    safe_send_keys(field, last_name)
                    matched = True
                elif any(key in field_identity for key in ["name", "full name"]):
                    force_enable_field(driver, field)
                    safe_send_keys(field, name or "")
                    matched = True
                elif "email" in field_identity:
                    force_enable_field(driver, field)
                    safe_send_keys(field, extracted_resume_data.get("Email", ""))
                    if not field.get_attribute("value"):
                        js_set_value(driver, field, extracted_resume_data.get("Email", ""))
                    matched = True
                elif "phone" in field_identity or "mobile" in field_identity:
                    force_enable_field(driver, field)
                    safe_send_keys(field, extracted_resume_data.get("Phone", ""))
                    if not field.get_attribute("value"):
                        js_set_value(driver, field, extracted_resume_data.get("Phone", ""))
                    matched = True
                elif "address" in field_identity:
                    force_enable_field(driver, field)
                    safe_send_keys(field, extracted_resume_data.get("Address", ""))
                    matched = True
                elif "skill" in field_identity:
                    force_enable_field(driver, field)
                    skills = ", ".join(extracted_resume_data.get("Skills", []))
                    safe_send_keys(field, skills)
                    matched = True
                elif "education" in field_identity:
                    force_enable_field(driver, field)
                    safe_send_keys(field, extracted_resume_data.get("Education", ""))
                    matched = True
                elif "experience" in field_identity:
                    force_enable_field(driver, field)
                    safe_send_keys(field, str(extracted_resume_data.get("Experience", "")))
                    matched = True
                if matched:
                    print(f"✅ Re-filled field: {field_identity}")
            if field.tag_name == "select":
                options = field.find_elements(By.TAG_NAME, "option")
                for option in options:
                    if "bachelor" in option.text.lower() and "bachelor" in extracted_resume_data.get("Education", "").lower():
                        option.click()
                        break
                    elif "master" in option.text.lower() and "master" in extracted_resume_data.get("Education", "").lower():
                        option.click()
                        break
                    elif "phd" in option.text.lower() and "phd" in extracted_resume_data.get("Education", "").lower():
                        option.click()
                        break
        except Exception as e:
            print(f"⚠️ Skipped a field (re-fill) due to error: {e}")

    print("\n🎯 Form filling attempt finished!\n")
    time.sleep(10)  # Pause so you can check form
    driver.quit()


# ================ Example Usage ========================
if __name__ == "__main__":
    job_link = input("🔗 Enter Job Application Link: ")

    # Example extracted data (normally you'll pass from resume_extraction.py)
    extracted_resume_data = {
        "Name": "John Doe",
        "Email": "john.doe@example.com",
        "Phone": "+1234567890",
        "Address": "New York, USA",
        "Skills": ["Python", "Machine Learning", "Deep Learning"],
        "Education": "Masters",
        "Experience": 3
    }

    resume_file_path = "path_to_your_resume.pdf"  # Update this!

    auto_fill_form(job_link, extracted_resume_data, resume_file_path)
