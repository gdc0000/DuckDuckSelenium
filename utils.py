import pandas as pd
import logging
import os
import sys

def setup_logging():
    """Sets up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("scraper.log", mode='w')
        ]
    )

def read_input_file(filepath):
    """Reads an input file into a list. Assumes a header row exists."""
    try:
        # Read as plain text to avoid pandas separator guessing issues
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        
        if not lines:
            return []
            
        # Return lines excluding the header
        return lines[1:]
    except Exception as e:
        logging.error(f"Error reading {filepath}: {e}")
        return []

def read_date_file(filepath):
    """Reads the date file. Expects start_date and end_date columns."""
    try:
        # Explicitly use tab separator as seen in the file
        df = pd.read_csv(filepath, sep='\t')
        # Normalize column names
        df.columns = [c.strip().lower() for c in df.columns]
        return df
    except Exception as e:
        logging.error(f"Error reading {filepath}: {e}")
        # Fallback to trying with whitespace separator if tab fails
        try:
            df = pd.read_csv(filepath, delim_whitespace=True)
            df.columns = [c.strip().lower() for c in df.columns]
            return df
        except:
            return pd.DataFrame()

def ensure_output_dir(directory):
    """Creates the output directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)
