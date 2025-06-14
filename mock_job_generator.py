"""
Mock Job Generator Module for Berojgar

This module generates mock job listings for demonstration purposes.
It's used as a fallback when the job_scraper module dependencies are missing.
"""

import random
import time
from datetime import datetime

def generate_mock_jobs(query, location="", resume_data=None, limit=20):
    """
    Generate mock job listings based on user input
    
    Args:
        query (str): Job search query
        location (str): Location for job search
        resume_data (dict): Resume data including skills
        limit (int): Maximum number of jobs to return
        
    Returns:
        list: List of job dictionaries
    """
    jobs = []
    sources = ["Indeed", "LinkedIn", "GitHub", "Google Jobs", "RSS Feeds"]
    
    # Normalize query and location
    query = query.strip() if query else "Software Developer"
    location = location.strip() if location else "Remote"
    
    # Get resume skills if available
    resume_skills = []
    if resume_data and 'skills' in resume_data:
        resume_skills = [skill.lower() for skill in resume_data['skills']]
    
    # Generate mock jobs
    for i in range(min(limit, 20)):
        # Randomize job attributes
        source = sources[i % len(sources)]
        job_type = ["Full-time", "Part-time", "Contract", "Temporary", "Internship"][i % 5]
        posted_days_ago = random.randint(1, 14)
        posted_date = datetime.now().timestamp() - (posted_days_ago * 86400)
        
        # Generate a job title based on the query
        if query.lower() in ["python", "javascript", "java", "c++", "ruby", "php"]:
            title = f"{query.title()} {['Developer', 'Engineer', 'Programmer', 'Architect', 'Specialist'][i % 5]}"
        elif "data" in query.lower():
            title = f"Data {['Scientist', 'Analyst', 'Engineer', 'Architect', 'Specialist'][i % 5]}"
        elif "manager" in query.lower() or "management" in query.lower():
            title = f"{['Project', 'Product', 'Program', 'Technical', 'Engineering'][i % 5]} Manager"
        else:
            title = f"{query.title()} {['Specialist', 'Professional', 'Expert', 'Consultant', 'Analyst'][i % 5]}"
        
        # Generate company name
        companies = [
            "TechCorp", "InnovateTech", "DataDriven", "CodeMasters", "SoftSolutions",
            "GlobalTech", "FutureSoft", "InnovateNow", "TechGiants", "DataPros",
            "OpenSource", "GitMasters", "CodeCollab", "DevOps", "TechStack",
            "Alphabet", "SearchTech", "DataInnovators", "CloudComputing", "AIExperts"
        ]
        company = f"{companies[i % len(companies)]}"
        
        # Generate job description
        description = f"We are looking for a skilled {query} professional to join our team. The ideal candidate will have experience with modern technologies and a passion for creating high-quality solutions. You will work on challenging projects that make a real impact."
        
        # Generate skills
        tech_skills = {
            "python": ["Python", "Django", "Flask", "Pandas", "NumPy", "PyTorch", "TensorFlow"],
            "javascript": ["JavaScript", "React", "Node.js", "Express", "Vue.js", "Angular", "TypeScript"],
            "java": ["Java", "Spring", "Hibernate", "Maven", "JUnit", "Microservices"],
            "data": ["SQL", "Data Analysis", "Data Visualization", "Power BI", "Tableau", "Big Data"],
            "machine learning": ["Machine Learning", "Deep Learning", "NLP", "Computer Vision", "AI", "Data Science"],
            "web": ["HTML", "CSS", "JavaScript", "Responsive Design", "Web Development", "Frontend"],
            "backend": ["API Development", "Database Design", "Server Management", "Microservices"],
            "devops": ["Docker", "Kubernetes", "CI/CD", "AWS", "Azure", "GCP", "Infrastructure as Code"],
            "mobile": ["iOS", "Android", "React Native", "Flutter", "Mobile Development"],
            "cloud": ["AWS", "Azure", "GCP", "Cloud Architecture", "Serverless"],
            "database": ["SQL", "NoSQL", "MongoDB", "PostgreSQL", "MySQL", "Database Design"],
            "security": ["Cybersecurity", "Penetration Testing", "Security Auditing", "Encryption"],
            "project": ["Project Management", "Agile", "Scrum", "Jira", "Kanban"],
            "ui": ["UI Design", "UX Design", "Figma", "Adobe XD", "Sketch"],
            "testing": ["QA", "Test Automation", "Selenium", "JUnit", "TestNG", "Quality Assurance"]
        }
        
        # Determine relevant skill categories based on the query
        relevant_categories = []
        for category in tech_skills:
            if category in query.lower():
                relevant_categories.append(category)
        
        # If no specific categories found, add some general tech categories
        if not relevant_categories:
            if "developer" in query.lower() or "engineer" in query.lower():
                relevant_categories = ["python", "javascript", "java"]
            elif "data" in query.lower() or "analyst" in query.lower():
                relevant_categories = ["data", "database", "python"]
            elif "manager" in query.lower() or "lead" in query.lower():
                relevant_categories = ["project", "devops", "cloud"]
            else:
                relevant_categories = ["web", "python", "javascript"]
        
        # Collect skills from relevant categories
        base_skills = ["Communication", "Problem Solving", "Teamwork", "Time Management"]
        skills = base_skills.copy()
        for category in relevant_categories:
            skills.extend(tech_skills[category][:3])  # Add top 3 skills from each category
        
        # Remove duplicates and shuffle
        unique_skills = list(set(skills))
        random.shuffle(unique_skills)
        job_skills = unique_skills[:8]  # Return up to 8 skills
        
        # Generate requirements
        requirements = [
            f"{random.randint(1, 5)}+ years of experience in {query}",
            "Bachelor's degree in Computer Science or related field",
            "Strong problem-solving skills",
            "Excellent communication abilities"
        ]
        
        # Generate salary range
        min_salary = random.randint(50, 120)
        max_salary = min_salary + random.randint(20, 60)
        salary = f"${min_salary}k - ${max_salary}k"
        
        # Calculate match score if resume skills are provided
        if resume_skills:
            job_skills_lower = [skill.lower() for skill in job_skills]
            matching_skills = set(resume_skills).intersection(set(job_skills_lower))
            
            # Calculate match percentage
            if job_skills:
                match_percentage = (len(matching_skills) / len(job_skills)) * 100
            else:
                match_percentage = 50  # Default score if no job skills
            
            # Add some randomness to make it more realistic
            match_percentage = match_percentage + random.uniform(-10, 10)
            
            # Ensure the score is between 0 and 100
            match_percentage = max(0, min(100, match_percentage))
            
            match_score = int(match_percentage)
            matching_skills_list = list(matching_skills)
        else:
            # If no resume skills provided, assign random match scores
            match_score = random.randint(50, 95)
            matching_skills_list = []
        
        # Create job object with a proper Google search URL for all job titles
        title_slug = title.replace(' ', '+')
        company_slug = company.replace(' ', '+')
        google_search_url = f"https://www.google.com/search?q={title_slug}+{company_slug}+job+apply"
        
        job = {
            "id": f"{source.lower().replace(' ', '_')}_{i}_{int(time.time())}",
            "title": title,
            "company": company,
            "location": location,
            "description": description,
            "url": google_search_url,
            "application_url": google_search_url,  # Add application URL that matches the URL
            "source": source,
            "job_type": job_type,
            "salary": salary,
            "posted_date": f"{posted_days_ago} days ago",
            "posted_date_timestamp": posted_date,
            "requirements": requirements,
            "skills": job_skills,
            "match_score": match_score,
            "matching_skills": matching_skills_list
        }
        
        jobs.append(job)
    
    # Sort by match score (highest first)
    jobs.sort(key=lambda x: x['match_score'], reverse=True)
    
    return jobs

