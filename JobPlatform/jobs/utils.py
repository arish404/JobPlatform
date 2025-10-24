from PyPDF2 import PdfReader

def parse_resume_and_calculate_score(resume_file, job_keywords):
    """
    Parses a resume PDF and calculates a score based on job keywords.
    :param resume_file: Uploaded resume file
    :param job_keywords: List of keywords for the job
    :return: Resume score (float)
    """
    try:
        # Extract text from the PDF resume
        reader = PdfReader(resume_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()

        # Calculate the score based on keyword matches
        text = text.lower()
        keywords_matched = sum(1 for keyword in job_keywords if keyword.lower() in text)
        total_keywords = len(job_keywords)

        score = (keywords_matched / total_keywords) * 100 if total_keywords > 0 else 0
        return score
    except Exception as e:
        print(f"Error parsing resume: {e}")
        return 0.0
