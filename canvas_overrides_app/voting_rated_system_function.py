from collections import defaultdict

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

# Example usage
if __name__ == '__main__':
    # Example list of paths from experts
    expert_paths = [
        [15, 21, 17, 23, 22],
        [15, 16, 21, 17, 22, 23],
        [15, 21, 16, 22, 23],
        [15, 16, 21, 23],
        [21, 15, 16, 1],
        [21, 15, 16, 23, 22],
        [21, 16, 22, 23, 15],
        [21, 15, 16, 23],
        [21, 16, 15, 22, 17, 23],
        [21, 15, 17, 22]
    ]
    
    # Generate the final path using the rated voting method
    final_path = rated_voting(expert_paths, max_score=5)
    print("Final Path:", final_path)