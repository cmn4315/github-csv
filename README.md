# github-csv
### repo_miner.py
### Author: Caleb Naeger - cmn4315@rit.edu

## Overview
A command-line tool to:
  1) Fetch and normalize commit data from GitHub
  2) fetch and normalize issue data from GitHub, excluding PRs

### Sub-commands:
  - fetch-commits
  - fetch-issues

### Installing Dependencies
This project depends on PyGitHub and Pandas, among other libraries. To install the required dependencies:
 - First, start a new python virtual environment with `python3 -m venv .venv`
    - On a Unix-based system, start the venv with `source .venv/bin/activate`
 - Install dependencies with `python3 -m pip install -r requirements.txt`

### Example Command Line Usage
 - `fetch-commits` is run following the following format
    - `python -m src.repo_miner fetch-commits --repo octocat/Hello-World [--max 2] [--out commits_limited.csv]`
 - `fetch-issues` is similar, following the format: 
    - `python -m src.repo_miner fetch-issues --repo owner/repo [--state all|open|closed] [--max 50] --out issues.csv`
