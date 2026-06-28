# Runbook

## Setup

1. Activate the project environment.
2. Install dependencies from `requirements.txt`.
3. Place the hackathon dataset in `data/raw/`.

## Commands

### Run the Streamlit app

```bash
streamlit run app.py
```

### Run the pipeline

```bash
python main.py
```

### Inspect the dataset

```bash
python inspect_data.py --input-dir data/raw --output output/inspection_report.md
```

### Run tests

```bash
python -m pytest
```

## Expected Files

- `job_description.docx`
- `candidates.jsonl`
- `candidate_schema.json`
- `sample_submission.csv`
- `submission_spec.docx`
- `redrob_signals_doc.docx`
- `validate_submission.py`

## Troubleshooting

- If the app cannot import dependencies, reinstall packages inside `.venv`.
- If the validator is missing, the code falls back to local column checks.
- If the input files are missing, the CLI will still generate an empty report and note the issue.