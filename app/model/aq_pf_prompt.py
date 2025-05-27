import sys,os,requests
import pandas as pd
from pinecone import Pinecone
from datetime import datetime
# import openai
from openai import OpenAI
#from canvasapi import Canvas




# class CanvasAPI:
#     def __init__(self, api_url, api_key):
#         self.canvas = Canvas(api_url, api_key)

#     def create_conversation(self, recipients, subject, body, force_new=True, group_conversation=False, mode='sync'):
#         """
#         Create a new conversation or message in Canvas.

#         :param recipients: List of recipient ids (strings).
#         :param subject: Subject of the message.
#         :param body: Body of the message.
#         :param force_new: Forces creation of a new conversation.
#         :param group_conversation: Set to True for group conversations.
#         :param mode: 'sync' or 'async' operation.
#         """
#         # Prepare the data for the POST request
#         conversation_data = {
#             'recipients': recipients,
#             'subject': subject,
#             'body': body,
#             'force_new': force_new,
#             'group_conversation': group_conversation,
#             'mode': mode
#         }

#         # # base_url = 'https://nus-dev.instructure.com'
#         # base_url = 'https://canvas.nus.edu.sg'
#         # access_token = os.getenv('CANVAS_PROD_KEY')
#         # url =  f"{base_url}/api/v1/conversations"
    
#         # headers = {
#         # 'Authorization': f'Bearer {access_token}',
#         # 'Content-Type': 'application/json'
#         # }

#         # response = requests.post(url, json=conversation_data, headers=headers)

#         return self.canvas.create_conversation(**conversation_data)


def call_gpt(input_text):
    api_key = os.getenv('OPENAI_API_KEY')
    client = OpenAI(api_key=api_key) # TODO fill in your own key
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": input_text}],
        model='chatgpt-4o-latest',
        stream=False
    )
    output = chat_completion.choices[0].message.content
    return output


def load_and_process_log(user_log, processed_records_file):
    # Try to load previously processed records or create an empty DataFrame with the correct column if it fails
    try:
        processed_records = pd.read_csv(processed_records_file)
        if 'user_id' not in processed_records.columns or 'n_attempt' not in processed_records.columns:
            processed_records = pd.DataFrame(columns=['user_id', 'n_attempt'])
    except FileNotFoundError:
        processed_records = pd.DataFrame(columns=['user_id', 'n_attempt'])

    # Load user log and prepare unique identifier
    # user_log = pd.read_csv(user_log, encoding="utf-8")

    user_log = pd.read_excel(user_log) # <--- Task 1: 'user_log' reading from database itself?
    user_log = user_log[user_log['username'] != "no data"]
    user_log['unique_id_attempt'] = user_log['user_id'].astype(str) + "_" + user_log['n_attempt'].astype(str)

    # Filter out already processed records
    unique_checks = set(processed_records['user_id'].astype(str) + "_" + processed_records['n_attempt'].astype(str))
    user_log = user_log[~user_log['unique_id_attempt'].isin(unique_checks)]

    # Filter user_log to retain only records with exactly 10 occurrences per user_id and n_attempt combination
    # len(x) is the number of questions --> generalise to any number of questions
    valid_combinations = user_log.groupby(['user_id', 'n_attempt']).filter(lambda x: len(x) == len(user_log))

    # If no valid combinations are found, halt the process
    if valid_combinations.empty:
        # print("No valid records found with exactly 10 attempts.")
        sys.exit()

    # Append new processed records to the processed_records DataFrame and save
    new_processed = valid_combinations[['user_id', 'n_attempt']].drop_duplicates()
    processed_records = pd.concat([processed_records, new_processed], ignore_index=True)
    processed_records.to_csv(os.path.join('_cache',processed_records_file), index=False)

    # Sort and return valid_combinations, removing temporary columns
    return valid_combinations.sort_values(by=['n_attempt', 'id']).drop(columns=['unique_id_attempt'])


# def load_quiz_bank(file_path):
#     return pd.read_excel(file_path, sheet_name='Overview') # <--- Task 2: read from SQL?


def merge_data(user_log, canvas_mapping):
    return pd.merge(user_log, canvas_mapping, left_on='username', right_on='username', how='left') # <--- Task 3: Mostly done on Pandas, switch to manipulate in SQL?


