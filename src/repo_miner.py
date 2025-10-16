#!/usr/bin/env python3
"""
repo_miner.py

Author: Caleb Naeger - cmn4315@rit.edu

A command-line tool to:
  1) Fetch and normalize commit data from GitHub

Sub-commands:
  - fetch-commits
"""

import os
import argparse
import pandas as pd
from github import Github, Auth


def fetch_commits(repo_name: str, max_commits: int = None) -> pd.DataFrame:
    """
    Fetch up to `max_commits` from the specified GitHub repository.
    Returns a DataFrame with columns: sha, author, email, date, message.
    """
    # 1) Read GitHub token from environment
    token = os.environ.get("GITHUB_TOKEN", None)

    # 2) Initialize GitHub client and get the repo
    gh_client = Github(token)
    repo = gh_client.get_repo(repo_name)

    # 3) Fetch commit objects (paginated by PyGitHub)
    commits = repo.get_commits()

    # 4) Normalize each commit into a record dict
    if max_commits is not None:
        commits = commits[:max_commits]

    dicts = []
    for commit in commits:
        dicts.append(
            {
                "sha": commit.sha,
                "author": commit.commit.author.name,
                "email": commit.commit.author.email,
                "date": commit.commit.author.date,
                "message": commit.commit.message.split("\n", 1)[0],
            }
        )

    # 5) Build DataFrame from records
    return pd.DataFrame(dicts)


def fetch_issues(
    repo_name: str, state: str = "all", max_issues: int = None
) -> pd.DataFrame:
    """
    Fetch up to `max_issues` from the specified GitHub repository (issues only).
    Returns a DataFrame with columns: id, number, title, user, state, created_at, closed_at, comments.
    """
    # 1) Read GitHub token from environment
    token = os.environ.get("GITHUB_TOKEN", None)

    # 2) Initialize GitHub client and get the repo
    gh_client = Github(token)
    repo = gh_client.get_repo(repo_name)

    # 3) Fetch issues, filtered by state ('all', 'open', 'closed')
    issues = repo.get_issues(state=state)

    # 4) Normalize each issue (skip PRs)
    records = []
    for idx, issue in enumerate(issues):
        if max_issues and idx >= max_issues:
            break
        # Skip pull requests
        if not issue.pull_request:
            # Append records
            records.append(
                {
                    "id": issue.id,
                    "number": issue.number,
                    "title": issue.title,
                    "user": issue.user,
                    "state": issue.state,
                    "created_at": issue.created_at,
                    "closed_at": issue.closed_at,
                    "comments": issue.comments,
                    "open_duration_days": (issue.closed_at - issue.created_at).days
                    if issue.closed_at is not None
                    else None,
                }
            )

    # 5) Build DataFrame
    return pd.DataFrame(records)


def merge_and_summarize(commits_df: pd.DataFrame, issues_df: pd.DataFrame) -> None:
    """
    Takes two DataFrames (commits and issues) and prints:
      - Top 5 committers by commit count
      - Issue close rate (closed/total)
      - Average open duration for closed issues (in days)
    """
    # Copy to avoid modifying original data
    commits = commits_df.copy()
    issues = issues_df.copy()

    # 1) Normalize date/time columns to pandas datetime
    commits["date"] = pd.to_datetime(commits["date"], errors="coerce")
    issues["created_at"] = pd.to_datetime(issues["created_at"], errors="coerce")
    issues["closed_at"] = pd.to_datetime(issues["closed_at"], errors="coerce")

    # 2) Top 5 committers
    print(f"Top 5 committers: ")
    for value, count in commits["author"].value_counts().head(5).items():
        print(f"{value}: {count} commits")

    # 3) Calculate issue close rate
    num_closed = int(issues["state"].value_counts().get("closed", 0))
    print(f"Issue close rate: {round(num_closed / len(issues['state']), 2)}")

    # 4) Compute average open duration (days) for closed issues
    print(
        f"Avg. issue open duration: {
            sum(
                (
                    (issues['closed_at'][i] - issues['created_at'][i]).days
                    if pd.notna(issues['closed_at'][i])
                    else 0
                )
                for i in range(len(issues['created_at']))
            )
            / num_closed
        }"
    )


def main():
    """
    Parse command-line arguments and dispatch to sub-commands.
    """
    parser = argparse.ArgumentParser(
        prog="repo_miner", description="Fetch GitHub commits/issues and summarize them"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Sub-command: fetch-commits
    c1 = subparsers.add_parser("fetch-commits", help="Fetch commits and save to CSV")
    c1.add_argument("--repo", required=True, help="Repository in owner/repo format")
    c1.add_argument(
        "--max", type=int, dest="max_commits", help="Max number of commits to fetch"
    )
    c1.add_argument("--out", required=True, help="Path to output commits CSV")

    # Sub-command: fetch-issues
    c2 = subparsers.add_parser("fetch-issues", help="Fetch issues and save to CSV")
    c2.add_argument("--repo", required=True, help="Repository in owner/repo format")
    c2.add_argument(
        "--state",
        choices=["all", "open", "closed"],
        default="all",
        help="Filter issues by state",
    )
    c2.add_argument(
        "--max", type=int, dest="max_issues", help="Max number of issues to fetch"
    )
    c2.add_argument("--out", required=True, help="Path to output issues CSV")

    # Sub-command: summarize
    c3 = subparsers.add_parser("summarize", help="Summarize commits and issues")
    c3.add_argument("--commits", required=True, help="Path to commits CSV file")
    c3.add_argument("--issues", required=True, help="Path to issues CSV file")

    args = parser.parse_args()
    # Dispatch based on selected command
    if args.command == "fetch-commits":
        df = fetch_commits(args.repo, args.max_commits)
        df.to_csv(args.out, index=False)
        print(f"Saved {len(df)} commits to {args.out}")

    elif args.command == "fetch-issues":
        df = fetch_issues(args.repo, args.state, args.max_issues)
        df.to_csv(args.out, index=False)
        print(f"Saved {len(df)} issues to {args.out}")
    elif args.command == "summarize":
        # Read CSVs into DataFrames
        commits_df = pd.read_csv(args.commits)
        issues_df = pd.read_csv(args.issues)
        # Generate and print the summary
        merge_and_summarize(commits_df, issues_df)


if __name__ == "__main__":
    main()
