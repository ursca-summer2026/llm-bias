
model="gemma4"
runs="50"
echo "Model $model"
uv run llm-bias query \
  --model ${model} \
  --keywords "Nurse,Doctor,Engineer,Lawyer,Teacher,Chef,Hair Stylist" \
  --prompt-file prompts/prompts_2.txt \
  --runs ${runs} \
  --output 0_out/runs_${runs}-model_${model} \
  --max-tokens 500


model="deepseek-r1"
runs="100"
echo "Model $model"
uv run llm-bias query \
  --model ${model} \
  --keywords "Nurse,Doctor,Engineer,Lawyer,Teacher,Chef,Hair Stylist" \
  --prompt-file prompts/prompts_2.txt \
  --runs ${runs} \
  --output 0_out/runs_${runs}-model_${model} \
  --max-tokens 500


model="gemma4"
runs="100"
echo "Model $model"
uv run llm-bias query \
  --model ${model} \
  --keywords "Nurse,Doctor,Engineer,Lawyer,Teacher,Chef,Hair Stylist" \
  --prompt-file prompts/prompts_2.txt \
  --runs ${runs} \
  --output 0_out/runs_${runs}-model_${model} \
  --max-tokens 500
  