def check_quiz_name(n_attempt, name):
    """
    Returns the quiz name based on the attempt number.

    - For n_attempt == 1, returns "Baseline Quiz"
    - For n_attempt >= 2, returns "Quiz {n_attempt - 1}"
    - For n_attempt < 1, returns "Invalid attempt number"

    Args:
        n_attempt (int): The attempt number.

    Returns:
        str: The name of the quiz corresponding to the attempt number.
    """
    if n_attempt < 1:
        return "Invalid attempt number"
    elif n_attempt == 1:
        return "Baseline Quiz"
        # if name == 'Post-quiz':
        #     return "Post-quiz"
        # else:
        #     return "Baseline Quiz"
    else:
        if name == 'Post-quiz':
            return "Post-quiz"
        else:
            return f"Quiz {n_attempt - 1}"

def generate_feedback(merged_data, user_id, attempt):
    data = merged_data[(merged_data['user_id'] == user_id) & (merged_data['n_attempt'] == attempt)]
    if data.empty:
        return "No data available for this user and attempt."

    feedback_prompt = "\nQuiz Details and Student Responses:\n"
    # Iterate over each question response and build the feedback
    for idx, row in data.iterrows():
        # Determine the student's response status
        response_status = 'correct' if row['answer_correct'] == 1 else 'wrong'
        # Get the rationale or indicate it's empty
        rationale = row['explanation'] if not pd.isna(row['explanation']) else "No explanation provided."

        # Append individual question feedback
        feedback_prompt += (f"Question: {row['question_text']}\n"
                            f"Correct answer: {row['correct_answer']}\n"
                            f"The student answered {row['answer_text']} and it was {response_status}.\n"
                            f"Rationale: {rationale}\n\n")

    # Add summary of the quiz performance
    correct_count = data['answer_correct'].sum()
    incorrect_count = len(data) - correct_count
    feedback_prompt += (f"In total, the student answered {correct_count} questions correctly "
                        f"and {incorrect_count} questions incorrectly out of {len(data)} questions.\n")

    return feedback_prompt


#! for course learning objective & instruction for feedback
def append_los_text(feedback_prompt, learner_description):
    with open('docs/los.txt', 'r', encoding='utf-8') as file: # Learning objective
        los_text = file.read()
    with open('docs/request.txt', 'r', encoding='utf-8') as file: # Feedback Generation Request
        request_text = file.read()
    return request_text + "\n" + learner_description + "\n" + feedback_prompt + "\n" + los_text


def get_datetime_suffix():
    # Generates a string suffix for the filename based on the current datetime
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def get_context(query):
    openai_key = os.getenv('OPENAI_API_KEY')
    pinecone = os.getenv('PINECONE_API_KEY')
    client = OpenAI(api_key=openai_key) # Please fill in
    pc = Pinecone(api_key=pinecone) # Please fill in
    # Initialize Pinecone Index
    index = pc.Index("qe2-learning-materials") # for QE2
    # Get embeddings from OpenAI
    embedding_response = client.embeddings.create(input=query, model="text-embedding-3-small")
    query_vector = embedding_response.data[0].embedding
    # print(f"query_vector is: {query_vector}")
    # Query Pinecone with the embedding
    response = index.query(namespace="qe2", vector=query_vector, top_k=10, include_metadata=True) # for QE2
    # print(f"response is: {response}")
    context_docs = [match['metadata']['text'] for match in response['matches']]
    # print(f"context_docs is: {context_docs}")
    # Return the context documents concatenated into a single string
    return "\n\nPM Knowledge for reference:\n" + "\n\n".join(context_docs)


def append_learner_description(learner_info, student_id):
    """Appends a description of the learner based on the learner information DataFrame."""
    # Filter the learner information for the specific student ID
    learner_row = learner_info[learner_info['Email Address'] == student_id]
    if not learner_row.empty:
        description = (
            f"Gender: {learner_row['Gender'].iloc[0]}, "
            f"Role: {learner_row['Role'].iloc[0]}, "
            f"Job Title: {learner_row['Job Title'].iloc[0]}, "
            f"Experience: {learner_row['Years of Experience in Construction Industry'].iloc[0]}, "
            f"Projects Managed: {learner_row['How many projects have you managed or been heavily involved in?'].iloc[0]}, "
            f"Qualification: {learner_row['Highest Qualification'].iloc[0]}, "
            f"Discipline: {learner_row['Discipline / Major of Highest Qualification'].iloc[0]}."
        )
    else:
        description = "No additional learner information available."
    return description


