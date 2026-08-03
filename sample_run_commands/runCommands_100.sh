

model="phi3"
runs="100"
echo "Model $model"
uv run llm-bias query \
  --model ${model} \
  --keywords "Nurse,Doctor,Engineer,Lawyer,Teacher,Chef,Hair Stylist" \
  --prompt-file prompts/prompts_2.txt \
  --runs ${runs} \
  --output 0_out/runs_${runs}-model_${model} \
  --max-tokens 500


model="qwen"
runs="100"
echo "Model $model"
uv run llm-bias query \
  --model ${model} \
  --keywords "Nurse,Doctor,Engineer,Lawyer,Teacher,Chef,Hair Stylist" \
  --prompt-file prompts/prompts_2.txt \
  --runs ${runs} \
  --output 0_out/runs_${runs}-model_${model} \
  --max-tokens 500



model="ornith"
runs="100"
echo "Model $model"
uv run llm-bias query \
  --model ${model} \
  --keywords "Nurse,Doctor,Engineer,Lawyer,Teacher,Chef,Hair Stylist" \
  --prompt-file prompts/prompts_2.txt \
  --runs ${runs} \
  --output 0_out/runs_${runs}-model_${model} \
  --max-tokens 500




model="llama3.2"
runs="100"
echo "Model $model"
uv run llm-bias query \
  --model ${model} \
  --keywords "Nurse,Doctor,Engineer,Lawyer,Teacher,Chef,Hair Stylist" \
  --prompt-file prompts/prompts_2.txt \
  --runs ${runs} \
  --output 0_out/runs_${runs}-model_${model} \
  --max-tokens 500




model="mistral"
runs="100"
echo "Model $model"
uv run llm-bias query \
  --model ${model} \
  --keywords "Nurse,Doctor,Engineer,Lawyer,Teacher,Chef,Hair Stylist" \
  --prompt-file prompts/prompts_2.txt \
  --runs ${runs} \
  --output 0_out/runs_${runs}-model_${model} \
  --max-tokens 500


model="nomic-embed-text"
runs="100"
echo "Model $model"
uv run llm-bias query \
  --model ${model} \
  --keywords "Nurse,Doctor,Engineer,Lawyer,Teacher,Chef,Hair Stylist" \
  --prompt-file prompts/prompts_2.txt \
  --runs ${runs} \
  --output 0_out/runs_${runs}-model_${model} \
  --max-tokens 500


model="qwen3-coder-next"
runs="100"
echo "Model $model"
uv run llm-bias query \
  --model ${model} \
  --keywords "Nurse,Doctor,Engineer,Lawyer,Teacher,Chef,Hair Stylist" \
  --prompt-file prompts/prompts_2.txt \
  --runs ${runs} \
  --output 0_out/runs_${runs}-model_${model} \
  --max-tokens 500



```bash
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
```

```bash
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
```
