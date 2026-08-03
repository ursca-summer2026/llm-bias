# Sample Scripts

Here you can find the scripts used to create the experimental data from the study. Each script run in series the models with the prompts and keywords. If you would like to add a new model to the work, first be sure that Ollama has this model already "pulled" (e.g., `ollama pull <modelName>`) and then add the new model to the script while following the same formatting as the other commands.

The command to run the "gemma4" model with prompts applied to the professional titles (keywords), providing 50 results, is the following.

```bash
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
```


## Running the scripts

These `.sh` files may be run on Unix machine using the command, `sh`. For example, to run the script `runCommands_50.sh`, the command is `sh runCommands_50`.

## Output

After running the script, two output files are produced; a CSV and an SQLite database file. The database file may be used with the dashboard application.
 