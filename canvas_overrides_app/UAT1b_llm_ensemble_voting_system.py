from openai import OpenAI
from dotenv import load_dotenv
# from voting_ranked_pairs_function import ranked_pairs
# from voting_rated_system_function import rated_voting
import os
import re
from collections import defaultdict


def llm_ensemble(PG_rank_order, KA_rank_order,learner_background_and_prior_knowledge,time_constraint_min,pretest_scores,cell_mastery_pair,additional_custom_information,student_id):
    ## Set the API key
    # Load environment variables from .env file
    load_dotenv()

    # Get the API key from environment variables
    api_key = os.getenv('OPENAI_API_KEY')

    # Initialize the OpenAI client with the API key
    client = OpenAI(api_key=api_key)

    gpt_current_role_1="construction project management expert"
    gpt_current_role_2="experienced project management trainer and course developer"

    if gpt_current_role_2 is not None:
        gpt_current_role_1 = gpt_current_role_1 + " and " + gpt_current_role_2

    # cell_min_pair={ 1: 17, 2: 21, 3: 22, 4: 35, 5: 18, 6: 32, 7: 17, 8: 58, 9: 9, 10: 31, 11: 6, 12: 13, 13: 11, 14: 11, 15: 28, 16: 80, 17: 10, 18: 13, 19: 19, 20: 5, 21: 60, 22: 3, 23: 5, 24: 41, 25: 13, 26: 13, 27: 5, 28: 12, 29: 13, 30: 4 }
    cell_min_pair = {
        1: 29,  # Integration - Initiating
        2: 36,  # Integration - Planning
        3: 35,  # Integration - Executing
        4: 35,  # Integration - Monitoring & Controlling
        5: 29,  # Integration - Closing
        6: 32,  # Scope - Planning
        7: 17,  # Scope - Monitoring & Controlling
        8: 58,  # Schedule - Planning
        9: 9,   # Schedule - Monitoring & Controlling
        10: 31, # Cost - Planning
        11: 6,  # Cost - Monitoring & Controlling
        12: 13, # Quality - Planning
        13: 11, # Quality - Executing
        14: 11, # Quality - Monitoring & Controlling
        15: 45, # Resource - Planning
        16: 129,# Resource - Executing
        17: 16, # Resource - Monitoring & Controlling
        18: 23, # Communication - Planning
        19: 32, # Communication - Executing
        20: 8,  # Communication - Monitoring & Controlling
        21: 97, # Risk - Planning
        22: 5,  # Risk - Executing
        23: 10, # Risk - Monitoring & Controlling
        24: 68, # Procurement - Planning
        25: 21, # Procurement - Executing
        26: 22, # Procurement - Monitoring & Controlling
        27: 9,  # Stakeholder - Initiating
        28: 20, # Stakeholder - Planning
        29: 21, # Stakeholder - Executing
        30: 8   # Stakeholder - Monitoring & Controlling
    }



    initial_prompt = '''You are a ''' + gpt_current_role_1 + '''. This Project Management course can be divided into 5 Process Groups (PG): Initiating, Planning, Execution, Monitoring and Controlling, Closing. 
    The course also can be divided into 10 knowledge areas (KA): Integration, Scope, Schedule, Cost, Quality, Resources, Communication, Risk, Procurement, Stakeholders.
    In both process groups and knowledge areas can be preferential ranked from 1, 2, 3, 4, 5 and 1,2,3,4,5,7,6,8,9,10 respectively. The smaller, the better.
    Here is the detail of each cell based on Process Group (PG) and Knowledge Area (KA)

    Cell 1 (PG = Initiating, KA = Integration)
    Develop Project Charter

    Cell 2 (PG = Planning, KA = Integration)
    Develop Project Management Plan

    Cell 3 (PG = Executing, KA = Integration)
    Direct and Manage Project Work
    Manage Project Knowledge

    Cell 4 (PG= Monitoring & Controlling, KA = Integration)
    Monitor and Control Project Work
    Perform Integrated Change Control

    Cell 5 (PG = Closing, KA = Integration)
    Close Project or Phase

    Cell 6 (PG = Planning, KA = Scope)
    Plan Scope Management
    Collect Requirements
    Define Scope
    Create Work Breakdown Structure

    Cell 7 (PG = Monitoring & Controlling, KA = Scope)
    Validate Scope
    Control Scope

    Cell 8 (PG = Planning, KA = Schedule)
    Plan Schedule Management
    Define Activities
    Sequence Activities
    Estimate Activity Durations
    Develop Schedule

    Cell 9 (PG = Monitoring & Controlling, KA = Schedule)
    Control Schedule

    Cell 10 (PG = Planning, KA = Cost)
    Plan Cost Management
    Estimate Costs
    Determine Budget

    Cell 11 (PG = Monitoring & Controlling, KA = Cost)
    Control Costs

    Cell 12 (PG = Planning, KA = Quality)
    Plan Quality Management

    Cell 13 (PG = Executing, KA = Quality)
    Manage Quality

    Cell 14 (PG = Monitoring & Controlling, KA = Quality)
    Control Quality

    Cell 15 (PG = Planning, KA = Resources)
    Plan Resource Management
    Estimating Activity Resources

    Cell 16 (PG = Executing, KA = Resources)
    Acquiring Resources
    Develop Team
    Manage Team

    Cell 17 (PG = Monitoring & Controlling, KA = Resources)
    Control Resources

    Cell 18 (PG = Planning, KA = Communication)
    Plan Communications Management

    Cell 19 (PG = Executing, KA = Communication)
    Manage Communications

    Cell 20 (PG = Monitoring & Controlling, KA = Communication)
    Monitor Communications

    Cell 21 (PG = Planning, KA = Risk)
    Plan Risk Management
    Identify Risks
    Perform Qualitative Risk Analysis
    Perform Quantitative Risk Analysis
    Plan Risk Responses

    Cell 22 (PG = Executing, KA = Risk)
    Implement Risk Responses

    Cell 23 (PG = Monitoring & Controlling, KA = Risk)
    Monitor Risks

    Cell 24 (PG = Planning, KA = Procurement)
    Plan Procurement Management

    Cell 25 (PG = Executing, KA = Procurement)
    Conduct Procurements

    Cell 26 (PG = Monitoring & Controlling, KA = Procurement)
    Control Procurement

    Cell 27 (PG = Initiating, KA = Stakeholder)
    Stakeholder Identification

    Cell 28 (PG = Planning, KA = Stakeholder)
    Plan Stakeholder Management

    Cell 29 (PG = Executing, KA = Stakeholder)
    Manage Stakeholder Engagement

    Cell 30 (PG = Monitoring & Controlling, KA = Stakeholder)
    Monitor Stakeholder Engagement

    I have a time constraint that I only can learn the recommended path within timeframe of '''+ str(time_constraint_min)+''' mins. I must strictly keep within this time constraint. Different cells need learning timeframe. 30 cell-mins pair: '''+str(cell_min_pair)+'''. For example, if I learn the second cell, I must consume 21 mins.

    Please recommend a learning path of this Project Management according to my background (job role and preferences) and prior knowledge (pre-test information). You may place more emphasis on the current job role if necessary.
    Return only the path. You must absolutely provide the path and strictly in this format:[1,2,...,nth]. Also, provide the selection criteria and summarize the rationale behind the recommendation of this learning path. List the headings of the section.


    Learner's background and prior knowledge: ''' + learner_background_and_prior_knowledge + '''

    My Pre-test Knowledge Quiz Score is ''' + pretest_scores + ''', covering 30 cell-mastery pair: ''' + str(cell_mastery_pair) + '''. Each index represents cell 1 to cell 30 respectively. Value 1 means learner has possibly covered knowledge in this area and 0 means learner has not yet covered knowledge in this area.

    Ranking order : 1 means highest preferred.
    My preferences ranking in for Process Groups (PG) is ''' + PG_rank_order + '''.
    My preferences ranking in for Knowledge Areas (KA) is ''' + KA_rank_order + '''.
    Here are some additional custom information: '''+ additional_custom_information+'''
   Do not list intermediate paths. The total duration must never exceed the time constraint of '''+ str(time_constraint_min)+''' mins. The maximum you may exceed is by 30min. If the time exceeds the time constraint, the recommendation will be rejected.
    
    '''
    # in the format Cell 1 --> Cell 2 --> ... --> Cell_nth. You must also absolutely provide the path 
    run = 0
    full_ensemble_output_path = ""
    full_ensemble_output = ""
    last_output = ""

    def call_chatgpt_api(prompt):
        nonlocal run, full_ensemble_output_path, full_ensemble_output, last_output
        MODEL="gpt-4o"

        completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a construction project management expert and an experienced project management trainer and course developer."},
            {"role": "user", "content": prompt}
        ]
        )
        run += 1
        print("count",run)

        # full_ensemble_output += completion.choices[0].message.content +"\n"+ "New expert"+"\n========================================\n"
        full_ensemble_output += "\n"+ "New expert from this point onwards:"+"\n"+completion.choices[0].message.content 
        last_output = completion.choices[0].message.content

        # Search for the word "Final" and start regex search after it
        final_index = last_output.find("Final")
        if final_index != -1:
                search_text = last_output[final_index:]  # Start searching from "Final"
                print("Final included")
        else:
                search_text = last_output

        match_gpt = re.search(r'\*\*Path:\*\*\s\[(.*?)\]', search_text)
        match_gpt_bracket = re.search(r'\[\s*(\d+\s*(?:,\s*\d+\s*)*)\]', search_text)
        match_gpt_bracket_2 = re.search(r'\\\[\s*(\d+\s*(?:,\s*\d+\s*)*)\\\]', search_text) 
        match_gpt_bracket_3 = re.search(r'\[\*\*Cell \d+(?: --> Cell \d+)*\*\*\]', search_text)
        match_gpt_bracket_4 = re.search(r'\*\*\s\[\d+\s*->\s*\d+\]\*\*', search_text) #** [21 -> 27]**
        match_gpt_bracket_5 = re.search(r'\*\*Path:\s\[Cell \d+(?: --> Cell \d+)*\]\*\*', search_text) # **Path: [Cell 2 --> Cell 10 --> Cell 18 --> Cell 25 --> Cell 28]**
        match_gpt_bracket_6 = re.search(r'\[Cell \d+(?: --> Cell \d+)*\]', search_text) #[Cell 3 --> Cell 25 --> Cell 22 --> Cell 30 --> Cell 20]
        match_gpt_bracket_7 = re.search(r'\[Cell \d+ \rightarrow Cell \d+( \rightarrow Cell \d+)*\]', search_text) # \[Cell 3 \rightarrow Cell 6 \rightarrow Cell 10 \rightarrow Cell 15 \rightarrow Cell 18\]
        
        # If no path is found and "Final" was included, try searching from the beginning
        if not (match_gpt or match_gpt_bracket or match_gpt_bracket_2 or match_gpt_bracket_3 or match_gpt_bracket_4 or match_gpt_bracket_5 or match_gpt_bracket_7):
            if final_index != -1:
                print("Path not found after 'Final', searching from the start")
                search_text = last_output  # Reset to search from the beginning

                # Perform the regex searches again on the full text
                match_gpt = re.search(r'\*\*Path:\*\*\s\[(.*?)\]', search_text)
                match_gpt_bracket = re.search(r'\[\s*(\d+\s*(?:,\s*\d+\s*)*)\]', search_text)
                match_gpt_bracket_2 = re.search(r'\\\[\s*(\d+\s*(?:,\s*\d+\s*)*)\\\]', search_text) 
                match_gpt_bracket_3 = re.search(r'\[\*\*Cell \d+(?: --> Cell \d+)*\*\*\]', search_text)
                match_gpt_bracket_4 = re.search(r'\*\*\s\[\d+\s*->\s*\d+\]\*\*', search_text) #** [21 -> 27]**
                match_gpt_bracket_5 = re.search(r'\*\*Path:\s\[Cell \d+(?: --> Cell \d+)*\]\*\*', search_text) # **Path: [Cell 2 --> Cell 10 --> Cell 18 --> Cell 25 --> Cell 28]**
                match_gpt_bracket_6 = re.search(r'\[Cell \d+(?: --> Cell \d+)*\]', search_text) #[Cell 3 --> Cell 25 --> Cell 22 --> Cell 30 --> Cell 20]
                match_gpt_bracket_7 = re.search(r'\[Cell \d+ \rightarrow Cell \d+( \rightarrow Cell \d+)*\]', search_text) # \[Cell 3 \rightarrow Cell 6 \rightarrow Cell 10 \rightarrow Cell 15 \rightarrow Cell 18\]
        
        if match_gpt:
            path_str = match_gpt.group(1)
            path_gpt_list = [int(num) for num in path_str.split(',')]
            print("Path_gpt_0:", path_gpt_list)
        elif match_gpt_bracket:
            path_str = match_gpt_bracket.group(1)
            path_gpt_list = [int(num) for num in path_str.split(',')]
            print("Path_gpt_1:", path_gpt_list)
        elif match_gpt_bracket_2:
            path_str = match_gpt_bracket_2.group(1)
            path_gpt_list = [int(num) for num in path_str.split(',')]
            print("Path_gpt_2:", path_gpt_list)    
        elif match_gpt_bracket_3:
            path_str = match_gpt_bracket_3.group(1)
            path_gpt_list = [int(num) for num in path_str.split(',')]
            print("Path_gpt_3:", path_gpt_list)    
        elif match_gpt_bracket_4:
            path_str = match_gpt_bracket_4.group(1)
            path_gpt_list = [int(num) for num in path_str.split(',')]
            print("Path_gpt_4:", path_gpt_list)    
        elif match_gpt_bracket_5:
            path_str = match_gpt_bracket_5.group(1)
            path_gpt_list = [int(num) for num in path_str.split(',')]
            print("Path_gpt_5:", path_gpt_list)    
        # elif match_gpt_bracket_6:
        #     path_str = match_gpt_bracket_6.group(1)
        #     path_gpt_list = [int(num) for num in path_str.split(',')]
        #     print("Path_gpt_6:", path_gpt_list)    
        elif match_gpt_bracket_7:
            path_str = match_gpt_bracket_7.group(1)
            path_gpt_list = [int(num) for num in path_str.split(',')]
            print("Path_gpt_7:", path_gpt_list)    
        else:
            print("Path not found while searching in gpt")
            return str([-1])
        return ( str(path_gpt_list))

    outputs = [call_chatgpt_api(initial_prompt) for _ in range(10)]
    print("outputs",outputs)
    print(type(outputs))
    
    # Ensure the output directory exists
    output_dir = 'student_LLM_text_outputs'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    collated_output_dir = 'collated_student_LLM_path_outputs'
    if not os.path.exists(collated_output_dir):
        os.makedirs(collated_output_dir)
    ensemble_prompt_dir = 'ensemble_prompt_students'
    if not os.path.exists(ensemble_prompt_dir):
        os.makedirs(ensemble_prompt_dir)
    ensemble_prompt_output = 'ensemble_prompt_outputs'
    if not os.path.exists(ensemble_prompt_output):
        os.makedirs(ensemble_prompt_output)
    
    with open(os.path.join(output_dir, f'full_ensemble_output_{student_id}.txt'), 'w') as file:
        file.write((full_ensemble_output))

    with open(os.path.join(collated_output_dir, f'collated_outputs_{student_id}.txt'), 'w') as file:
        file.write('\n'.join(outputs))

    nested_list = [list(map(int, s.strip('[]').split(', '))) for s in outputs]
    # path_list = ranked_pairs(nested_list)
    path_list = rated_voting(nested_list)
        
    return path_list

def rated_voting(expert_paths, max_score=5):
    """
    Aggregates expert-provided paths into a consensus path using a rated voting system.
    Scores are inferred from the positions of steps within the expert paths.

    Parameters:
    - expert_paths: List[List[int]]
        A list where each inner list represents a path provided by an expert.
    - max_score: int
        The maximum score that can be assigned to a step.

    Returns:
    - final_path: List[int]
        The consensus path derived from the aggregated scores of each step.
    """
    # Initialize a dictionary to hold scores
    step_scores = defaultdict(float)

    # Determine the maximum length of the paths
    max_length = max(len(path) for path in expert_paths)

    for path in expert_paths:
        num_steps = len(path)
        for position, step in enumerate(path):
            # Assign scores inversely proportional to position
            # Normalize the score to the max_score
            score = max_score * (1 - (position / (num_steps - 1)) if num_steps > 1 else 1)
            step_scores[step] += score

    # Sort steps based on total scores in descending order
    # If there's a tie, sort by the step number (or any other tie-breaker)
    sorted_steps = sorted(step_scores.items(), key=lambda x: (-x[1], x[0]))

    # Extract the steps from the sorted tuples
    final_path = [step for step, score in sorted_steps]

    return final_path