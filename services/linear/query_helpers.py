#!/usr/bin/env python3
"""Pre-built GraphQL queries and fragments for common Linear operations.

Import these instead of inlining query strings so field selections stay
consistent across call sites.
"""

# Standard issue fields used by list/search results
ISSUE_FIELDS = """
    id
    identifier
    title
    description
    priority
    url
    createdAt
    updatedAt
    state { id name type }
    assignee { id name displayName }
    labels { nodes { id name } }
    project { id name }
"""

# Extended issue fields for single-issue fetches (adds comments + cycle)
ISSUE_DETAIL_FIELDS = """
    id
    identifier
    title
    description
    priority
    priorityLabel
    url
    createdAt
    updatedAt
    dueDate
    state { id name type }
    assignee { id name displayName }
    team { id name key }
    project { id name status }
    cycle { id name startsAt endsAt }
    labels { nodes { id name } }
    comments {
        nodes {
            id body createdAt
            user { id name displayName }
        }
    }
"""

PROJECT_FIELDS = """
    id
    name
    description
    status
    targetDate
    startDate
    progress
    url
"""

TEAM_FIELDS = """
    id
    name
    key
    description
"""

CYCLE_FIELDS = """
    id
    name
    number
    startsAt
    endsAt
    isActive
    completedAt
"""


def viewer_query() -> str:
    """Minimal auth/identity check."""
    return "query { viewer { id name email organization { name } } }"


def teams_query() -> str:
    return f"query {{ teams {{ nodes {{ {TEAM_FIELDS} }} }} }}"


def projects_query(status: str = None, limit: int = 50) -> str:
    if status:
        return (
            f'query {{ projects(first: {limit}, filter: '
            f'{{ status: {{ name: {{ eq: "{status}" }} }} }}) '
            f"{{ nodes {{ {PROJECT_FIELDS} }} }} }}"
        )
    return f"query {{ projects(first: {limit}) {{ nodes {{ {PROJECT_FIELDS} }} }} }}"


def issues_query(team_key: str, limit: int = 20) -> str:
    return (
        f'query {{ team(id: "{team_key}") {{ '
        f"issues(first: {limit}) {{ nodes {{ {ISSUE_FIELDS} }} }} }} }}"
    )


def search_issues_query(term: str, limit: int = 20) -> str:
    escaped = term.replace('"', '\\"')
    return (
        f'query {{ searchIssues(term: "{escaped}", first: {limit}) '
        f"{{ nodes {{ ... on Issue {{ {ISSUE_FIELDS} }} }} }} }}"
    )


def issue_by_identifier_query(identifier: str) -> str:
    escaped = identifier.replace('"', '\\"')
    return (
        f'query {{ issueSearch(filter: {{ identifier: {{ eq: "{escaped}" }} }}) '
        f"{{ nodes {{ {ISSUE_DETAIL_FIELDS} }} }} }}"
    )