def apply_text_styles(doc, text):
    """Applies text styles based on markdown-like annotations in the text."""
    lines = text.split('\n\n')
    for line in lines:
        if line.startswith('**') and line.endswith('**'):
            # Remove the markdown style and create a formatted heading
            line = line.strip('**')
            doc.add_heading(line, level=2)
        else:
            doc.add_paragraph(line)

# Previous version /wo error handling
def process_feedback_for_all_students(merged_data, canvas_api, name):
    # Get unique combinations of student id and attempt numbers
    unique_students_attempts = merged_data[['user_id', 'n_attempt']].drop_duplicates()

    # Iterate over each student and attempt to generate feedback
    for _, row in unique_students_attempts.iterrows():
        student_id = row['user_id']
        attempt = row['n_attempt']
        # Extract student's name
        student_name = \
            merged_data[(merged_data['user_id'] == student_id) & (merged_data['n_attempt'] == attempt)]['name'].iloc[0]
        student_sis_id = \
            merged_data[(merged_data['user_id'] == student_id) & (merged_data['n_attempt'] == attempt)]['sis_id'].iloc[
                0]
        canvas_id = \
            merged_data[(merged_data['user_id'] == student_id) & (merged_data['n_attempt'] == attempt)][
                'canvas_id'].iloc[
                0]

        feedback = generate_feedback(merged_data, student_id, attempt)
        # Get contextual information from Pinecone how to access Pinecone?
        context = get_context(feedback)

        learner_info = pd.read_excel('docs/Sign Up List.xlsx', sheet_name='Compiled') # parsing learner info from excel?
        learner_description = append_learner_description(learner_info, student_sis_id)

        # Further process these feedback results
        feedback_with_los = append_los_text(feedback, learner_description) 


        # Append Pinecone context to the feedback
        full_prompt = feedback_with_los + context

        # Generate GPT feedback
        gpt_output = call_gpt(full_prompt)
        gpt_output = gpt_output.replace('**', '')
        # formatted_gpt_output = gpt_output.replace('\n', '\n\n')

        datetime_suffix = get_datetime_suffix()
        feedback_filename = f'feedback_output_user_{student_id}_attempt_{attempt}_{datetime_suffix}.txt'
        gpt_filename = f'gpt_feedback_output_user_{student_id}_attempt_{attempt}_{datetime_suffix}.txt'
        file_path_gpt_output = os.path.join('gpt_feedback_log', gpt_filename)
        file_path_prompt = os.path.join('gpt_prompt_log', feedback_filename)
        try:
            with open(file_path_prompt, 'w', encoding='utf-8') as f:
                f.write(full_prompt)
        except Exception as e:
            print(f"Error writing to file: {e}")
            pass

        try:
            with open(file_path_gpt_output, 'w', encoding='utf-8') as f:
                f.write(gpt_output)
        except Exception as e:
            print(f"Error writing to file: {e}")
            pass

        message_content = f"Dear {student_name},\n\n{gpt_output}\n\nBest regards,\nYour Friendly Instructor Team"
        quiz_name = check_quiz_name(attempt, name)
        # Send the feedback via Canvas message API
        subject = f'{quiz_name} Personalised Feedback'
        # response = canvas_api.create_conversation([str(canvas_id)], subject, message_content)
        # print(f"Feedback sent to student {student_id} for attempt {attempt}: {response}")
        return gpt_filename

# with error handling
# import logging
# def process_feedback_for_all_students(merged_data, canvas_api, name):
#     # Get unique combinations of student id and attempt numbers
#     unique_students_attempts = merged_data[['user_id', 'n_attempt']].drop_duplicates()

#     # Iterate over each student and attempt to generate feedback
#     for _, row in unique_students_attempts.iterrows():
#         try:
#             student_id = row['user_id']
#             attempt = row['n_attempt']

#             # Extract student's name, sis_id, and canvas_id
#             try:
#                 student_info = merged_data[(merged_data['user_id'] == student_id) & (merged_data['n_attempt'] == attempt)].iloc[0]
#                 student_name = student_info['name']
#                 student_sis_id = student_info['sis_id']
#                 canvas_id = student_info['canvas_id']
#             except IndexError as e:
#                 logging.error(f"Error extracting student info for user_id: {student_id}, attempt: {attempt}. Error: {e}")
#                 continue

