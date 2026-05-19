## Summary

- 

## Architecture Changes

- 

## New Features

- 

## Removed Features

- 

## How to Test

```bash
# Install dependencies (first time only)
pip install jinja2
npm install && npm run build

# Start the puzzle server
python scripts/serve.py 8000
```

- Open `http://localhost:8000/puzzle/<id>` to view a puzzle
- Append `?seed=<value>` to test different seed variations
- Submit an answer via the form; expect correct/incorrect feedback
- Check hint reveal behavior with the "Show hints" toggle

## Added TODOs

- 
