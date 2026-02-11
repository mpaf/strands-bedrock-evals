agentcore eval run \
  --agent-id passport_agent \
  --session-id $SESSION_ID \
  --evaluator "Builtin.Helpfulness" \
  --evaluator "Builtin.GoalSuccessRate"