# Dataset Inspection

The inspection CLI summarizes every supported file in the input directory and produces a markdown report.

## Supported Files

- `.jsonl`
- `.json`
- `.csv`
- `.docx`

## What the Report Includes

- file path
- file type
- record count
- detected fields
- inferred field types
- presence and missing counts
- example values
- short text previews for DOCX and text-like inputs

## Usage

```bash
python inspect_data.py --input-dir data/raw --output output/inspection_report.md
```

If the output path ends in `.json`, the CLI writes structured JSON instead of markdown.