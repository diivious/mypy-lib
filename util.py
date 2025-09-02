#
# Donnie V Savage | Copyright (C) 2025
# Free to use - no copyrights
#
import os
import sys
import csv
import logger
import warnings

import pandas as pd
from openpyxl import Workbook

from logger import logger
from logger import DEBUG
from logger import INFO
from logger import WARNING
from logger import ERROR
from logger import CRITICAL

import warnings
from pathlib import Path

####
## Functons to manage coversion between list and dictionary
def list_to_dict(header, list):
    header = [h.strip() for h in header.split(',')]
    return [dict(zip(header, row)) for row in list]

def dict_to_list(dicts):
    foo = None
    header = [key.strip() for key in dicts[0].keys()]
    list = [[record.get(key) for key in header] for record in dicts] 
    return header, list

# Function to create an empty list
def blank_list(size):
    list =  [''] * size + ['\n']
    return list

def read_excel_index(filename):
    """
    Reads a CSV/XLS/XLSX file and returns a dict indexed by 'RACS Asset ID'.
    Skips rows with missing or blank 'RACS Asset ID'.
    """
    import os
    import sys
    import warnings
    import pandas as pd

    added_rows = 0
    dropped_rows = 0

    logger(DEBUG, f"Reading file as indexed dict: {filename}")
    try:
        suffix = os.path.splitext(filename)[1].lower()

        # ─── CSV PATH ─────────────────────────────────────────────────────────────
        if suffix == ".csv":
            for enc in ("utf-8", "latin-1", "ISO-8859-1"):
                try:
                    df = pd.read_csv(filename, dtype=str, skipinitialspace=True, encoding=enc).fillna("")
                    logger(DEBUG, f"Loaded CSV with encoding {enc}")
                    break
                except UnicodeDecodeError:
                    logger(DEBUG, f"Reading {filename} :: Trying encoding {enc}")
            else:
                logger(ERROR, f"All CSV encodings failed for {filename}")
                sys.exit(2)
                return None

        # ─── EXCEL PATH ───────────────────────────────────────────────────────────
        elif suffix in (".xls", ".xlsx"):
            warnings.filterwarnings(
                "ignore",
                category=UserWarning,
                module="openpyxl.styles.stylesheet",
            )
            df = (
                pd.read_excel(filename, sheet_name=0, dtype=str)
                  .fillna("")
            )

        # ─── UNSUPPORTED ──────────────────────────────────────────────────────────
        else:
            logger(DEBUG, f"Unsupported file type: {suffix}")
            return None

        # ─── CLEANUP ──────────────────────────────────────────────────────────────
        df.columns = df.columns.str.strip()
        df = df.apply(lambda v: v.str.strip() if v.dtype == "object" else v)

        # ─── INDEXING BY RACS Asset ID ────────────────────────────────────────────
        if "RACS Asset ID" not in df.columns:
            logger(ERROR, f"'RACS Asset ID' column missing in {filename}")
            return None

        indexed = {}
        for row in df.to_dict(orient="records"):
            key = row.get("RACS Asset ID", "").strip()
            if key:
                added_rows += 1
                indexed[key] = row
            else:
                dropped_rows += 1

        logger(DEBUG, f"Reading {filename} :: Rows:{added_rows} :: Dropped:{dropped_rows}")
        return indexed

    except FileNotFoundError:
        logger(DEBUG, f"File not found: {filename}")
        return None