def get_mock_job_details(job_id):
    """
    Get detailed information for a specific job
    
    Args:
        job_id (str): ID of the job
        
    Returns:
        dict: Job details
    """
    # Parse job source and index from the ID
    parts = job_id.split('_')
    if len(parts) < 2:
        return None
    
    source = parts[0]
    index = int(parts[1]) if parts[1].isdigit() else 0
    
    # Generate a mock job with more details
    job = generate_mock_jobs("", "", None, 1)[0]
    
    # Update job with specific details based on the ID
    job["id"] = job_id
    
    if source == "indeed":
        job["source"] = "Indeed"
        job["company"] = f"Indeed Company {index}"
    elif source == "linkedin":
        job["source"] = "LinkedIn"
        job["company"] = f"LinkedIn Corporation {index}"
    elif source == "github":
        job["source"] = "GitHub"
        job["company"] = f"GitHub Enterprise {index}"
    elif source == "google":
        job["source"] = "Google Jobs"
        job["company"] = f"Google Workplace {index}"
    elif source == "rss":
        job["source"] = "RSS Feeds"
        job["company"] = f"RSS Network {index}"
    
    # Add more detailed description
    job["description"] = f"""
    {job["company"]} is seeking a talented {job["title"]} to join our growing team.
    
    About Us:
    We are a leading technology company specializing in innovative solutions for businesses of all sizes. Our team is dedicated to creating high-quality products that make a difference.
    
    Job Description:
    As a {job["title"]}, you will be responsible for designing, developing, and maintaining software applications. You will work closely with cross-functional teams to deliver exceptional results.
    
    Responsibilities:
    - Design and develop high-quality software solutions
    - Collaborate with product managers and designers to understand requirements
    - Write clean, maintainable, and efficient code
    - Troubleshoot and fix bugs in existing applications
    - Participate in code reviews and provide constructive feedback
    - Stay up-to-date with emerging trends and technologies
    
    We offer:
    - Competitive salary: {job["salary"]}
    - Flexible work arrangements
    - Comprehensive health benefits
    - Professional development opportunities
    - Collaborative and inclusive work environment
    
    Join our team and be part of something amazing!
    """
    
    # Create proper Google search URL for job application
    title_slug = job["title"].replace(' ', '+')
    company_slug = job["company"].replace(' ', '+')
    google_search_url = f"https://www.google.com/search?q={title_slug}+{company_slug}+job+apply"
    
    # Add proper URLs
    job["url"] = google_search_url
    job["application_url"] = google_search_url
    
    return job

# Example usage
if __name__ == "__main__":
    # Test the mock job generator
    jobs = generate_mock_jobs("python developer", "New York", limit=5)
    
    print(f"Found {len(jobs)} jobs")
    for job in jobs:
        print(f"\nTitle: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Match Score: {job['match_score']}%")
        print(f"Skills: {', '.join(job['skills'])}")
    
    # Test job details
    job_details = get_mock_job_details("indeed_1_1234567890")
    if job_details:
        print(f"\n\nJob Details:")
        print(f"Title: {job_details['title']}")
        print(f"Company: {job_details['company']}")
        print(f"Source: {job_details['source']}")
