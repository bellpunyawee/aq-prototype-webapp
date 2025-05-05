import os
import requests
from dotenv import load_dotenv

load_dotenv()
canvas_api_key = os.getenv('CANVAS_API_KEY')
# canvas_api_key = os.getenv('canvas_api_key_to_create_overrides')
base_url = 'https://canvas.nus.edu.sg/api/v1/courses'

headers = {
    'Authorization': f'Bearer {canvas_api_key}'
}

def get_all_pages(url):
    """Fetch all pages of a paginated Canvas API response."""
    items = []
    while url:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        items.extend(response.json())
        links = response.headers.get('Link', '')
        url = None
        for link in links.split(','):
            if 'rel="next"' in link:
                url = link[link.find("<")+1:link.find(">")]
    return items

def get_grades(course_id, assignment_id):
    url = f'{base_url}/{course_id}/assignments/{assignment_id}/submissions'
    return get_all_pages(url)

def check_all_assignments_completed(course_id, assignment_id_list, student_id):
    # """Check if a specific student has completed all assignments in the provided list."""
    # completed_assignment_ids = []
    
    # for assignment_id in assignment_id_list:
    #     submissions = get_grades(course_id, assignment_id)
        
    #     # Check if the specified student has completed the assignment
    #     for submission in submissions:
    #         if submission['user_id'] == int(student_id):
    #             grade = submission.get('grade')
    #             if grade is not None:
    #                 completed_assignment_ids.append(assignment_id)
    #             break 

    # # Compare completed assignment IDs with input assignment IDs (Hardcode)
    # print(set(completed_assignment_ids))
    completed_assignment_ids = []
    
    for assignment_id in assignment_id_list:
        submissions = get_grades(course_id, assignment_id)

        # Check if the specified student has submitted the assignment
        for submission in submissions:
            if submission['user_id'] == int(student_id):
                # Check submission status and other relevant fields
                workflow_state = submission.get('workflow_state')  # e.g., 'submitted', 'graded', 'pending_review'
                submitted_at = submission.get('submitted_at')  # Timestamp of submission
                attempt = submission.get('attempt', 0)  # Number of attempts, default to 0 if None
                grade_match = submission.get('grade_matches_current_submission')

                # Consider the assignment completed if it is submitted, attempted, or marked as done
                # mark as done cannot catch, but assignment_id_list involves all assignment, they must submit quizzes!
                if (workflow_state in ['submitted','graded', 'pending_review'] or 
                    submitted_at is not None or 
                    (attempt and attempt > 0) ) or grade_match == True:
                    completed_assignment_ids.append(assignment_id)
                break

    # Print completed assignment IDs and compare with the input list
    # print(f"Completed Assignments for Student {student_id}: {set(completed_assignment_ids)}")
    # print(f"Assignments List {student_id}: {set(assignment_id_list)})")
    
    # Check if all assignments in the list are completed
    return set(completed_assignment_ids) == set(assignment_id_list)

def check_to_unlock_all_modules(course_id, assignment_id_list, student_id):
    """Check if a specific student has completed post-test."""
    completed_assignment_ids = []
    
    for assignment_id in assignment_id_list:
        submissions = get_grades(course_id, assignment_id)
        
        # Check if the specified student has completed the assignment
        for submission in submissions:
            if submission['user_id'] == int(student_id):
                grade = submission.get('grade')
                if grade is not None:
                    completed_assignment_ids.append(assignment_id)
                break 

    # Compare completed assignment IDs with input assignment IDs (Hardcode)
    return set(completed_assignment_ids) == {159913}

if __name__ == '__main__':
    assignment_ids = [149331, 149332, 149333, 149334, 149385, 149391, 149384, 149388]  
    course_id = '73870'  # Replace with your course ID
    canvas_student_id = '156282'  # Replace with the actual student ID
    all_assignments_completed = check_all_assignments_completed(course_id, assignment_ids, canvas_student_id)
    print("All assignments completed:", all_assignments_completed)
