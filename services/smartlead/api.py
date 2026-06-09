#!/usr/bin/env python3
"""
Smartlead API Client
Token Cost: ~600 tokens when loaded

Cold email automation platform for:
- Campaign management and scheduling
- Lead tracking and categorization
- Email sequences and variants
- Analytics and deliverability
- Webhook automation
"""

import os
import json
import time
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timedelta
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from core.base_api import BaseAPI, APIError


class LeadChunkSizeError(APIError):
    """Raised when add_leads_to_campaign receives more than MAX_LEADS_PER_REQUEST (400) leads.

    Subclasses APIError so existing ``except APIError`` callers still catch it,
    but Spec C's Lead Pusher (Task 7.1) can branch on this typed error to
    re-chunk and retry without confusing it with transport/auth failures.
    """


class SmartleadAPI(BaseAPI):
    """
    Smartlead API wrapper for cold email automation.

    CAPABILITIES:
    - Create and manage email campaigns
    - Add and track leads
    - Configure email sequences
    - Monitor deliverability
    - Track replies and engagement
    - Webhook integration

    AUTHENTICATION:
    - API Key as query parameter

    RATE LIMITS:
    - 10 requests per 2 seconds

    COMMON PATTERNS:
    ```python
    api = SmartleadAPI()

    # Create campaign
    campaign = api.create_campaign('New Campaign', client_id=123)

    # Add leads
    api.add_leads_to_campaign(campaign['id'], leads_list)

    # Check analytics
    stats = api.get_campaign_analytics(campaign['id'])
    ```
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Smartlead API client.

        Args:
            api_key: Smartlead API key
        """
        self.api_key = api_key or os.getenv("SMARTLEAD_API_KEY")

        if not self.api_key:
            raise APIError("SMARTLEAD_API_KEY is required")

        super().__init__(
            api_key=self.api_key,
            base_url="https://server.smartlead.ai/api/v1",  # Correct server URL
            requests_per_second=5,  # 10 requests per 2 seconds = 5/second
        )

    def _setup_auth(self):
        """Setup authentication - Smartlead uses query params"""
        # Auth is handled in _make_request for Smartlead
        self.session.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Override to add API key to query params and retry on 429.

        Wraps the BaseAPI _make_request to add Smartlead's auth-via-query-param.
        Also catches 429 Too Many Requests (which BaseAPI treats as a
        non-retryable 4xx) and retries with exponential backoff + jitter.
        Max 5 attempts.

        Honors a body-encoded ``retry_after`` field when present; the HTTP
        ``Retry-After`` header is currently inaccessible because
        ``core/base_api.py`` strips response headers when raising APIError
        (tracked: future BaseAPI follow-up). Until that lands, header-only
        Retry-After values from Smartlead degrade silently to the
        exponential-backoff fallback.

        Fail-loud on terminal failure: APIError propagates unchanged.
        """
        import random

        # Add API key to params
        if params is None:
            params = {}
        params["api_key"] = self.api_key

        # Ensure endpoint doesn't start with /
        endpoint = endpoint.lstrip("/")

        # 429-aware retry wrapper around BaseAPI._make_request.
        # BaseAPI handles 5xx + connection errors already; 429 falls through
        # as a 4xx client error, so we wrap and re-call.
        #
        # Hand-rolled retry (not tenacity): BaseAPI's _make_request already
        # owns the auth + 5xx retry loop; wrapping super()._make_request()
        # with tenacity would create a confusing double-retry. The
        # body-encoded retry_after + exp-backoff below layers cleanly on top
        # of BaseAPI's existing 5xx handling.
        max_429_retries = 5
        attempt = 0
        last_error: Optional[APIError] = None
        while attempt < max_429_retries:
            try:
                return super()._make_request(method, endpoint, data, params, headers)
            except APIError as e:
                if e.status_code != 429:
                    raise
                # Honor Retry-After if the response carried one in body.
                # APIError stores the response body in `.response` (str|dict),
                # but the original requests.Response (and its headers) is
                # discarded by BaseAPI — best-effort: parse a numeric body or
                # fall back to exponential backoff with jitter.
                retry_after_s: float = 0.0
                resp = getattr(e, "response", None)
                try:
                    if isinstance(resp, dict):
                        retry_after_s = float(resp.get("retry_after", 0)) or 0.0
                    elif isinstance(resp, str) and resp:
                        body_json = json.loads(resp)
                        retry_after_s = float(body_json.get("retry_after", 0)) or 0.0
                except (ValueError, TypeError):
                    retry_after_s = 0.0
                if retry_after_s <= 0:
                    # Exponential backoff with jitter: 1, 2, 4, 8, 16 +/- 25%
                    base = 2**attempt
                    retry_after_s = base * (0.75 + random.random() * 0.5)
                last_error = e
                attempt += 1
                if attempt < max_429_retries:
                    time.sleep(retry_after_s)
        # Exhausted
        if last_error is not None:
            raise last_error
        raise APIError("429 retry loop exhausted with no captured error")

    # ============= CAMPAIGN OPERATIONS =============

    def create_campaign(
        self,
        name: str,
        client_id: Optional[int] = None,
        timezone: str = "America/New_York",
        settings: Optional[Dict] = None,
    ) -> Dict:
        """
        Create a new email campaign.

        REFRESHED 2026-05-20 (Spec C Phase 2): the live Smartlead API rejects
        anything but ``{name, client_id?}`` in the create-campaign body. The
        old ``timezone`` parameter and arbitrary ``settings`` dict are now
        accepted but IGNORED for the create call — apply schedule/settings
        via update_campaign_schedule / update_campaign_settings after create.
        The kept signature preserves backwards-compat for sibling callers
        (faire-us-operator / Faire_lead_gen export_to_smartlead.py).

        Args:
            name: Campaign name
            client_id: Client/workspace ID (optional)
            timezone: IGNORED (kept for backwards-compat; set via schedule)
            settings: IGNORED (kept for backwards-compat; set via update_campaign_settings)

        Returns:
            Created campaign details (id, status='DRAFTED', name, ...)

        Example:
            campaign = api.create_campaign('Q1 Outreach')
            api.update_campaign_schedule(campaign['id'], {...})
            api.update_campaign_settings(campaign['id'], {...})
        """
        payload: Dict[str, Any] = {"name": name}
        if client_id is not None:
            payload["client_id"] = client_id
        # timezone/settings intentionally NOT included — live API rejects them.

        return self._make_request("POST", "campaigns/create", data=payload)

    # Page size for paginated /campaigns/list scans. Smartlead's docs/behavior
    # do not pin this exactly; 100 is the conservative default observed in
    # the field. Tunable via list_campaigns(limit=...).
    _CAMPAIGN_LIST_PAGE_SIZE = 100
    # Sanity cap (NOT an expected workspace size) — protects get_campaign_by_name
    # from infinite loops if Smartlead's pagination ever stops honoring offset.
    _CAMPAIGN_LIST_SAFETY_CAP = 5000

    def get_campaign_by_name(self, name: str) -> Optional[Dict]:
        """Look up a campaign by exact name match (lookup-before-create).

        Smartlead's ``GET /campaigns/list`` does not server-side filter by
        name reliably, so we scan the list client-side. The endpoint is
        paginated (page size ~100); we iterate ``offset`` until a page comes
        back short or empty. Returns the first case-sensitive equality match,
        or None.

        Raises:
            APIError: if we scan more than ``_CAMPAIGN_LIST_SAFETY_CAP``
                (5000) campaigns without finishing — indicates pagination is
                broken or workspace has grown past sanity cap.

        Args:
            name: Exact campaign name to match

        Returns:
            ``{"id": int, "name": str, ...}`` or None if not found
        """
        page_size = self._CAMPAIGN_LIST_PAGE_SIZE
        offset = 0
        scanned = 0
        while True:
            page = self.list_campaigns(offset=offset, limit=page_size) or []
            for c in page:
                if c.get("name") == name:
                    return c
            scanned += len(page)
            # Short or empty page → done.
            if len(page) < page_size:
                return None
            if scanned >= self._CAMPAIGN_LIST_SAFETY_CAP:
                raise APIError(
                    f"get_campaign_by_name: hit safety cap "
                    f"({self._CAMPAIGN_LIST_SAFETY_CAP} campaigns scanned); "
                    f"pagination broken or campaign count exceeds cap."
                )
            offset += page_size

    def get_campaign(self, campaign_id: int) -> Dict:
        """
        Get campaign details by ID.

        Args:
            campaign_id: Campaign ID

        Returns:
            Campaign details
        """
        return self._make_request("GET", f"campaigns/{campaign_id}")

    def list_campaigns(
        self,
        client_id: Optional[int] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        """
        List campaigns.

        ``offset``/``limit`` are additive — when omitted the call preserves
        the original no-arg behavior (Smartlead returns its default page).
        Pass both to walk pages explicitly (see ``get_campaign_by_name`` for
        the canonical paginating consumer).

        Args:
            client_id: Filter by client ID
            offset: Pagination offset (0-indexed). When None, no offset sent.
            limit: Page size. When None, no limit sent.

        Returns:
            List of campaigns
        """
        params: Dict[str, Any] = {}
        if client_id:
            params["client_id"] = client_id
        if offset is not None:
            params["offset"] = offset
        if limit is not None:
            params["limit"] = limit

        return self._make_request("GET", "campaigns/list", params=params)

    def update_campaign_settings(self, campaign_id: int, settings: Dict) -> Dict:
        """
        Update campaign settings.

        Args:
            campaign_id: Campaign ID
            settings: Settings to update

        Returns:
            Updated campaign

        Example:
            api.update_campaign_settings(
                123,
                {
                    'track_opens': True,
                    'track_link_clicks': True,
                    'stop_on_reply': True
                }
            )
        """
        return self._make_request(
            "POST", f"campaigns/{campaign_id}/settings", data=settings
        )

    def update_campaign_schedule(self, campaign_id: int, schedule: Dict) -> Dict:
        """
        Update campaign sending schedule.

        Args:
            campaign_id: Campaign ID
            schedule: Schedule configuration

        Returns:
            Updated campaign

        Example:
            api.update_campaign_schedule(
                123,
                {
                    'days_of_week': [1, 2, 3, 4, 5],  # Mon-Fri
                    'start_hour': '09:00',
                    'end_hour': '17:00',
                    'timezone': 'America/New_York'
                }
            )
        """
        return self._make_request(
            "POST", f"campaigns/{campaign_id}/schedule", data=schedule
        )

    def pause_campaign(self, campaign_id: int) -> Dict:
        """Pause a campaign"""
        return self._make_request("POST", f"campaigns/{campaign_id}/pause")

    def resume_campaign(self, campaign_id: int) -> Dict:
        """Resume a paused campaign"""
        return self._make_request("POST", f"campaigns/{campaign_id}/resume")

    def get_campaign_sequence(self, campaign_id: int) -> Dict:
        """
        Get email sequences for a campaign.

        Args:
            campaign_id: Campaign ID

        Returns:
            Campaign sequences
        """
        return self._make_request("GET", f"campaigns/{campaign_id}/sequences")

    # ============= SPEC C BRIDGE ALIASES + NEW =============
    # (Phase 0.3 live-API verified 2026-05-20. These names match the Spec C
    # bridge plan; existing method names above are preserved for
    # backwards-compat with sibling callers.)

    def get_sequence(self, campaign_id: int) -> Dict:
        """Spec C alias for ``get_campaign_sequence``.

        Returns the campaign's sequence steps. Used by post-provision
        verification (Task 6.2) to assert body-only steps and that steps
        2/3 have empty subjects.
        """
        return self.get_campaign_sequence(campaign_id)

    def save_sequence(self, campaign_id: int, sequence: Dict) -> Dict:
        """Write the full sequence for a campaign.

        Endpoint: ``POST /campaigns/{id}/sequences``.
        The full payload (including all steps) must be sent; partial updates
        are not supported by the live API.

        Args:
            campaign_id: Campaign ID
            sequence: Sequence dict with ``sequences: [{seq_number, ...}]``

        Returns:
            ``{"ok": True, "data": {"sequences": [{seqNumber, id}, ...]}}``
        """
        return self._make_request(
            "POST", f"campaigns/{campaign_id}/sequences", data=sequence
        )

    def attach_email_accounts(
        self, campaign_id: int, email_account_ids: List[int]
    ) -> Dict:
        """Attach mailboxes to a campaign.

        Endpoint: ``POST /campaigns/{id}/email-accounts``.
        Idempotent — re-attaching already-associated accounts returns
        ``{"ok": True, "result": [], "message": "Email account already
        associated - <ids>"}``.

        Args:
            campaign_id: Campaign ID
            email_account_ids: List of mailbox IDs to attach

        Returns:
            ``{"ok": True, ...}``
        """
        return self._make_request(
            "POST",
            f"campaigns/{campaign_id}/email-accounts",
            data={"email_account_ids": email_account_ids},
        )

    def set_schedule(self, campaign_id: int, schedule: Dict) -> Dict:
        """Spec C alias for ``update_campaign_schedule``.

        Phase 0.3 contract notes:
          - ``max_new_leads_per_day`` is REQUIRED on write.
          - Field-name asymmetry: write ``min_time_btw_emails`` (no 'n');
            GET echoes ``min_time_btwn_emails`` (with 'n'). Callers should
            be tolerant on read.
        """
        return self.update_campaign_schedule(campaign_id, schedule)

    def update_settings(self, campaign_id: int, settings: Dict) -> Dict:
        """Spec C alias for ``update_campaign_settings``.

        Phase 0.3 contract notes:
          - ``track_settings`` is an OPT-OUT enum ARRAY, not booleans.
            ``[]`` means open+click tracking ON;
            ``["DONT_TRACK_EMAIL_OPEN", "DONT_TRACK_LINK_CLICK"]`` = both off.
          - ``stop_lead_settings`` is a single enum string
            (e.g. ``"REPLY_TO_AN_EMAIL"``).
          - ``unsubscribe_text`` is the SOLE opt-out lever; any non-empty
            value triggers Smartlead's implicit List-Unsubscribe + RFC 8058
            header injection (empirically verified 2026-05-20). Set ``""``
            to disable.
          - ``auto_pause_domain_leads_on_reply`` is accepted on POST but
            does NOT echo back on GET (behavior-only).
        """
        return self.update_campaign_settings(campaign_id, settings)

    _STATUS_TRANSLATIONS = {
        # Semantic name (used by bridge) -> live-API write value.
        # Verified live 2026-06-09: POST /campaigns/{id}/status accepts ONLY
        # START / PAUSED / STOPPED. Earlier PAUSE/STOP values were rejected 400.
        "ACTIVE": "START",
        "START": "START",
        "PAUSED": "PAUSED",
        "PAUSE": "PAUSED",
        "STOPPED": "STOPPED",
        "STOP": "STOPPED",
    }

    @classmethod
    def _translate_status(cls, semantic_status: str) -> str:
        """Translate a semantic status name to the live-API write value.

        Raises APIError on unknown status to fail loud rather than send a
        request the API will reject silently.
        """
        try:
            return cls._STATUS_TRANSLATIONS[semantic_status.upper()]
        except KeyError as e:
            raise APIError(
                f"Unknown semantic status '{semantic_status}'. "
                f"Expected one of: {sorted(cls._STATUS_TRANSLATIONS.keys())}"
            ) from e

    def set_status(self, campaign_id: int, semantic_status: str) -> Dict:
        """Set campaign status with semantic-name translation.

        Endpoint: ``POST /campaigns/{id}/status``.
        The live API write-value vocabulary (``START``/``PAUSE``/``STOP``)
        differs from the GET read-value vocabulary (``ACTIVE``/``PAUSED``/
        ``STOPPED``); this method accepts either and translates.

        Args:
            campaign_id: Campaign ID
            semantic_status: One of ACTIVE|PAUSED|STOPPED (or the literal
                START|PAUSE|STOP) — case-insensitive.

        Returns:
            ``{"ok": True}``
        """
        write_value = self._translate_status(semantic_status)
        return self._make_request(
            "POST",
            f"campaigns/{campaign_id}/status",
            data={"status": write_value},
        )

    # ============= LEAD OPERATIONS =============

    # Smartlead hard cap on /campaigns/{id}/leads per request.
    MAX_LEADS_PER_REQUEST = 400

    def add_leads_to_campaign(
        self, campaign_id: int, leads: List[Dict], settings: Optional[Dict] = None
    ) -> Dict:
        """Add leads to a campaign.

        REFRESHED 2026-05-20 (Spec C Phase 2). The live endpoint is
        ``POST /campaigns/{id}/leads`` with body
        ``{"lead_list": [...], "settings": {...}}`` — NOT the legacy
        ``POST /leads/add`` with ``{"campaign_id": ..., "leads": [...]}``.

        Defensive guardrail: raises APIError if ``len(leads) > 400`` (the
        Smartlead hard cap). Callers responsible for chunking should chunk
        upstream; this wrapper does NOT auto-chunk to avoid silent partial
        success.

        Args:
            campaign_id: Campaign ID
            leads: List of lead dicts, each shaped like::

                {
                    "email": "x@y.com",
                    "first_name": "Brent",
                    "company_name": "Bellows",
                    "custom_fields": {"subject": ..., "body_1": ..., ...}
                }

            settings: Per-import settings such as
                ``{"ignore_global_block_list": True, ...}``

        Returns:
            ``{"ok": True, "upload_count": int, "total_leads": int, ...}``
        """
        if not leads:
            raise APIError(
                "add_leads_to_campaign: empty lead list — upstream chunker bug?"
            )
        if len(leads) > self.MAX_LEADS_PER_REQUEST:
            raise LeadChunkSizeError(
                f"add_leads_to_campaign got {len(leads)} leads; Smartlead "
                f"hard cap is {self.MAX_LEADS_PER_REQUEST}. Chunk upstream."
            )
        payload: Dict[str, Any] = {"lead_list": leads}
        if settings:
            payload["settings"] = settings
        return self._make_request(
            "POST", f"campaigns/{campaign_id}/leads", data=payload
        )

    @staticmethod
    def parse_add_leads_response(resp: Dict) -> Dict:
        """Parse the response from ``add_leads_to_campaign`` into a normalized shape.

        Returns:
            ``{added_count, total_leads, skipped_leads, duplicate_count,
                invalid_email_count, block_count, bounce_count,
                already_added_to_campaign, unsubscribed_leads,
                is_lead_limit_exhausted, lead_import_stopped_count}``
        """
        return {
            "added_count": resp.get("upload_count", 0),
            "total_leads": resp.get("total_leads", 0),
            "skipped_leads": resp.get("invalid_emails", []) or [],
            "duplicate_count": resp.get("duplicate_count", 0),
            "invalid_email_count": resp.get("invalid_email_count", 0),
            "block_count": resp.get("block_count", 0),
            "bounce_count": resp.get("bounce_count", 0),
            "already_added_to_campaign": resp.get("already_added_to_campaign", 0),
            "unsubscribed_leads": resp.get("unsubscribed_leads", []) or [],
            "is_lead_limit_exhausted": resp.get("is_lead_limit_exhausted", False),
            "lead_import_stopped_count": resp.get("lead_import_stopped_count", 0),
        }

    def get_lead_by_email(self, campaign_id: int, email: str) -> Dict:
        """Look up a lead in a campaign by email address.

        Endpoint: ``GET /campaigns/{id}/leads/by-email?email=...``.
        Used for post-provision C-5a verification (Task 6.2) and for
        resolving lead_id from a Bridge Pusher context.

        Args:
            campaign_id: Campaign ID
            email: Lead email

        Returns:
            Full lead object including ``id``, ``email``, ``custom_fields``,
            ``lead_campaign_data``, etc.
        """
        return self._make_request(
            "GET",
            f"campaigns/{campaign_id}/leads/by-email",
            params={"email": email},
        )

    @staticmethod
    def parse_lead(resp: Dict) -> Dict:
        """Normalize a lead response into a stable subset.

        Returns:
            ``{id, email, first_name, last_name, company_name,
                custom_fields, lead_campaign_data, is_unsubscribed}``
        """
        return {
            "id": resp.get("id"),
            "email": resp.get("email"),
            "first_name": resp.get("first_name"),
            "last_name": resp.get("last_name"),
            "company_name": resp.get("company_name"),
            "custom_fields": resp.get("custom_fields", {}) or {},
            "lead_campaign_data": resp.get("lead_campaign_data", []) or [],
            "is_unsubscribed": resp.get("is_unsubscribed", False),
        }

    def get_lead(self, lead_id: int) -> Dict:
        """
        Get lead details.

        Args:
            lead_id: Lead ID

        Returns:
            Lead details
        """
        return self._make_request("GET", f"leads/{lead_id}")

    def get_lead_status(self, campaign_id: int, email: str) -> Dict:
        """
        Get lead status in a campaign.

        Args:
            campaign_id: Campaign ID
            email: Lead email

        Returns:
            Lead status (STARTED, COMPLETED, BLOCKED, INPROGRESS)
        """
        params = {"campaign_id": campaign_id, "email": email}
        return self._make_request("GET", "leads/status", params=params)

    def update_lead_category(self, lead_id: int, category: str) -> Dict:
        """
        Update lead category/status.

        Args:
            lead_id: Lead ID
            category: New category

        Returns:
            Updated lead
        """
        return self._make_request(
            "POST", f"leads/{lead_id}/category", data={"category": category}
        )

    def block_lead(self, email: str, reason: Optional[str] = None) -> Dict:
        """
        Add lead to block list.

        Args:
            email: Email to block
            reason: Block reason

        Returns:
            Block result
        """
        data = {"email": email}
        if reason:
            data["reason"] = reason

        return self._make_request("POST", "leads/block", data=data)

    def unblock_lead(self, email: str) -> Dict:
        """Remove lead from block list"""
        return self._make_request("POST", "leads/unblock", data={"email": email})

    def get_lead_activities(
        self, lead_id: int, campaign_id: Optional[int] = None
    ) -> List[Dict]:
        """
        Get lead activity history.

        Args:
            lead_id: Lead ID
            campaign_id: Filter by campaign

        Returns:
            List of activities
        """
        params = {"lead_id": lead_id}
        if campaign_id:
            params["campaign_id"] = campaign_id

        return self._make_request("GET", "leads/activities", params=params)

    # ============= ANALYTICS & REPORTING =============

    def get_campaign_analytics(self, campaign_id: int) -> Dict:
        """
        Get campaign performance analytics.

        Args:
            campaign_id: Campaign ID

        Returns:
            Analytics data including sent, opened, clicked, replied
        """
        return self._make_request("GET", f"campaigns/{campaign_id}/analytics")

    def get_lead_statistics(self, campaign_id: int) -> Dict:
        """
        Get detailed lead statistics for a campaign.

        Args:
            campaign_id: Campaign ID

        Returns:
            Lead statistics by status and category
        """
        # KNOWN-STALE 2026-06-03: endpoint returns 404 against live API.
        # Do not use for monitoring; use get_campaign_analytics instead.
        # Repair endpoint path before relying on this.
        return self._make_request("GET", f"campaigns/{campaign_id}/lead-stats")

    def get_campaign_summary(self, campaign_id: int) -> Dict:
        """
        Get comprehensive campaign summary.

        Args:
            campaign_id: Campaign ID

        Returns:
            Complete campaign overview with all metrics
        """
        # KNOWN-STALE 2026-06-03: endpoint returns 404 against live API.
        # Do not use for monitoring; use get_campaign_analytics instead.
        # Repair endpoint path before relying on this.
        return self._make_request("GET", f"campaigns/{campaign_id}/summary")

    def get_email_replies(
        self, campaign_id: Optional[int] = None, lead_id: Optional[int] = None
    ) -> List[Dict]:
        """
        Get email replies.

        Args:
            campaign_id: Filter by campaign
            lead_id: Filter by lead

        Returns:
            List of email replies
        """
        # KNOWN-STALE 2026-06-03: endpoint returns 404 against live API.
        # Do not use for monitoring; use get_campaign_analytics instead.
        # Repair endpoint path before relying on this.
        params = {}
        if campaign_id:
            params["campaign_id"] = campaign_id
        if lead_id:
            params["lead_id"] = lead_id

        return self._make_request("GET", "emails/replies", params=params)

    def get_bounce_report(
        self,
        campaign_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict]:
        """
        Get email bounce report.

        Args:
            campaign_id: Filter by campaign
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Bounce report
        """
        # KNOWN-STALE 2026-06-03: endpoint returns 404 against live API.
        # Do not use for monitoring; use get_campaign_analytics instead.
        # Repair endpoint path before relying on this.
        params = {}
        if campaign_id:
            params["campaign_id"] = campaign_id
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        return self._make_request("GET", "analytics/bounces", params=params)

    def export_campaign_data(
        self, campaign_id: int, export_type: str = "csv"
    ) -> Union[str, Dict]:
        """
        Export campaign data.

        Args:
            campaign_id: Campaign ID
            export_type: Format (csv, json)

        Returns:
            Export data or download URL
        """
        params = {"campaign_id": campaign_id, "type": export_type}
        return self._make_request("GET", "export/campaign", params=params)

    # ============= EMAIL ACCOUNT OPERATIONS =============

    def list_email_accounts(self) -> List[Dict]:
        """
        List all email accounts.

        Returns:
            List of email accounts with warmup status
        """
        return self._make_request("GET", "email-accounts")

    def get_email_account(self, account_id: int) -> Dict:
        """
        Get email account details.

        Args:
            account_id: Email account ID

        Returns:
            Email account details including warmup status
        """
        return self._make_request("GET", f"email-accounts/{account_id}")

    def add_email_account(
        self,
        email: str,
        smtp_host: str,
        smtp_port: int,
        smtp_username: str,
        smtp_password: str,
        imap_host: Optional[str] = None,
        imap_port: Optional[int] = None,
        imap_username: Optional[str] = None,
        imap_password: Optional[str] = None,
        warmup_enabled: bool = True,
    ) -> Dict:
        """
        Add a new email account for sending.

        Args:
            email: Email address
            smtp_host: SMTP server host
            smtp_port: SMTP port
            smtp_username: SMTP username
            smtp_password: SMTP password
            imap_host: IMAP server host (for reply tracking)
            imap_port: IMAP port
            imap_username: IMAP username
            imap_password: IMAP password
            warmup_enabled: Enable warmup for this account

        Returns:
            Created email account details
        """
        data = {
            "email": email,
            "smtp_host": smtp_host,
            "smtp_port": smtp_port,
            "smtp_username": smtp_username,
            "smtp_password": smtp_password,
            "warmup_enabled": warmup_enabled,
        }

        if imap_host:
            data.update(
                {
                    "imap_host": imap_host,
                    "imap_port": imap_port,
                    "imap_username": imap_username,
                    "imap_password": imap_password,
                }
            )

        return self._make_request("POST", "email-accounts", data=data)

    def update_email_account_warmup(
        self, account_id: int, warmup_enabled: bool
    ) -> Dict:
        """
        Enable or disable warmup for an email account.

        Args:
            account_id: Email account ID
            warmup_enabled: Enable/disable warmup

        Returns:
            Updated account details
        """
        return self._make_request(
            "POST",
            f"email-accounts/{account_id}/warmup",
            data={"warmup_enabled": warmup_enabled},
        )

    def update_email_account(self, account_id: int, **kwargs) -> Dict:
        """
        Update email account settings.

        Args:
            account_id: Email account ID
            **kwargs: Fields to update. Common fields:
                - different_reply_to_address (str): Reply-to email address
                - is_different_imap_account (bool): True if reply-to uses different IMAP
                - imap_username (str): IMAP username for reply-to account
                - imap_password (str): IMAP password for reply-to account
                - imap_host (str): IMAP server host
                - imap_port (int): IMAP port
                - imap_port_type (str): 'SSL' or 'TLS'
                - max_email_per_day (int): Daily send limit
                - signature (str): Email signature
                - bcc (str): BCC email address
                - custom_tracking_url (str): Custom tracking domain

        Returns:
            Updated account details

        Example:
            # Set unified reply-to address
            api.update_email_account(
                account_id=123,
                different_reply_to_address='replies@company.com',
                is_different_imap_account=True,
                imap_username='replies@company.com',
                imap_password='app-password',
                imap_host='imap.gmail.com',
                imap_port=993,
                imap_port_type='SSL'
            )
        """
        return self._make_request("POST", f"email-accounts/{account_id}", data=kwargs)

    def set_reply_to_address(
        self,
        account_id: int,
        reply_to_email: str,
        imap_host: Optional[str] = None,
        imap_port: Optional[int] = None,
        imap_username: Optional[str] = None,
        imap_password: Optional[str] = None,
        imap_port_type: str = "SSL",
    ) -> Dict:
        """
        Set a different reply-to address for an email account.

        WARNING: this method calls POST /email-accounts/save which re-runs
        SMTP verification and FAILS on OAuth Gmail/Outlook accounts. For
        signature-only updates on OAuth accounts, use ``set_signature()``
        (POST /email-accounts/{id} partial update) — see set_signature
        docstring.

        Args:
            account_id: Email account ID
            reply_to_email: Email address for replies
            imap_host: IMAP server (e.g., 'imap.gmail.com')
            imap_port: IMAP port (e.g., 993)
            imap_username: IMAP login (usually same as reply_to_email)
            imap_password: IMAP password/app-password
            imap_port_type: 'SSL' or 'TLS'

        Returns:
            Updated account details

        Example:
            api.set_reply_to_address(
                account_id=123,
                reply_to_email='replies@company.com',
                imap_host='imap.gmail.com',
                imap_port=993,
                imap_username='replies@company.com',
                imap_password='your-app-password'
            )

        Note:
            For replies to appear in Smartlead's Master Inbox, the
            reply-to email must also be added as a separate email
            account in Smartlead.
        """
        # Fetch existing account data first
        existing = self.get_email_account(account_id)
        account_type = existing.get("type", "SMTP")

        # Build update payload with required fields from existing account
        # Note: API expects 'user_name' not 'username'
        warmup = existing.get("warmup_details", {})
        data = {
            "id": account_id,
            "type": account_type,  # GMAIL, OUTLOOK, SMTP, ZOHO
            "from_name": existing.get("from_name", ""),
            "from_email": existing.get("from_email", ""),
            "user_name": existing.get("username", ""),  # API uses user_name
            "password": existing.get("password", ""),  # Required field
            "different_reply_to_address": reply_to_email,
            "warmup_enabled": warmup.get("status") == "ACTIVE",
            "max_email_per_day": existing.get("message_per_day", 50),
        }

        # Include SMTP details - use defaults for OAuth accounts if not set
        if existing.get("smtp_host"):
            data["smtp_host"] = existing.get("smtp_host")
            data["smtp_port"] = existing.get("smtp_port")
        elif account_type == "GMAIL":
            data["smtp_host"] = "smtp.gmail.com"
            data["smtp_port"] = 465
        elif account_type == "OUTLOOK":
            data["smtp_host"] = "smtp.office365.com"
            data["smtp_port"] = 587

        # Include IMAP details - use existing or defaults
        if existing.get("imap_host"):
            data["imap_host"] = existing.get("imap_host")
            data["imap_port"] = existing.get("imap_port")
        elif account_type == "GMAIL":
            data["imap_host"] = "imap.gmail.com"
            data["imap_port"] = 993
        elif account_type == "OUTLOOK":
            data["imap_host"] = "outlook.office365.com"
            data["imap_port"] = 993

        return self._make_request("POST", "email-accounts/save", data=data)

    def delete_email_account(self, account_id: int) -> bool:
        """
        Delete an email account.

        Args:
            account_id: Email account ID

        Returns:
            True if successful
        """
        self._make_request("DELETE", f"email-accounts/{account_id}")
        return True

    def get_warmup_status(self, account_id: int) -> Dict:
        """
        Get warmup status for an email account.

        Args:
            account_id: Email account ID

        Returns:
            Warmup statistics and progress
        """
        return self._make_request("GET", f"email-accounts/{account_id}/warmup")

    def set_signature(self, email_account_id: int, signature_text: str) -> Dict:
        """Set the per-mailbox signature via partial-update endpoint.

        CRITICAL GOTCHA: do NOT use ``POST /email-accounts/save`` for this —
        that endpoint re-runs SMTP verification and FAILS on OAuth Gmail /
        Outlook accounts. The partial-update endpoint
        ``POST /email-accounts/{id}`` accepts ``{"signature": ...}`` alone
        and works on OAuth mailboxes.

        Signature is per-EMAIL-ACCOUNT (mailbox), not per-campaign. Used by
        Spec C C-5 (physical address in signature for CAN-SPAM).

        Args:
            email_account_id: Mailbox ID
            signature_text: HTML or plain signature

        Returns:
            ``{"ok": True, "message": "...", "emailAccountId": int}``
        """
        return self._make_request(
            "POST",
            f"email-accounts/{email_account_id}",
            data={"signature": signature_text},
        )

    # ============= BLOCK LIST =============

    def get_global_block_list(self, limit: int = 1000, offset: int = 0) -> List[Dict]:
        """Fetch the user-level global domain block list.

        Endpoint: ``GET /leads/get-domain-block-list``.
        Used by Spec C Wave Assembler (Task 4.1) for fail-closed live
        anti-join against Smartlead's block list.

        NOTE: response shape is not yet fixture-captured as of 2026-05-20;
        this method assumes a paginated list-of-dicts (likely
        ``[{domain, reason, created_at}, ...]``). The contract test for
        this method is currently skipped pending fixture capture.

        Args:
            limit: Page size (default 1000)
            offset: Page offset

        Returns:
            List of blocked-domain dicts.
        """
        return self._make_request(
            "GET",
            "leads/get-domain-block-list",
            params={"limit": limit, "offset": offset},
        )

    # ============= WEBHOOK OPERATIONS =============

    def register_webhook(
        self,
        url: str,
        events: List[str],
        scope: str = "user",
        campaign_id: Optional[int] = None,
    ) -> Dict:
        """
        Register a webhook endpoint.

        Args:
            url: Webhook URL
            events: List of events to subscribe
            scope: Webhook scope (user, client, campaign)
            campaign_id: Campaign ID for campaign-scoped webhooks

        Returns:
            Webhook registration details

        Example:
            api.register_webhook(
                'https://example.com/webhook',
                ['EMAIL_REPLY', 'EMAIL_OPENED'],
                scope='campaign',
                campaign_id=123
            )
        """
        data = {"url": url, "events": events, "scope": scope}

        if campaign_id and scope == "campaign":
            data["campaign_id"] = campaign_id

        return self._make_request("POST", "webhooks/register", data=data)

    def list_webhooks(self) -> List[Dict]:
        """List all registered webhooks"""
        return self._make_request("GET", "webhooks/list")

    def delete_webhook(self, webhook_id: int) -> Dict:
        """Delete a webhook"""
        return self._make_request("DELETE", f"webhooks/{webhook_id}")

    def create_webhook(
        self,
        url: str,
        events: List[str],
        association_type: int = 1,
        hmac_secret: Optional[str] = None,
        campaign_id: Optional[int] = None,
    ) -> Dict:
        """Spec C create-webhook wrapper for the bridge ingester (Task 8.1).

        Endpoint: ``POST /webhook/create`` (singular, distinct from the older
        ``webhooks/register`` endpoint).

        Args:
            url: Webhook URL
            events: List of event types (EMAIL_REPLY, EMAIL_OPENED, ...)
            association_type: 1 = user-level (default), 2 = client-level,
                3 = campaign-level. Spec C uses user-level (1).
            hmac_secret: Shared secret for HMAC signing of webhook bodies
            campaign_id: Required iff ``association_type == 3``

        Returns:
            Webhook registration details
        """
        if association_type == 3 and campaign_id is None:
            raise APIError(
                "create_webhook: association_type=3 (campaign-level) "
                "requires a non-None campaign_id"
            )
        data: Dict[str, Any] = {
            "url": url,
            "events": events,
            "association_type": association_type,
        }
        if hmac_secret:
            data["hmac_secret"] = hmac_secret
        if association_type == 3 and campaign_id is not None:
            data["campaign_id"] = campaign_id
        return self._make_request("POST", "webhook/create", data=data)

    # ============= HELPER METHODS =============

    def discover(self, resource: Optional[str] = None) -> Dict:
        """
        Discover available resources and capabilities.

        Args:
            resource: Specific resource to explore

        Returns:
            Discovery information
        """
        if resource == "campaigns":
            try:
                campaigns = self.list_campaigns()
                return {
                    "total": len(campaigns),
                    "campaigns": [
                        {
                            "id": c.get("id"),
                            "name": c.get("name"),
                            "status": c.get("status"),
                            "created": c.get("created_at"),
                        }
                        for c in campaigns[:10]
                    ],
                }
            except:
                return {"error": "Could not list campaigns - check API key"}

        elif resource == "email_accounts":
            try:
                accounts = self.list_email_accounts()
                return {
                    "total": len(accounts),
                    "accounts": [
                        {
                            "id": a.get("id"),
                            "email": a.get("email"),
                            "warmup_enabled": a.get("warmup_enabled"),
                            "status": a.get("status"),
                        }
                        for a in accounts[:10]
                    ],
                }
            except:
                return {"error": "Could not list email accounts - check API key"}

        elif resource == "webhooks":
            return {
                "available_events": [
                    "EMAIL_SENT",
                    "EMAIL_OPENED",
                    "EMAIL_CLICKED",
                    "EMAIL_REPLY",
                    "EMAIL_BOUNCED",
                    "LEAD_UNSUBSCRIBED",
                    "LEAD_CATEGORY_UPDATED",
                    "CAMPAIGN_STATUS_CHANGE",
                    "MANUAL_STEP_REACHED",
                ],
                "scopes": ["user", "client", "campaign"],
            }
        else:
            # General discovery
            return {
                "api_version": "v1",
                "base_url": self.base_url,
                "resources": [
                    "campaigns",
                    "leads",
                    "email_accounts",
                    "analytics",
                    "webhooks",
                ],
                "rate_limit": "10 requests per 2 seconds",
                "features": [
                    "Campaign management",
                    "Lead tracking",
                    "Email account management",
                    "Email warmup",
                    "Analytics & reporting",
                    "Webhook automation",
                    "CSV/JSON exports",
                ],
            }

    def quick_start(self) -> None:
        """Display quick start information"""
        print("🚀 Smartlead API Quick Start")
        print("=" * 50)

        # Test connection
        try:
            if self.test_connection():
                print("✅ Connected to Smartlead")
            else:
                print("❌ Connection failed")
                return
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return

        # Show campaigns
        try:
            campaigns = self.list_campaigns()
            print(f"\n📧 Campaigns: {len(campaigns)}")
            for campaign in campaigns[:5]:
                print(f"  - {campaign.get('name')} (ID: {campaign.get('id')})")
        except Exception as e:
            print(f"Could not list campaigns: {e}")

        print("\n📝 Common Operations:")
        print("  # Create campaign")
        print("  campaign = api.create_campaign('New Campaign', client_id=1)")
        print("\n  # Add leads")
        print("  leads = [{'email': 'test@example.com', 'first_name': 'Test'}]")
        print("  api.add_leads_to_campaign(campaign_id, leads)")
        print("\n  # Check analytics")
        print("  stats = api.get_campaign_analytics(campaign_id)")
        print("\n  # Setup webhook")
        print("  api.register_webhook(url, ['EMAIL_REPLY'])")

    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            # Try to list campaigns with limit
            self._make_request("GET", "campaigns/list", params={"limit": 1})
            return True
        except Exception:
            return False


# ============= CLI INTERFACE =============

if __name__ == "__main__":
    import sys

    api = SmartleadAPI()

    if len(sys.argv) < 2:
        print("Smartlead API CLI")
        print("=" * 40)
        print("Usage:")
        print("  python api.py test                  # Test connection")
        print("  python api.py quick_start            # Show quick start")
        print("  python api.py discover               # Show resources")
        print("  python api.py campaigns              # List campaigns")
        print("  python api.py campaign [id]          # Get campaign details")
        print("  python api.py analytics [id]         # Get campaign analytics")
        print("  python api.py webhooks               # List webhooks")
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "test":
            if api.test_connection():
                print("✅ Connection successful")
            else:
                print("❌ Connection failed - check API key")

        elif command == "quick_start":
            api.quick_start()

        elif command == "discover":
            info = api.discover()
            print(json.dumps(info, indent=2))

        elif command == "campaigns":
            campaigns = api.list_campaigns()
            print(f"Found {len(campaigns)} campaigns:")
            for c in campaigns[:10]:
                print(
                    f"  - {c.get('name')} (ID: {c.get('id')}, Status: {c.get('status')})"
                )

        elif command == "campaign" and len(sys.argv) > 2:
            campaign_id = int(sys.argv[2])
            campaign = api.get_campaign(campaign_id)
            print(json.dumps(campaign, indent=2))

        elif command == "analytics" and len(sys.argv) > 2:
            campaign_id = int(sys.argv[2])
            analytics = api.get_campaign_analytics(campaign_id)
            print(f"Campaign Analytics (ID: {campaign_id}):")
            print(json.dumps(analytics, indent=2))

        elif command == "webhooks":
            webhooks = api.list_webhooks()
            print(f"Found {len(webhooks)} webhooks:")
            for w in webhooks:
                print(f"  - {w.get('url')} (Events: {', '.join(w.get('events', []))})")

        else:
            print(f"Unknown command: {command}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
