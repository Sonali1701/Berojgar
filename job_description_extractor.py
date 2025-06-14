# job_description_extractor.py
import requests
from bs4 import BeautifulSoup


def extract_job_description(url):
    # Initialize a dictionary to store the job description and other details
    data = {
        'description': '',  # Added 'description' key
        'Required_Skills': [],
        'Min_Experience': 0,
        'Preferred_Education': '',
        'Role': 'Unknown'
    }

    try:
        # Send a GET request to fetch the HTML content of the job listing page
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text(separator=' ').lower()  # Get the whole text from the page

            # Skill keywords to look for in the job description
            skill_keywords = ['python', 'java', 'sql', 'machine learning', 'deep learning', 'nlp', 'data analysis',
                              'aws', 'docker']
            education_levels = ['bachelor', 'master', 'phd']
            job_roles = ['data scientist', 'ml engineer', 'software developer', 'data analyst']

            # Extract skills mentioned in the job description
            data['Required_Skills'] = [skill.title() for skill in skill_keywords if skill in text]

            # Extract the minimum experience required from the job description (e.g., '3+ years')
            import re
            exp_matches = re.findall(r'(\d+)\+?\s+years', text)
            if exp_matches:
                data['Min_Experience'] = max([int(num) for num in exp_matches])  # Max years if multiple matches

            # Extract the preferred education level (bachelor, master, phd)
            for edu in education_levels:
                if edu in text:
                    data['Preferred_Education'] = edu.title()
                    break

            # Extract the job role (data scientist, ML engineer, etc.)
            for role in job_roles:
                if role in text:
                    data['Role'] = role.title()
                    break

            # Assign the full job description text (for analysis)
            data['description'] = text

        else:
            print("❌ Failed to fetch job description!")

    except Exception as e:
        print(f"❌ Error extracting job description: {e}")

    return data
