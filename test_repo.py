# tests/test_repo_miner.py

import os
import pandas as pd
import pytest
from datetime import datetime, timedelta
from src.repo_miner import (
    fetch_commits,
    fetch_issues,
)  # , merge_and_summarize <-- commented until implemented

# --- Helpers for dummy GitHub API objects ---


class DummyAuthor:
    def __init__(self, name, email, date):
        self.name = name
        self.email = email
        self.date = date


class DummyCommitCommit:
    def __init__(self, author, message):
        self.author = author
        self.message = message


class DummyCommit:
    def __init__(self, sha, author, email, date, message):
        self.sha = sha
        self.commit = DummyCommitCommit(
            DummyAuthor(author, email, date), message)


class DummyUser:
    def __init__(self, login):
        self.login = login


class DummyIssue:
    def __init__(
        self,
        id_,
        number,
        title,
        user,
        state,
        created_at,
        closed_at,
        comments,
        is_pr=False,
    ):
        self.id = id_
        self.number = number
        self.title = title
        self.user = DummyUser(user)
        self.state = state
        self.created_at = created_at
        self.closed_at = closed_at
        self.comments = comments
        # attribute only on pull requests
        self.pull_request = DummyUser("pr") if is_pr else None


class DummyRepo:
    def __init__(self, commits, issues):
        self._commits = commits
        self._issues = issues

    def get_commits(self):
        return self._commits

    def get_issues(self, state="all"):
        # filter by state
        if state == "all":
            return self._issues
        return [i for i in self._issues if i.state == state]


class DummyGithub:
    def __init__(self, token):
        assert token == "fake-token"

    def get_repo(self, repo_name):
        # ignore repo_name; return repo set in test fixture
        return self._repo


@pytest.fixture(autouse=True)
def patch_env_and_github(monkeypatch):
    # Set fake token
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    # Patch Github class
    monkeypatch.setattr("src.repo_miner.Github", lambda token: gh_instance)


# Helper global placeholder
gh_instance = DummyGithub("fake-token")

# --- Tests for fetch_commits ---
# An example test case


def test_fetch_commits_basic(monkeypatch):
    # Setup dummy commits
    now = datetime.now()
    commits = [
        DummyCommit("sha1", "Alice", "a@example.com",
                    now, "Initial commit\nDetails"),
        DummyCommit("sha2", "Bob", "b@example.com",
                    now - timedelta(days=1), "Bug fix"),
    ]
    gh_instance._repo = DummyRepo(commits, [])
    df = fetch_commits("any/repo")
    assert list(df.columns) == ["sha", "author", "email", "date", "message"]
    assert len(df) == 2
    assert df.iloc[0]["message"] == "Initial commit"


def test_fetch_commits_limit(monkeypatch):
    # More commits than max_commits
    # TODO： Test that fetch_commits respects the max_commits limit.
    now = datetime.now()
    commits = [
        DummyCommit("sha1", "Alice", "a@example.com",
                    now, "Initial commit\nDetails"),
        DummyCommit("sha2", "Bob", "b@example.com",
                    now - timedelta(days=1), "Bug fix"),
    ]
    gh_instance._repo = DummyRepo(commits, [])
    df = fetch_commits("any/repo", max_commits=1)
    assert len(df) == 1


def test_fetch_commits_empty(monkeypatch):
    commits = []
    gh_instance._repo = DummyRepo(commits, [])
    df = fetch_commits("any/repo")
    assert len(df) == 0


def test_fetch_issues_dates(monkeypatch):
    now = datetime.now()
    issues = [
        DummyIssue(1, 101, "Issue A", "alice", "open",
                   datetime(2025, 10, 2), None, 0),
        DummyIssue(2, 102, "Issue B", "bob", "closed",
                   now - timedelta(days=2), now, 2),
    ]
    gh_instance._repo = DummyRepo([], issues)
    df = fetch_issues("any/repo", state="all")
    assert {
        "id",
        "number",
        "title",
        "user",
        "state",
        "created_at",
        "closed_at",
        "comments",
    }.issubset(df.columns)
    assert len(df) == 2
    # Check date normalization
    assert str(df.iloc[0, 5]).startswith(
        "2025-10-02"
    )  # use first issue to test format of string
    assert df.iloc[1, 8] == 2  # check second issue's days_open


def test_fetch_issues_time_open_days(monkeypatch):
    now = datetime.now()
    issues = [
        DummyIssue(1, 101, "Issue A", "alice", "open",
                   datetime(2025, 10, 2), None, 0),
        DummyIssue(2, 102, "Issue B", "bob", "closed",
                   now - timedelta(days=2), now, 2),
    ]
    gh_instance._repo = DummyRepo([], issues)
    df = fetch_issues("any/repo", state="all")
    assert {
        "id",
        "number",
        "title",
        "user",
        "state",
        "created_at",
        "closed_at",
        "comments",
    }.issubset(df.columns)
    assert len(df) == 2
    assert df.iloc[1, 8] == 2  # check second issue's days_open


def test_fetch_issues_pr_excluded(monkeypatch):
    now = datetime.now()
    issues = [
        DummyIssue(1, 101, "Issue A", "alice", "open",
                   datetime(2025, 10, 2), None, 0),
        DummyIssue(
            2,
            102,
            "PR A",
            "bob",
            "closed",
            now - timedelta(days=2),
            now - timedelta(days=1),
            2,
            is_pr=True,
        ),
        DummyIssue(3, 103, "Issue B", "bob", "closed",
                   now - timedelta(days=2), now, 2),
    ]
    gh_instance._repo = DummyRepo([], issues)
    df = fetch_issues("any/repo", state="all")
    assert {
        "id",
        "number",
        "title",
        "user",
        "state",
        "created_at",
        "closed_at",
        "comments",
    }.issubset(df.columns)
    assert len(df) == 2  # check that we actually only get 2 back, instead of 3