####
## Function to manage reading a spread sheet into a dict
## Excepts CSV, XLS, XLSX
def read_excel_dict(filename):
    """
    Core loader: CSV/XLS/XLSX → list of dicts (one dict per row).
    Tries utf-8, latin-1, ISO-8859-1 on CSVs; suppresses the openpyxl warning.
    """
    logger(DEBUG, f"Reading file as dict: {filename}")
    try:
        suffix = os.path.splitext(filename)[1].lower()

        # ─── CSV PATH ─────────────────────────────────────────────────────────────
        if suffix == ".csv":
            for enc in ("utf-8", "latin-1", "ISO-8859-1"):
                try:
                    df = pd.read_csv(filename, dtype=str, skipinitialspace=True, encoding=enc).fillna("")
                    logger(DEBUG, f"Loaded CSV with encoding {enc}")
                    break
                except UnicodeDecodeError:
                    logger(DEBUG, f"Reading {filename} :: Trying encoding {enc}")
            else:
                # only reached if loop completes without break
                logger(ERROR, f"All CSV encodings failed for {filename}")
                sys.exit(2)
                return None

        # ─── EXCEL PATH ───────────────────────────────────────────────────────────
        elif suffix in (".xls", ".xlsx"):
            warnings.filterwarnings(
                "ignore",
                category=UserWarning,
                module="openpyxl.styles.stylesheet",
            )
            df = (
                pd.read_excel(filename, sheet_name=0, dtype=str)
                  .fillna("")           # ensure no NaN
            )

        # ─── UNSUPPORTED ──────────────────────────────────────────────────────────
        else:
            logger(DEBUG, f"Unsupported file type: {suffix}")
            return None

        # ─── CLEANUP ──────────────────────────────────────────────────────────────
        # strip whitespace from column names
        df.columns = df.columns.str.strip()
        # strip whitespace from every string cell
        df = df.apply(lambda v: v.str.strip() if v.dtype == "object" else v)

        # first-run: no data rows ⇒ create one empty record
        records = df.to_dict(orient="records")
        if not records:
            # first-run: no data rows ⇒ create one empty record
            records = [{col: "" for col in df.columns}]
        
        return records

    except FileNotFoundError:
        logger(DEBUG, f"File not found: {filename}")
        return None

####
## Function to manage reading a spread sheet into a list
## Excepts CSV, XLS, XLSX
def read_excel_list(filename):
    """
    Reads filename (CSV/XLS/XLSX) into list-of-lists exactly as
    df.values.tolist() would, via read_excel_dict + dict_to_list.
    """
    records = read_excel_dict(filename)
    if not records:
        return None

    header, rows = dict_to_list(records)
    return [header] + rows

####
## Function to remvoe duplicate rows from list or dict
## Excepts LIST, DICT
## Retutns LIST, DICT
def remove_duprows(data):
    """
    Remove duplicate rows from `data`, where each row is either:
      - a list (or tuple) of values, or
      - a dict of values.
    Returns:
      - dup_count: number of rows removed
      - unique:   list of rows of the same type, in original order
    """
    if not data:
        return 0, []

    seen = set()
    unique = []
    dup_count = 0
    first = data[0]

    # list/tuple rows
    if isinstance(first, (list, tuple)):
        for row in data:
            key = tuple(row)
            if key not in seen:
                seen.add(key)
                unique.append(row)
            else:
                dup_count += 1

    # dict rows
    elif isinstance(first, dict):
        for row in data:
            key = frozenset(row.items())
            if key not in seen:
                seen.add(key)
                unique.append(row)
            else:
                dup_count += 1

    else:
        unique = rows
        logger(ERROR, f"Cant remove duprows from unsupported type %r" % type(first))

    return dup_count, unique

####
## Function writes XLSX files
def write_xls_list(filename, list_data):
    # Convert the list into a pandas DataFrame
    df = pd.DataFrame(list_data)
    
    # Write the DataFrame to an Excel file (single sheet by default)
    try:
        df.to_excel(filename, index=False, header=False)

    except Exception as e:
        logger(CRITICAL, f"File {filename} failed to save: {e}")
        sys.exit(2)

def write_xls_dict(filename, dict_data):
    # Convert the dictionary into a pandas DataFrame
    df = pd.DataFrame([dict_data])
    
    # Write the DataFrame to an Excel file (single sheet by default)
    try:
        df.to_excel(filename, index=False)

    except Exception as e:
        logger(CRITICAL, f"File {filename} failed to save: {e}")
        sys.exit(2)

####
## Function read/write CSV files
def write_csv_list(filename, list_data):
    if not list_data:
        return  # nothing to do

    # assume first row is header
    header, *rows = list_data

    try:
        with open(filename, mode='w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            # always write header
            writer.writerow(header)

            # write only rows with at least one non-blank cell
            for row in rows:
                if any(
                    cell is not None and (not isinstance(cell, str) or cell.strip())
                    for cell in row
                ):
                    writer.writerow(row)

    except Exception as e:
        logger(CRITICAL, f"File {filename} failed to save list: {e}")
        sys.exit(2)


def write_csv_dict(filename, dict_data):
    # Explicit header list
    header = list(dict_data[0].keys())

    try:
        with open(filename, 'w', encoding='utf-8', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=header)
            writer.writeheader()

            for row in dict_data:
                # Skip rows where all values are None or blank/whitespace
                if all(v is None or (isinstance(v, str) and not v.strip())
                       for v in row.values()):
                    continue
                writer.writerow(row)

    except Exception as e:
        logger(CRITICAL, f"File {filename} failed to save dict: {e}")
        sys.exit(2)
       



