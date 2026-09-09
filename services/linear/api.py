#!/usr/bin/env python3
"""
Linear API Client
Token Cost: ~800 tokens when loaded

GraphQL-based client for Linear project management.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

from core.base_api import BaseAPI, APIError


class LinearAPI(BaseAPI):
    """
    Linear GraphQL API wrapper.

    CAPABILITIES:
    - List/search issues, projects, teams, cycles, initiatives
    - Create and update issues, add comments
    - Health checks: stale issues, blocked work, overdue projects
    - Sprint/cycle status summaries
    - Milestone logging

    USAGE:
        api = LinearAPI()
        api.quick_start()
    """

    GRAPHQL_ENDPOINT = "https://api.linear.app/graphql"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Linear client.

        Args:
            api_key: Linear personal API key. If not provided, reads from
                     GOVSIGNALS_LINEAR_API_KEY or LINEAR_API_KEY env vars.
        """
        self.graphql_url = self.GRAPHQL_ENDPOINT

        api_key = (
            api_key
            or os.getenv("GOVSIGNALS_LINEAR_API_KEY")
            or os.getenv("LINEAR_API_KEY")
        )

        if not api_key:
            raise APIError(
                "No Linear API key found. Set GOVSIGNALS_LINEAR_API_KEY or LINEAR_API_KEY in .env"
            )

        super().__init__(
            api_key=api_key,
            base_url=self.GRAPHQL_ENDPOINT,
            requests_per_second=10,
            max_retries=3,
        )

    def _setup_auth(self):
        """Setup Linear authentication headers"""
        if self.api_key:
            self.session.headers.update(
                {
                    "Authorization": self.api_key,
                    "Content-Type": "application/json",
                }
            )

    def graphql(self, query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query against Linear's API.

        Args:
            query: GraphQL query string
            variables: Optional variables for the query

        Returns:
            Dict with query results (the 'data' key from GraphQL response)

        Raises:
            APIError: If the query fails or returns errors
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = self._make_request("POST", "", data=payload)

        if "errors" in response:
            errors = response["errors"]
            msg = "; ".join(e.get("message", str(e)) for e in errors)
            raise APIError(f"GraphQL error: {msg}")

        return response.get("data", {})

    def test_connection(self) -> bool:
        """Test if Linear API connection works"""
        try:
            result = self.graphql("{ viewer { id name } }")
            return "viewer" in result
        except Exception:
            return False

    # ============= READ OPERATIONS =============

    def list_teams(self) -> List[Dict]:
        """List all teams in the workspace."""
        result = self.graphql(
            """
            query {
                teams {
                    nodes {
                        id
                        name
                        key
                        description
                    }
                }
            }
        """
        )
        return result.get("teams", {}).get("nodes", [])

    def list_projects(
        self, status: Optional[str] = None, limit: int = 50
    ) -> List[Dict]:
        """
        List projects with optional status filter.

        Args:
            status: Filter by status name (e.g., "In Progress", "Backlog", "Planning")
            limit: Max results (default 50)

        Returns:
            List of project dicts
        """
        filter_clause = ""
        variables = {"first": limit}

        if status:
            filter_clause = ", filter: { status: { name: { eq: $status } } }"
            variables["status"] = status

        query = (
            """
            query($first: Int"""
            + (", $status: String" if status else "")
            + """) {
                projects(first: $first"""
            + filter_clause
            + """) {
                    nodes {
                        id
                        name
                        status { name }
                        lead { name }
                        targetDate
                        startDate
                        url
                    }
                }
            }
        """
        )
        result = self.graphql(query, variables)
        return result.get("projects", {}).get("nodes", [])

    def list_cycles(self, team: str) -> List[Dict]:
        """
        List cycles (sprints) for a team.

        Args:
            team: Team name or key (e.g., "OPS")

        Returns:
            List of cycle dicts with id, number, name, startsAt, endsAt, isActive
        """
        team_id = self._resolve_team_id(team)
        if not team_id:
            raise APIError(
                f"Team not found: {team}. Use list_teams() to see available teams."
            )
        result = self.graphql(
            """
            query($teamId: String!) {
                team(id: $teamId) {
                    cycles {
                        nodes { id number name startsAt endsAt isActive completedAt }
                    }
                }
            }
        """,
            {"teamId": team_id},
        )
        return result.get("team", {}).get("cycles", {}).get("nodes", [])

    def list_issues(
        self,
        team: Optional[str] = None,
        status: Optional[str] = None,
        assignee: Optional[str] = None,
        priority: Optional[int] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """
        List issues with optional filters.

        Args:
            team: Filter by team name
            status: Filter by status name (e.g., "In Progress", "Done")
            assignee: Filter by assignee name
            priority: Filter by priority (1=Urgent, 2=High, 3=Medium, 4=Low)
            limit: Max results (default 50)

        Returns:
            List of issue dicts
        """
        filters = []
        if team:
            team_id = self._resolve_team_id(team)
            if team_id:
                filters.append('team: { id: { eq: "%s" } }' % team_id)
            else:
                filters.append('team: { name: { eq: "%s" } }' % team)
        if status:
            filters.append('state: { name: { eq: "%s" } }' % status)
        if assignee:
            filters.append('assignee: { name: { eq: "%s" } }' % assignee)
        if priority is not None:
            filters.append("priority: { eq: %d }" % priority)

        filter_clause = ""
        if filters:
            filter_clause = ", filter: { " + ", ".join(filters) + " }"

        query = (
            """
            query($first: Int) {
                issues(first: $first, orderBy: updatedAt%s) {
                    nodes {
                        id
                        identifier
                        title
                        priority
                        state { name }
                        assignee { name }
                        team { name key }
                        project { name }
                        url
                        createdAt
                        updatedAt
                    }
                }
            }
        """
            % filter_clause
        )
        result = self.graphql(query, {"first": limit})
        return result.get("issues", {}).get("nodes", [])

    def get_issue(self, identifier: str) -> Optional[Dict]:
        """
        Get a single issue by identifier (e.g., "ENG-9276").

        Args:
            identifier: Issue identifier like "ENG-9276"

        Returns:
            Issue dict with full detail, or None
        """
        result = self.graphql(
            """
            query($term: String!) {
                searchIssues(term: $term, first: 1) {
                    nodes {
                        id
                        identifier
                        title
                        description
                        priority
                        state { name }
                        assignee { name email }
                        team { name key }
                        project { name }
                        labels { nodes { name } }
                        comments { nodes { body createdAt user { name } } }
                        url
                        createdAt
                        updatedAt
                    }
                }
            }
        """,
            {"term": identifier},
        )
        nodes = result.get("searchIssues", {}).get("nodes", [])
        return nodes[0] if nodes else None

    def search_issues(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search issues by text query.

        Args:
            query: Search text
            limit: Max results (default 20)

        Returns:
            List of matching issues
        """
        result = self.graphql(
            """
            query($term: String!, $first: Int) {
                searchIssues(term: $term, first: $first) {
                    nodes {
                        id
                        identifier
                        title
                        priority
                        state { name }
                        assignee { name }
                        team { name }
                        url
                        updatedAt
                    }
                }
            }
        """,
            {"term": query, "first": limit},
        )
        return result.get("searchIssues", {}).get("nodes", [])

    # ============= HEALTH & DETECTION =============

    def health_check(self) -> Dict[str, Any]:
        """
        Run a health check across the workspace.

        Returns:
            Dict with:
            - overdue_projects: Projects past their target date
            - stale_issues: Issues with no update in 7+ days that are In Progress
            - blocked_issues: Issues in a blocked/on-hold state
            - summary: Quick text summary
        """
        from datetime import datetime

        report = {
            "overdue_projects": [],
            "stale_issues": [],
            "blocked_issues": [],
            "summary": "",
        }

        today = datetime.now().strftime("%Y-%m-%d")

        # Overdue projects
        projects = self.list_projects()
        for p in projects:
            target = p.get("targetDate")
            status_name = (p.get("status") or {}).get("name", "")
            if (
                target
                and target < today
                and status_name not in ("Completed", "Canceled", "Duplicate")
            ):
                report["overdue_projects"].append(
                    {
                        "name": p["name"],
                        "targetDate": target,
                        "status": status_name,
                        "lead": (p.get("lead") or {}).get("name", "Unassigned"),
                    }
                )

        # Stale in-progress issues (no update in 7+ days)
        report["stale_issues"] = self.stale_issues(days=7)

        # Blocked issues
        report["blocked_issues"] = self.blocked_issues()

        # Summary
        parts = []
        if report["overdue_projects"]:
            parts.append(f"{len(report['overdue_projects'])} overdue projects")
        if report["stale_issues"]:
            parts.append(f"{len(report['stale_issues'])} stale issues (7+ days)")
        if report["blocked_issues"]:
            parts.append(f"{len(report['blocked_issues'])} blocked issues")
        report["summary"] = "; ".join(parts) if parts else "All clear"

        return report

    def stale_issues(self, days: int = 7) -> List[Dict]:
        """
        Find in-progress issues with no activity in N days.

        Args:
            days: Number of days without update (default 7)

        Returns:
            List of stale issue dicts
        """
        from datetime import datetime, timedelta

        cutoff = datetime.now() - timedelta(days=days)

        # Fetch in-progress issues and filter by date in Python
        # (Linear's DateTime filter types have compatibility issues)
        result = self.graphql(
            """
            query {
                issues(
                    filter: {
                        state: { type: { eq: "started" } }
                    }
                    first: 100
                    orderBy: updatedAt
                ) {
                    nodes {
                        identifier
                        title
                        assignee { name }
                        team { name }
                        state { name }
                        updatedAt
                        url
                    }
                }
            }
        """
        )
        issues = result.get("issues", {}).get("nodes", [])

        # Filter to only stale ones
        stale = []
        for issue in issues:
            updated = issue.get("updatedAt", "")
            if updated:
                updated_dt = datetime.fromisoformat(
                    updated.replace("Z", "+00:00")
                ).replace(tzinfo=None)
                if updated_dt < cutoff:
                    stale.append(issue)
        return stale

    def blocked_issues(self) -> List[Dict]:
        """
        Find issues in a blocked or on-hold state.

        Returns:
            List of blocked issue dicts
        """
        # Search for issues with blocked-related labels
        try:
            blocked = self.search_issues("label:blocked", limit=50)
        except Exception:
            blocked = []

        # Also search for on-hold
        try:
            on_hold = self.search_issues("label:on-hold", limit=50)
        except Exception:
            on_hold = []

        # Deduplicate by id
        seen = set()
        result = []
        for issue in blocked + on_hold:
            if issue.get("id") not in seen:
                seen.add(issue.get("id"))
                result.append(issue)
        return result

    def get_sprint_status(self) -> Dict[str, Any]:
        """
        Get current active cycle (sprint) status across all teams.

        Returns:
            Dict with cycle info and issue counts by state
        """
        result = self.graphql(
            """
            query {
                cycles(filter: { isActive: { eq: true } }, first: 10) {
                    nodes {
                        id
                        name
                        number
                        startsAt
                        endsAt
                        team { name key }
                        progress
                        issues {
                            nodes {
                                identifier
                                title
                                state { name type }
                                assignee { name }
                                priority
                            }
                        }
                    }
                }
            }
        """
        )
        cycles = result.get("cycles", {}).get("nodes", [])

        sprint_report = {"active_cycles": [], "summary": ""}
        for cycle in cycles:
            issues = cycle.get("issues", {}).get("nodes", [])
            by_state = {}
            for issue in issues:
                state = (issue.get("state") or {}).get("name", "Unknown")
                by_state[state] = by_state.get(state, 0) + 1

            sprint_report["active_cycles"].append(
                {
                    "team": (cycle.get("team") or {}).get("name"),
                    "name": cycle.get("name") or f"Cycle {cycle.get('number')}",
                    "starts": cycle.get("startsAt"),
                    "ends": cycle.get("endsAt"),
                    "progress": cycle.get("progress"),
                    "total_issues": len(issues),
                    "by_state": by_state,
                }
            )

        if sprint_report["active_cycles"]:
            sprint_report[
                "summary"
            ] = f"{len(sprint_report['active_cycles'])} active cycles"
        else:
            sprint_report["summary"] = "No active cycles"

        return sprint_report

    # ============= WRITE OPERATIONS =============

    def create_issue(
        self,
        team: str,
        title: str,
        description: Optional[str] = None,
        priority: Optional[int] = None,
        project: Optional[str] = None,
        assignee: Optional[str] = None,
        state: Optional[str] = None,
        due_date: Optional[str] = None,
        subscribers: Optional[List[str]] = None,
    ) -> Dict:
        """
        Create a new issue.

        Args:
            team: Team name or key (e.g., "Engineering" or "ENG")
            title: Issue title
            description: Optional markdown description
            priority: 1=Urgent, 2=High, 3=Medium, 4=Low
            project: Optional project name to add issue to
            assignee: Optional assignee name or email
            state: Optional state name (e.g., "Todo", "In Progress", "Backlog")
            due_date: Optional due date as ISO string (e.g., "2026-02-27")
            subscribers: Optional list of user names/emails to subscribe

        Returns:
            Created issue dict with id, identifier, url
        """
        team_id = self._resolve_team_id(team)
        if not team_id:
            raise APIError(
                f"Team not found: {team}. Use list_teams() to see available teams."
            )

        input_fields = ["teamId: $teamId", "title: $title"]
        var_decls = ["$teamId: String!", "$title: String!"]
        variables = {"teamId": team_id, "title": title}

        if description:
            input_fields.append("description: $description")
            var_decls.append("$description: String")
            variables["description"] = description

        if priority is not None:
            input_fields.append("priority: $priority")
            var_decls.append("$priority: Int")
            variables["priority"] = priority

        if project:
            project_id = self._resolve_project_id(project)
            if project_id:
                input_fields.append("projectId: $projectId")
                var_decls.append("$projectId: String")
                variables["projectId"] = project_id

        if assignee:
            assignee_id = self._resolve_assignee_id(assignee)
            if assignee_id:
                input_fields.append("assigneeId: $assigneeId")
                var_decls.append("$assigneeId: String")
                variables["assigneeId"] = assignee_id

        if state:
            # Get team key for state resolution
            team_key = team if len(team) <= 5 else None
            if not team_key:
                teams = self.list_teams()
                for t in teams:
                    if t["name"].lower() == team.lower():
                        team_key = t.get("key", team)
                        break
            if team_key:
                state_id = self._resolve_state_id(team_key, state)
                if state_id:
                    input_fields.append("stateId: $stateId")
                    var_decls.append("$stateId: String")
                    variables["stateId"] = state_id

        if due_date:
            input_fields.append("dueDate: $dueDate")
            var_decls.append("$dueDate: TimelessDate")
            variables["dueDate"] = due_date

        if subscribers:
            sub_ids = []
            for sub in subscribers:
                sub_id = self._resolve_assignee_id(sub)
                if sub_id:
                    sub_ids.append(sub_id)
            if sub_ids:
                input_fields.append("subscriberIds: $subscriberIds")
                var_decls.append("$subscriberIds: [String!]")
                variables["subscriberIds"] = sub_ids

        query = """
            mutation(%s) {
                issueCreate(input: { %s }) {
                    success
                    issue {
                        id
                        identifier
                        title
                        url
                        state { name }
                        assignee { name }
                        project { name }
                        dueDate
                        subscribers { nodes { name } }
                    }
                }
            }
        """ % (
            ", ".join(var_decls),
            ", ".join(input_fields),
        )

        result = self.graphql(query, variables)

        create_result = result.get("issueCreate", {})
        if not create_result.get("success"):
            raise APIError("Failed to create issue")

        return create_result.get("issue", {})

    def subscribe_to_issue(self, identifier: str, users: List[str]) -> Dict:
        """
        Subscribe users to an existing issue.

        Args:
            identifier: Issue identifier (e.g., "GTE-3")
            users: List of user names or emails to subscribe

        Returns:
            Updated issue dict with subscribers
        """
        issue = self.get_issue(identifier)
        if not issue:
            raise APIError(f"Issue not found: {identifier}")

        sub_ids = []
        for user in users:
            user_id = self._resolve_assignee_id(user)
            if user_id:
                sub_ids.append(user_id)

        if not sub_ids:
            raise APIError(f"No valid users found from: {users}")

        result = self.graphql(
            """
            mutation($issueId: String!, $subscriberIds: [String!]!) {
                issueUpdate(id: $issueId, input: { subscriberIds: $subscriberIds }) {
                    success
                    issue {
                        id
                        identifier
                        subscribers { nodes { name email } }
                    }
                }
            }
        """,
            {"issueId": issue["id"], "subscriberIds": sub_ids},
        )

        return result.get("issueUpdate", {}).get("issue", {})

    def update_issue(
        self,
        identifier: str,
        status: Optional[str] = None,
        priority: Optional[int] = None,
        assignee: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> Dict:
        """
        Update an existing issue.

        Args:
            identifier: Issue identifier (e.g., "ENG-9276")
            status: New status name (e.g., "Done", "In Progress")
            priority: New priority (1-4)
            assignee: New assignee name
            title: New title
            description: New description
            comment: Optional comment to add with the update

        Returns:
            Updated issue dict
        """
        # Find the issue ID from identifier
        issue = self.get_issue(identifier)
        if not issue:
            raise APIError(f"Issue not found: {identifier}")

        issue_id = issue["id"]
        input_fields = []
        variables = {"issueId": issue_id}

        if status:
            # Resolve status name to state ID
            state_id = self._resolve_state_id(issue["team"]["key"], status)
            if state_id:
                input_fields.append("stateId: $stateId")
                variables["stateId"] = state_id

        if priority is not None:
            input_fields.append("priority: $priority")
            variables["priority"] = priority

        if title:
            input_fields.append("title: $title")
            variables["title"] = title

        if description:
            input_fields.append("description: $description")
            variables["description"] = description

        if assignee:
            # Same resolution create_issue uses; update used to accept the
            # argument and silently drop it (found 2026-09-08 when a pager
            # mirror "assigned" an issue and Linear showed it unassigned).
            assignee_id = self._resolve_assignee_id(assignee)
            if assignee_id:
                input_fields.append("assigneeId: $assigneeId")
                variables["assigneeId"] = assignee_id

        if not input_fields and not comment:
            return issue  # Nothing to update

        updated = issue
        if input_fields:
            # Build dynamic variable declarations
            var_decls = ["$issueId: String!"]
            if "stateId" in variables:
                var_decls.append("$stateId: String")
            if "priority" in variables:
                var_decls.append("$priority: Int")
            if "title" in variables:
                var_decls.append("$title: String")
            if "description" in variables:
                var_decls.append("$description: String")
            if "assigneeId" in variables:
                var_decls.append("$assigneeId: String")

            query = """
                mutation(%s) {
                    issueUpdate(id: $issueId, input: { %s }) {
                        success
                        issue {
                            id
                            identifier
                            title
                            state { name }
                            url
                        }
                    }
                }
            """ % (
                ", ".join(var_decls),
                ", ".join(input_fields),
            )

            result = self.graphql(query, variables)
            updated = result.get("issueUpdate", {}).get("issue", issue)

        if comment:
            self.add_comment(identifier, comment)

        return updated

    def add_comment(self, identifier: str, body: str) -> Dict:
        """
        Add a comment to an issue.

        Args:
            identifier: Issue identifier (e.g., "ENG-9276")
            body: Comment body (markdown supported)

        Returns:
            Created comment dict
        """
        issue = self.get_issue(identifier)
        if not issue:
            raise APIError(f"Issue not found: {identifier}")

        result = self.graphql(
            """
            mutation($issueId: String!, $body: String!) {
                commentCreate(input: { issueId: $issueId, body: $body }) {
                    success
                    comment {
                        id
                        body
                        createdAt
                    }
                }
            }
        """,
            {"issueId": issue["id"], "body": body},
        )

        return result.get("commentCreate", {}).get("comment", {})

    def log_milestone(self, project: str, note: str) -> Dict:
        """
        Log a milestone completion as a project update.

        Args:
            project: Project name
            note: Milestone description/note

        Returns:
            Dict with project update info
        """
        # Find project
        projects = self.list_projects()
        target = None
        for p in projects:
            if p["name"].lower() == project.lower():
                target = p
                break

        if not target:
            raise APIError(
                f"Project not found: {project}. Use list_projects() to see available projects."
            )

        result = self.graphql(
            """
            mutation($projectId: String!, $body: String!) {
                projectUpdateCreate(input: {
                    projectId: $projectId
                    body: $body
                    health: onTrack
                }) {
                    success
                    projectUpdate {
                        id
                        body
                        createdAt
                    }
                }
            }
        """,
            {"projectId": target["id"], "body": note},
        )

        return result.get("projectUpdateCreate", {}).get("projectUpdate", {})

    # ============= CONSULTANCY VIEWS (multi-client) =============

    # Linear's hierarchy: Team -> Initiative -> Projects -> Issues.
    # Projects CANNOT nest under projects (no parent field). One initiative
    # per client; that client's workstreams are projects inside it.

    def list_clients(self) -> List[Dict[str, Any]]:
        """
        List all client initiatives with their contained projects and
        open-issue counts.

        Convention: each client is an Initiative in the Smoothed team;
        the client's workstreams are Projects attached to that initiative.

        Returns:
            List of dicts sorted by client name:
            [{client, status, target_date, projects: [...], open_issues}]
        """
        result = self.graphql(
            """
            query {
                initiatives {
                    nodes {
                        id
                        name
                        status
                        targetDate
                        url
                        projects {
                            nodes {
                                id
                                name
                                status { name }
                                progress
                                targetDate
                            }
                        }
                    }
                }
            }
        """
        )
        initiatives = result.get("initiatives", {}).get("nodes", [])

        issues = self.list_issues(limit=250)
        counts: Dict[str, int] = {}
        for i in issues:
            proj = (i.get("project") or {}).get("name")
            if proj:
                counts[proj] = counts.get(proj, 0) + 1

        clients = []
        for init in initiatives:
            projects = init.get("projects", {}).get("nodes", [])
            open_count = sum(counts.get(p["name"], 0) for p in projects)
            clients.append({
                "client": init["name"],
                "status": init.get("status"),
                "target_date": init.get("targetDate"),
                "projects": projects,
                "open_issues": open_count,
            })
        return sorted(clients, key=lambda c: c["client"])

    def client_overview(self, client_name: str) -> Dict[str, Any]:
        """
        Roll up everything for one client initiative: its projects and
        open-issue counts by state.

        Args:
            client_name: Initiative name (e.g., "Acme Corp")

        Returns:
            Dict with client info, projects, and issue rollup.
            Raises APIError if no initiative matches.
        """
        clients = self.list_clients()
        match = next(
            (c for c in clients if c["client"].lower() == client_name.lower()),
            None,
        )
        if not match:
            available = [c["client"] for c in clients]
            raise APIError(
                f"No client initiative named '{client_name}'. "
                f"Existing clients: {available}"
            )

        # Issues-by-state breakdown across this client's projects
        project_names = {p["name"] for p in match["projects"]}
        issues = self.list_issues(limit=250)
        by_state: Dict[str, int] = {}
        for i in issues:
            proj = (i.get("project") or {}).get("name")
            if proj in project_names:
                state = (i.get("state") or {}).get("name", "Unknown")
                by_state[state] = by_state.get(state, 0) + 1

        return {**match, "issues_by_state": by_state}

    def create_client(self, name: str, description: str = "") -> Dict[str, Any]:
        """
        Create a new client as an initiative.

        This is a consequential external action: it writes to Linear.
        Only call when the user has authorized workspace mutations.

        Args:
            name: Client name (e.g., "Acme Corp")
            description: Optional description

        Returns:
            Created initiative dict
        """
        result = self.graphql(
            """
            mutation($name: String!, $description: String) {
                initiativeCreate(
                    input: { name: $name, description: $description }
                ) {
                    success
                    initiative { id name url }
                }
            }
        """,
            {"name": name, "description": description},
        )
        return result.get("initiativeCreate", {}).get("initiative", {})

    def create_team(
        self,
        name: str,
        key: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict:
        """
        Create a new team.

        Args:
            name: Team display name (e.g., "Sunko Solar")
            key: Optional short key used for issue identifiers (e.g., "SUN").
                 If omitted, Linear auto-generates one.
            description: Optional team description.

        Returns:
            Created team dict with id, name, key, description

        Raises:
            APIError: If team creation fails.
        """
        viewer = self.graphql("{ viewer { organization { id } } }")
        org_id = ((viewer.get("viewer") or {}).get("organization") or {}).get("id")
        if not org_id:
            raise APIError("Could not resolve organization id for team creation")

        input_fields = ["name: $name", "organizationId: $organizationId"]
        var_decls = ["$name: String!", "$organizationId: String!"]
        variables = {"name": name, "organizationId": org_id}

        if key:
            input_fields.append("key: $key")
            var_decls.append("$key: String")
            variables["key"] = key

        if description:
            input_fields.append("description: $description")
            var_decls.append("$description: String")
            variables["description"] = description

        query = """
            mutation(%s) {
                teamCreate(input: { %s }) {
                    success
                    team { id name key description }
                }
            }
        """ % (", ".join(var_decls), ", ".join(input_fields))

        result = self.graphql(query, variables)
        create_result = result.get("teamCreate", {})
        if not create_result.get("success"):
            raise APIError("Failed to create team")
        return create_result.get("team", {})

    def update_team(
        self,
        team: str,
        name: Optional[str] = None,
        key: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict:
        """
        Update a team's display name, key, or description.

        Args:
            team: Team name or key to update (e.g., "Operations" or "OPS")
            name: Optional new display name (e.g., "SmoothOps")
            key: Optional new key (changes issue identifiers, e.g. OPS-1 -> SO-1)
            description: Optional new description

        Returns:
            Updated team dict with id, name, key, description

        Raises:
            APIError: If team is not found or no update fields are provided
        """
        team_id = self._resolve_team_id(team)
        if not team_id:
            raise APIError(
                f"Team not found: {team}. Use list_teams() to see available teams."
            )

        input_fields = []
        var_decls = ["$teamId: String!"]
        variables = {"teamId": team_id}

        if name:
            input_fields.append("name: $name")
            var_decls.append("$name: String")
            variables["name"] = name
        if key:
            input_fields.append("key: $key")
            var_decls.append("$key: String")
            variables["key"] = key
        if description:
            input_fields.append("description: $description")
            var_decls.append("$description: String")
            variables["description"] = description

        if not input_fields:
            raise APIError("update_team requires at least one of: name, key, description")

        query = """
            mutation(%s) {
                teamUpdate(id: $teamId, input: { %s }) {
                    success
                    team { id name key description }
                }
            }
        """ % (", ".join(var_decls), ", ".join(input_fields))

        result = self.graphql(query, variables)
        update_result = result.get("teamUpdate", {})
        if not update_result.get("success"):
            raise APIError("Failed to update team")

        return update_result.get("team", {})

    def create_project(
        self,
        name: str,
        team: str,
        description: Optional[str] = None,
        target_date: Optional[str] = None,
    ) -> Dict:
        """
        Create a new project under a team.

        Args:
            name: Project name (e.g., "Go-To-Market")
            team: Team name or key to attach the project to (e.g., "OPS")
            description: Optional project description
            target_date: Optional target date as ISO string (e.g., "2026-12-31")

        Returns:
            Created project dict with id, name, url, status

        Raises:
            APIError: If team is not found or project creation fails
        """
        team_id = self._resolve_team_id(team)
        if not team_id:
            raise APIError(
                f"Team not found: {team}. Use list_teams() to see available teams."
            )

        input_fields = ["name: $name", "teamIds: $teamIds"]
        var_decls = ["$name: String!", "$teamIds: [String!]!"]
        variables = {"name": name, "teamIds": [team_id]}

        if description:
            input_fields.append("description: $description")
            var_decls.append("$description: String")
            variables["description"] = description

        if target_date:
            input_fields.append("targetDate: $targetDate")
            var_decls.append("$targetDate: TimelessDate")
            variables["targetDate"] = target_date

        query = """
            mutation(%s) {
                projectCreate(input: { %s }) {
                    success
                    project { id name url status { name } }
                }
            }
        """ % (", ".join(var_decls), ", ".join(input_fields))

        result = self.graphql(query, variables)
        create_result = result.get("projectCreate", {})
        if not create_result.get("success"):
            raise APIError("Failed to create project")

        return create_result.get("project", {})

    def create_cycle(
        self,
        team: str,
        name: str,
        starts_at: str,
        ends_at: str,
    ) -> Dict:
        """
        Create a new cycle (sprint) for a team.

        Args:
            team: Team name or key (e.g., "OPS")
            name: Cycle name (e.g., "Week of Sep 7")
            starts_at: ISO 8601 start datetime (e.g., "2026-09-07T00:00:00.000Z")
            ends_at: ISO 8601 end datetime (e.g., "2026-09-13T23:59:59.000Z")

        Returns:
            Created cycle dict with id, number, name, startsAt, endsAt
        """
        team_id = self._resolve_team_id(team)
        if not team_id:
            raise APIError(
                f"Team not found: {team}. Use list_teams() to see available teams."
            )

        result = self.graphql(
            """
            mutation($teamId: String!, $name: String!, $startsAt: DateTime!, $endsAt: DateTime!) {
                cycleCreate(input: { teamId: $teamId, name: $name, startsAt: $startsAt, endsAt: $endsAt }) {
                    success
                    cycle { id number name startsAt endsAt }
                }
            }
        """,
            {"teamId": team_id, "name": name, "startsAt": starts_at, "endsAt": ends_at},
        )
        create_result = result.get("cycleCreate", {})
        if not create_result.get("success"):
            raise APIError("Failed to create cycle")
        return create_result.get("cycle", {})

    def create_label(
        self,
        name: str,
        color: Optional[str] = None,
        team: Optional[str] = None,
    ) -> Dict:
        """
        Create an issue label (workspace-wide, or team-scoped if team is given).

        Args:
            name: Label name (e.g., "blocked", "on-hold", "agent:zed")
            color: Optional hex color (e.g., "#EB5757"). Linear assigns one if omitted.
            team: Optional team name/key to scope the label to

        Returns:
            Created label dict with id, name
        """
        input_fields = ["name: $name"]
        var_decls = ["$name: String!"]
        variables = {"name": name}

        if color:
            input_fields.append("color: $color")
            var_decls.append("$color: String")
            variables["color"] = color

        if team:
            team_id = self._resolve_team_id(team)
            if team_id:
                input_fields.append("teamId: $teamId")
                var_decls.append("$teamId: String")
                variables["teamId"] = team_id

        query = """
            mutation(%s) {
                issueLabelCreate(input: { %s }) {
                    success
                    issueLabel { id name }
                }
            }
        """ % (", ".join(var_decls), ", ".join(input_fields))

        result = self.graphql(query, variables)
        create_result = result.get("issueLabelCreate", {})
        if not create_result.get("success"):
            raise APIError("Failed to create label")
        return create_result.get("issueLabel", {})

    # ============= DISCOVERY =============

    def discover(self, resource: Optional[str] = None) -> Dict[str, Any]:
        """
        Discover workspace structure.

        Args:
            resource: Optional specific resource ("teams", "projects", "issues")
                     If None, returns full overview.

        Returns:
            Dict with discovery results
        """
        if resource == "teams":
            teams = self.list_teams()
            return {"teams": teams, "count": len(teams)}
        elif resource == "projects":
            projects = self.list_projects()
            return {"projects": projects, "count": len(projects)}
        elif resource == "issues":
            issues = self.list_issues(limit=20)
            return {"issues": issues, "count": len(issues)}
        else:
            # Full overview
            teams = self.list_teams()
            projects = self.list_projects(limit=10)
            return {
                "workspace": self._get_viewer(),
                "teams": teams,
                "team_count": len(teams),
                "recent_projects": projects,
                "project_count": len(projects),
            }

    def _get_viewer(self) -> Dict:
        """Get current authenticated user info."""
        result = self.graphql("{ viewer { id name email } }")
        return result.get("viewer", {})

    def quick_start(self) -> None:
        """Show workspace overview in a readable format."""
        print(f"\n{'='*60}")
        print(f"Linear Workspace Overview")
        print(f"{'='*60}\n")

        if not self.test_connection():
            print("Connection failed. Check your API key.")
            return

        viewer = self._get_viewer()
        print(f"Authenticated as: {viewer.get('name')} ({viewer.get('email')})\n")

        teams = self.list_teams()
        print(f"Teams ({len(teams)}):")
        for t in teams:
            print(f"  [{t.get('key', '?'):5}] {t['name']}")

        projects = self.list_projects(limit=10)
        print(f"\nRecent Projects ({len(projects)} shown):")
        for p in projects:
            status = (p.get("status") or {}).get("name", "?")
            lead = (p.get("lead") or {}).get("name", "-")
            print(f"  [{status:12}] {p['name'][:50]}")
            print(f"               Lead: {lead} | Target: {p.get('targetDate', '-')}")

        print(f"\nQuick commands:")
        print(f"  api.list_issues(team='Engineering', limit=10)")
        print(f"  api.get_issue('ENG-123')")
        print(f"  api.search_issues('rate limit')")
        print(f"  api.health_check()")
        print(f"  api.get_sprint_status()")
        print(f"{'='*60}\n")

    def explore(self, resource: Optional[str] = None) -> None:
        """Interactive exploration - prints formatted output."""
        if resource:
            info = self.discover(resource)
            import json

            print(json.dumps(info, indent=2, default=str))
        else:
            self.quick_start()

    # ============= INTERNAL HELPERS =============

    def _resolve_team_id(self, team_name_or_key: str) -> Optional[str]:
        """Resolve a team name or key to its ID."""
        teams = self.list_teams()
        for t in teams:
            if (
                t["name"].lower() == team_name_or_key.lower()
                or t.get("key", "").lower() == team_name_or_key.lower()
            ):
                return t["id"]
        return None

    def _resolve_state_id(self, team_key: str, state_name: str) -> Optional[str]:
        """Resolve a state name to its ID for a given team."""
        # First resolve team key to team ID
        team_id = self._resolve_team_id(team_key)
        if not team_id:
            return None

        result = self.graphql(
            """
            query($teamId: String!) {
                team(id: $teamId) {
                    states {
                        nodes { id name }
                    }
                }
            }
        """,
            {"teamId": team_id},
        )
        states = result.get("team", {}).get("states", {}).get("nodes", [])
        for s in states:
            if s["name"].lower() == state_name.lower():
                return s["id"]
        return None

    def _resolve_project_id(self, project_name: str) -> Optional[str]:
        """Resolve a project name to its ID."""
        projects = self.list_projects(limit=50)
        for p in projects:
            if p["name"].lower() == project_name.lower():
                return p["id"]
        return None

    def _resolve_assignee_id(self, assignee_name: str) -> Optional[str]:
        """Resolve an assignee name or email to their user ID."""
        result = self.graphql(
            """
            query {
                users(first: 50) {
                    nodes { id name email }
                }
            }
        """
        )
        users = result.get("users", {}).get("nodes", [])
        for u in users:
            if (
                u.get("name", "").lower() == assignee_name.lower()
                or u.get("email", "").lower() == assignee_name.lower()
            ):
                return u["id"]
        return None


# ============= CLI INTERFACE =============

if __name__ == "__main__":
    import json

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python api.py test              # Test connection")
        print("  python api.py teams             # List teams")
        print("  python api.py projects          # List projects")
        print("  python api.py issues [team]     # List issues")
        print("  python api.py issue ENG-123     # Get single issue")
        print("  python api.py search 'query'    # Search issues")
        print("  python api.py health            # Health check")
        print("  python api.py sprint            # Sprint status")
        print("  python api.py explore           # Full overview")
        sys.exit(1)

    command = sys.argv[1]

    try:
        api = LinearAPI()

        if command == "test":
            if api.test_connection():
                viewer = api._get_viewer()
                print(f"Connected as: {viewer.get('name')} ({viewer.get('email')})")
            else:
                print("Connection failed")

        elif command == "teams":
            teams = api.list_teams()
            for t in teams:
                print(f"  [{t.get('key', '?'):5}] {t['name']}")

        elif command == "projects":
            status_filter = sys.argv[2] if len(sys.argv) > 2 else None
            projects = api.list_projects(status=status_filter)
            for p in projects:
                status = (p.get("status") or {}).get("name", "?")
                print(f"  [{status:12}] {p['name']}")

        elif command == "issues":
            team = sys.argv[2] if len(sys.argv) > 2 else None
            issues = api.list_issues(team=team, limit=20)
            for i in issues:
                state = (i.get("state") or {}).get("name", "?")
                print(f"  {i['identifier']:10} [{state:12}] {i['title'][:60]}")

        elif command == "issue" and len(sys.argv) > 2:
            issue = api.get_issue(sys.argv[2])
            if issue:
                print(json.dumps(issue, indent=2, default=str))
            else:
                print(f"Issue not found: {sys.argv[2]}")

        elif command == "search" and len(sys.argv) > 2:
            results = api.search_issues(sys.argv[2])
            for r in results:
                print(f"  {r['identifier']:10} {r['title'][:60]}")

        elif command == "health":
            report = api.health_check()
            print(f"Summary: {report['summary']}")
            if report["overdue_projects"]:
                print(f"\nOverdue projects ({len(report['overdue_projects'])}):")
                for p in report["overdue_projects"]:
                    print(f"  {p['name']} (due: {p['targetDate']})")
            if report["stale_issues"]:
                print(f"\nStale issues ({len(report['stale_issues'])}):")
                for i in report["stale_issues"][:10]:
                    print(
                        f"  {i['identifier']} {i['title'][:50]} (updated: {i['updatedAt'][:10]})"
                    )

        elif command == "sprint":
            sprint = api.get_sprint_status()
            print(f"Summary: {sprint['summary']}")
            for c in sprint["active_cycles"]:
                print(f"\n  {c['team']} - {c['name']}")
                print(f"  Progress: {c.get('progress', '?')}")
                for state, count in c.get("by_state", {}).items():
                    print(f"    {state}: {count}")

        elif command == "explore":
            api.quick_start()

        else:
            print(f"Unknown command: {command}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