#             # Generate feedback and get context
#             try:
#                 feedback = generate_feedback(merged_data, student_id, attempt)
#                 context = get_context(feedback)
#             except Exception as e:
#                 logging.error(f"Error generating feedback or context for user_id: {student_id}, attempt: {attempt}. Error: {e}")
#                 continue

#             # Parse learner info from excel
#             try:
#                 learner_info = pd.read_excel('docs/Sign Up List.xlsx', sheet_name='Compiled')
#                 learner_description = append_learner_description(learner_info, student_sis_id)
#             except FileNotFoundError as e:
#                 logging.error(f"Error reading learner info file for user_id: {student_id}, attempt: {attempt}. Error: {e}")
#                 continue

#             # Further process feedback
#             try:
#                 feedback_with_los = append_los_text(feedback, learner_description)
#                 full_prompt = feedback_with_los + context
#             except Exception as e:
#                 logging.error(f"Error appending LOS text or constructing full prompt for user_id: {student_id}, attempt: {attempt}. Error: {e}")
#                 continue

#             # Generate GPT feedback
#             try:
#                 gpt_output = call_gpt(full_prompt)
#                 gpt_output = gpt_output.replace('**', '')
#             except Exception as e:
#                 logging.error(f"Error calling GPT for user_id: {student_id}, attempt: {attempt}. Error: {e}")
#                 continue

#             # Write feedback and prompt to files
#             datetime_suffix = get_datetime_suffix()
#             feedback_filename = f'feedback_output_user_{student_id}_attempt_{attempt}_{datetime_suffix}.txt'
#             gpt_filename = f'gpt_feedback_output_user_{student_id}_attempt_{attempt}_{datetime_suffix}.txt'
#             file_path_gpt_output = os.path.join('gpt_feedback_log', gpt_filename)
#             file_path_prompt = os.path.join('gpt_prompt_log', feedback_filename)

#             try:
#                 with open(file_path_prompt, 'w', encoding='utf-8') as f:
#                     f.write(full_prompt)
#             except Exception as e:
#                 logging.error(f"Error writing prompt to file for user_id: {student_id}, attempt: {attempt}. Error: {e}")

#             try:
#                 with open(file_path_gpt_output, 'w', encoding='utf-8') as f:
#                     f.write(gpt_output)
#             except Exception as e:
#                 logging.error(f"Error writing GPT output to file for user_id: {student_id}, attempt: {attempt}. Error: {e}")

#             # Send feedback via Canvas message API
#             try:
#                 message_content = f"Dear {student_name},\n\n{gpt_output}\n\nBest regards,\nYour Friendly Instructor Team"
#                 quiz_name = check_quiz_name(attempt, name)
#                 subject = f'{quiz_name} Personalised Feedback'
#                 response = canvas_api.create_conversation([str(canvas_id)], subject, message_content)
#                 logging.info(f"Feedback sent to student {student_id} for attempt {attempt}: {response}")
#             except Exception as e:
#                 logging.error(f"Error sending feedback to Canvas for user_id: {student_id}, attempt: {attempt}. Error: {e}")

#         except Exception as general_e:
#             # Log any unexpected errors that could affect the entire process for a student
#             logging.error(f"Unexpected error for user_id: {student_id}, attempt: {attempt}. Error: {general_e}")

#     return gpt_filename


from dotenv import load_dotenv
def main(excel_filename, canvas_map_path, name):
    # Configuration for Canvas API
    # api_url = 'https://nus-dev.instructure.com'
    api_url = 'https://canvas.nus.edu.sg'
    load_dotenv()
    # api_key = os.getenv('CANVAS_API_KEY')
    # api_key = '' # Please fill in your own access token
    # canvas_api = CanvasAPI(api_url, api_key)

    # Example usage
    # Assuming merged_data is already loaded as a DataFrame

    file_path = excel_filename # from Adaptive Quiz: output log
    user_log = load_and_process_log(file_path, f'processed_record_aq.csv')
    save_path = os.path.join('_cache', "aq_user_log.csv")
    user_log.to_csv(save_path)
    canvas_mapping = pd.read_csv(canvas_map_path, encoding="utf-8")
    merged_data = merge_data(user_log, canvas_mapping)
    save_path_2 = os.path.join('_cache',"aq_merged_data.csv")
    merged_data.to_csv(save_path_2)

    # Example usage: assuming merged_data is available
    gpt_feedback = process_feedback_for_all_students(merged_data, None, name) #canvas_api, name)
    return gpt_feedback


if __name__ == "__main__":
    pass
