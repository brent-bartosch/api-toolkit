#!/usr/bin/env python3
"""Example usage of the Linear API client."""

import sys
import os

sys.path.insert(
    0, str(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
)

from services.linear.api import LinearAPI


def example_discovery():
    """Show workspace discovery."""
    print("=== Discovery ===")
    api = LinearAPI()
    api.quick_start()


def example_queries():
    """Show common query patterns."""
    print("=== Queries ===")
    api = LinearAPI()

    # List teams
    teams = api.list_teams()
    print(f"\nTeams ({len(teams)}):")
    for t in teams:
        print(f"  [{t.get('key', '?'):5}] {t['name']}")

    # List issues for first team
    if teams:
        team_name = teams[0]["name"]
        issues = api.list_issues(team=team_name, limit=5)
        print(f"\n{team_name} issues ({len(issues)}):")
        for i in issues:
            print(
                f"  {i['identifier']} [{(i.get('state') or {}).get('name', '?')}] {i['title'][:60]}"
            )

    # Search
    results = api.search_issues("bug", limit=3)
    print(f"\nSearch 'bug' ({len(results)} results):")
    for r in results:
        print(f"  {r['identifier']} {r['title'][:60]}")


def example_health():
    """Show health check."""
    print("=== Health Check ===")
    api = LinearAPI()
    report = api.health_check()
    print(f"\nSummary: {report['summary']}")
    if report["overdue_projects"]:
        print(f"\nOverdue projects:")
        for p in report["overdue_projects"]:
            print(f"  {p['name']} (due: {p['targetDate']}, lead: {p['lead']})")
    if report["stale_issues"]:
        print(f"\nStale issues ({len(report['stale_issues'])}):")
        for i in report["stale_issues"][:5]:
            print(
                f"  {i['identifier']} {i['title'][:50]} (updated: {i['updatedAt'][:10]})"
            )


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "discover"

    examples = {
        "discover": example_discovery,
        "queries": example_queries,
        "health": example_health,
    }

    if command in examples:
        examples[command]()
    else:
        print(f"Available examples: {', '.join(examples.keys())}")
