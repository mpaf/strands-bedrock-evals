from strands_evals import Case, Experiment
from strands_evals.extractors import tools_use_extractor
from strands_evals.evaluators import OutputEvaluator
from strands_evals.evaluators import TrajectoryEvaluator
from strands_evals.evaluators import HelpfulnessEvaluator, GoalSuccessRateEvaluator
import logging


test_cases = [
    Case[str, str](
        name="get passport details, name provided",
        input="Hi, my name is Christian, can you check my passport picture?",
        expected_trajectory=["analyze_passport_pic"],
        expected_output="Perfect! I've successfully analyzed your passport picture. Here's what I found"
    ),
    Case[str, str](
        name="get passport details, no name",
        input="Hi, can you check my passport picture?",
        expected_trajectory=["retrieve_customer_name", "analyze_passport_pic"],
        expected_output="Perfect! I've successfully analyzed your passport picture. Here's what I found"
    )

]

output_evaluator = OutputEvaluator(
    rubric="Score 1.0 for accurate, complete responses. Score 0.5 for partial answers. Score 0.0 for incorrect or unhelpful responses.",
)

trajectory_evaluator = TrajectoryEvaluator(
    rubric="Score 1.0 if correct tools used in proper sequence. Use scoring tools to verify trajectory matches."
)

goal_evaluator = GoalSuccessRateEvaluator()

experiment = Experiment[str, str](cases=test_cases, evaluators=[
    goal_evaluator, # trajectory_evaluator
])

# Define task function that captures tool usage
def get_response_with_tools(case: Case) -> dict:
    # Move agent definition inside each case to reset history for each test case

    from agent import my_agent
    response = my_agent(case.input)
    trajectory = tools_use_extractor.extract_agent_tools_used_from_metrics(response)

    return {"output": str(response), "trajectory": trajectory}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    reports = experiment.run_evaluations(get_response_with_tools)
    reports[0].run_display()