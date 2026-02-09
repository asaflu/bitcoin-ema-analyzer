#!/bin/bash
# Wrapper script for automated data updates
# Activates virtual environment and runs update script

# Change to project directory
cd /Users/asaf/__AI__/roiema

# Activate virtual environment
source venv/bin/activate

# Run update script with logging
python scripts/update_data.py >> logs/update_data.log 2>&1

# Exit with the script's exit code
exit $?
