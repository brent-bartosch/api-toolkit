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
        self.api_key = api_key or os.getenv('SMARTLEAD_API_KEY')

        if not self.api_key:
            raise APIError("SMARTLEAD_API_KEY is required")

        super().__init__(
            api_key=self.api_key,
            base_url="https://server.smartlead.ai/api/v1",  # Correct server URL
            requests_per_second=5  # 10 requests per 2 seconds = 5/second
        )

    def _setup_auth(self):
        """Setup authentication - Smartlead uses query params"""
        # Auth is handled in _make_request for Smartlead
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def _make_request(self, method: str, endpoint: str,
                     data: Optional[Dict] = None,
                     params: Optional[Dict] = None,
                     headers: Optional[Dict] = None) -> Dict[str, Any]:
        """Override to add API key to query params"""
        # Add API key to params
        if params is None:
            params = {}
        params['api_key'] = self.api_key

        # Ensure endpoint doesn't start with /
        endpoint = endpoint.lstrip('/')

        return super()._make_request(method, endpoint, data, params, headers)

    # ============= CAMPAIGN OPERATIONS =============

    def create_campaign(self,
                       name: str,
                       client_id: int,
                       timezone: str = "America/New_York",
                       settings: Optional[Dict] = None) -> Dict:
        """
        Create a new email campaign.

        Args:
            name: Campaign name
            client_id: Client/workspace ID
            timezone: Campaign timezone
            settings: Additional campaign settings

        Returns:
            Created campaign details

        Example:
            campaign = api.create_campaign(
                'Q1 Outreach',
                client_id=123,
                settings={'track_opens': True}
            )
        """
        payload = {
            'name': name,
            'client_id': client_id,
            'timezone': timezone
        }

        if settings:
            payload.update(settings)

        return self._make_request('POST', 'campaigns/create', data=payload)

    def get_campaign(self, campaign_id: int) -> Dict:
        """
        Get campaign details by ID.

        Args:
            campaign_id: Campaign ID

        Returns:
            Campaign details
        """
        return self._make_request('GET', f'campaigns/{campaign_id}')

    def list_campaigns(self, client_id: Optional[int] = None) -> List[Dict]:
        """
        List all campaigns.

        Args:
            client_id: Filter by client ID

        Returns:
            List of campaigns
        """
        params = {}
        if client_id:
            params['client_id'] = client_id

        return self._make_request('GET', 'campaigns/list', params=params)

    def update_campaign_settings(self,
                                campaign_id: int,
                                settings: Dict) -> Dict:
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
        return self._make_request('POST',
                                f'campaigns/{campaign_id}/settings',
                                data=settings)

    def update_campaign_schedule(self,
                                campaign_id: int,
                                schedule: Dict) -> Dict:
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
        return self._make_request('POST',
                                f'campaigns/{campaign_id}/schedule',
                                data=schedule)

    def pause_campaign(self, campaign_id: int) -> Dict:
        """Pause a campaign"""
        return self._make_request('POST', f'campaigns/{campaign_id}/pause')

    def resume_campaign(self, campaign_id: int) -> Dict:
        """Resume a paused campaign"""
        return self._make_request('POST', f'campaigns/{campaign_id}/resume')

    def get_campaign_sequence(self, campaign_id: int) -> Dict:
        """
        Get email sequences for a campaign.

        Args:
            campaign_id: Campaign ID

        Returns:
            Campaign sequences
        """
        return self._make_request('GET', f'campaigns/{campaign_id}/sequences')

    # ============= LEAD OPERATIONS =============

    def add_leads_to_campaign(self,
                             campaign_id: int,
                             leads: List[Dict],
                             settings: Optional[Dict] = None) -> Dict:
        """
        Add leads to a campaign.

        Args:
            campaign_id: Campaign ID
            leads: List of lead dictionaries
            settings: Import settings

        Returns:
            Import result

        Example:
            leads = [
                {
                    'email': 'john@example.com',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'company_name': 'Example Inc'
                }
            ]
            api.add_leads_to_campaign(123, leads)
        """
        payload = {
            'campaign_id': campaign_id,
            'leads': leads
        }

        if settings:
            payload.update(settings)

        return self._make_request('POST', 'leads/add', data=payload)

    def get_lead(self, lead_id: int) -> Dict:
        """
        Get lead details.

        Args:
            lead_id: Lead ID

        Returns:
            Lead details
        """
        return self._make_request('GET', f'leads/{lead_id}')

    def get_lead_status(self,
                       campaign_id: int,
                       email: str) -> Dict:
        """
        Get lead status in a campaign.

        Args:
            campaign_id: Campaign ID
            email: Lead email

        Returns:
            Lead status (STARTED, COMPLETED, BLOCKED, INPROGRESS)
        """
        params = {
            'campaign_id': campaign_id,
            'email': email
        }
        return self._make_request('GET', 'leads/status', params=params)

    def update_lead_category(self,
                           lead_id: int,
                           category: str) -> Dict:
        """
        Update lead category/status.

        Args:
            lead_id: Lead ID
            category: New category

        Returns:
            Updated lead
        """
        return self._make_request('POST',
                                f'leads/{lead_id}/category',
                                data={'category': category})

    def block_lead(self, email: str, reason: Optional[str] = None) -> Dict:
        """
        Add lead to block list.

        Args:
            email: Email to block
            reason: Block reason

        Returns:
            Block result
        """
        data = {'email': email}
        if reason:
            data['reason'] = reason

        return self._make_request('POST', 'leads/block', data=data)

    def unblock_lead(self, email: str) -> Dict:
        """Remove lead from block list"""
        return self._make_request('POST', 'leads/unblock',
                                data={'email': email})

    def get_lead_activities(self,
                           lead_id: int,
                           campaign_id: Optional[int] = None) -> List[Dict]:
        """
        Get lead activity history.

        Args:
            lead_id: Lead ID
            campaign_id: Filter by campaign

        Returns:
            List of activities
        """
        params = {'lead_id': lead_id}
        if campaign_id:
            params['campaign_id'] = campaign_id

        return self._make_request('GET', 'leads/activities', params=params)

    # ============= ANALYTICS & REPORTING =============

    def get_campaign_analytics(self, campaign_id: int) -> Dict:
        """
        Get campaign performance analytics.

        Args:
            campaign_id: Campaign ID

        Returns:
            Analytics data including sent, opened, clicked, replied
        """
        return self._make_request('GET', f'campaigns/{campaign_id}/analytics')

    def get_lead_statistics(self, campaign_id: int) -> Dict:
        """
        Get detailed lead statistics for a campaign.

        Args:
            campaign_id: Campaign ID

        Returns:
            Lead statistics by status and category
        """
        return self._make_request('GET', f'campaigns/{campaign_id}/lead-stats')

    def get_campaign_summary(self, campaign_id: int) -> Dict:
        """
        Get comprehensive campaign summary.

        Args:
            campaign_id: Campaign ID

        Returns:
            Complete campaign overview with all metrics
        """
        return self._make_request('GET', f'campaigns/{campaign_id}/summary')

    def get_email_replies(self,
                         campaign_id: Optional[int] = None,
                         lead_id: Optional[int] = None) -> List[Dict]:
        """
        Get email replies.

        Args:
            campaign_id: Filter by campaign
            lead_id: Filter by lead

        Returns:
            List of email replies
        """
        params = {}
        if campaign_id:
            params['campaign_id'] = campaign_id
        if lead_id:
            params['lead_id'] = lead_id

        return self._make_request('GET', 'emails/replies', params=params)

    def get_bounce_report(self,
                         campaign_id: Optional[int] = None,
                         start_date: Optional[str] = None,
                         end_date: Optional[str] = None) -> List[Dict]:
        """
        Get email bounce report.

        Args:
            campaign_id: Filter by campaign
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Bounce report
        """
        params = {}
        if campaign_id:
            params['campaign_id'] = campaign_id
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date

        return self._make_request('GET', 'analytics/bounces', params=params)

    def export_campaign_data(self,
                           campaign_id: int,
                           export_type: str = 'csv') -> Union[str, Dict]:
        """
        Export campaign data.

        Args:
            campaign_id: Campaign ID
            export_type: Format (csv, json)

        Returns:
            Export data or download URL
        """
        params = {
            'campaign_id': campaign_id,
            'type': export_type
        }
        return self._make_request('GET', 'export/campaign', params=params)

    # ============= EMAIL ACCOUNT OPERATIONS =============

    def list_email_accounts(self) -> List[Dict]:
        """
        List all email accounts.

        Returns:
            List of email accounts with warmup status
        """
        return self._make_request('GET', 'email-accounts')

    def get_email_account(self, account_id: int) -> Dict:
        """
        Get email account details.

        Args:
            account_id: Email account ID

        Returns:
            Email account details including warmup status
        """
        return self._make_request('GET', f'email-accounts/{account_id}')

    def add_email_account(self,
                         email: str,
                         smtp_host: str,
                         smtp_port: int,
                         smtp_username: str,
                         smtp_password: str,
                         imap_host: Optional[str] = None,
                         imap_port: Optional[int] = None,
                         imap_username: Optional[str] = None,
                         imap_password: Optional[str] = None,
                         warmup_enabled: bool = True) -> Dict:
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
            'email': email,
            'smtp_host': smtp_host,
            'smtp_port': smtp_port,
            'smtp_username': smtp_username,
            'smtp_password': smtp_password,
            'warmup_enabled': warmup_enabled
        }

        if imap_host:
            data.update({
                'imap_host': imap_host,
                'imap_port': imap_port,
                'imap_username': imap_username,
                'imap_password': imap_password
            })

        return self._make_request('POST', 'email-accounts', data=data)

    def update_email_account_warmup(self,
                                   account_id: int,
                                   warmup_enabled: bool) -> Dict:
        """
        Enable or disable warmup for an email account.

        Args:
            account_id: Email account ID
            warmup_enabled: Enable/disable warmup

        Returns:
            Updated account details
        """
        return self._make_request('POST',
                                f'email-accounts/{account_id}/warmup',
                                data={'warmup_enabled': warmup_enabled})

    def update_email_account(self,
                            account_id: int,
                            **kwargs) -> Dict:
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
        return self._make_request('POST',
                                f'email-accounts/{account_id}',
                                data=kwargs)

    def set_reply_to_address(self,
                            account_id: int,
                            reply_to_email: str,
                            imap_host: Optional[str] = None,
                            imap_port: Optional[int] = None,
                            imap_username: Optional[str] = None,
                            imap_password: Optional[str] = None,
                            imap_port_type: str = 'SSL') -> Dict:
        """
        Set a different reply-to address for an email account.

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
        account_type = existing.get('type', 'SMTP')

        # Build update payload with required fields from existing account
        # Note: API expects 'user_name' not 'username'
        warmup = existing.get('warmup_details', {})
        data = {
            'id': account_id,
            'type': account_type,  # GMAIL, OUTLOOK, SMTP, ZOHO
            'from_name': existing.get('from_name', ''),
            'from_email': existing.get('from_email', ''),
            'user_name': existing.get('username', ''),  # API uses user_name
            'password': existing.get('password', ''),  # Required field
            'different_reply_to_address': reply_to_email,
            'warmup_enabled': warmup.get('status') == 'ACTIVE',
            'max_email_per_day': existing.get('message_per_day', 50)
        }

        # Include SMTP details - use defaults for OAuth accounts if not set
        if existing.get('smtp_host'):
            data['smtp_host'] = existing.get('smtp_host')
            data['smtp_port'] = existing.get('smtp_port')
        elif account_type == 'GMAIL':
            data['smtp_host'] = 'smtp.gmail.com'
            data['smtp_port'] = 465
        elif account_type == 'OUTLOOK':
            data['smtp_host'] = 'smtp.office365.com'
            data['smtp_port'] = 587

        # Include IMAP details - use existing or defaults
        if existing.get('imap_host'):
            data['imap_host'] = existing.get('imap_host')
            data['imap_port'] = existing.get('imap_port')
        elif account_type == 'GMAIL':
            data['imap_host'] = 'imap.gmail.com'
            data['imap_port'] = 993
        elif account_type == 'OUTLOOK':
            data['imap_host'] = 'outlook.office365.com'
            data['imap_port'] = 993

        return self._make_request('POST', 'email-accounts/save', data=data)

    def delete_email_account(self, account_id: int) -> bool:
        """
        Delete an email account.

        Args:
            account_id: Email account ID

        Returns:
            True if successful
        """
        self._make_request('DELETE', f'email-accounts/{account_id}')
        return True

    def get_warmup_status(self, account_id: int) -> Dict:
        """
        Get warmup status for an email account.

        Args:
            account_id: Email account ID

        Returns:
            Warmup statistics and progress
        """
        return self._make_request('GET', f'email-accounts/{account_id}/warmup')

    # ============= WEBHOOK OPERATIONS =============

    def register_webhook(self,
                        url: str,
                        events: List[str],
                        scope: str = 'user',
                        campaign_id: Optional[int] = None) -> Dict:
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
        data = {
            'url': url,
            'events': events,
            'scope': scope
        }

        if campaign_id and scope == 'campaign':
            data['campaign_id'] = campaign_id

        return self._make_request('POST', 'webhooks/register', data=data)

    def list_webhooks(self) -> List[Dict]:
        """List all registered webhooks"""
        return self._make_request('GET', 'webhooks/list')

    def delete_webhook(self, webhook_id: int) -> Dict:
        """Delete a webhook"""
        return self._make_request('DELETE', f'webhooks/{webhook_id}')

    # ============= HELPER METHODS =============

    def discover(self, resource: Optional[str] = None) -> Dict:
        """
        Discover available resources and capabilities.

        Args:
            resource: Specific resource to explore

        Returns:
            Discovery information
        """
        if resource == 'campaigns':
            try:
                campaigns = self.list_campaigns()
                return {
                    'total': len(campaigns),
                    'campaigns': [
                        {
                            'id': c.get('id'),
                            'name': c.get('name'),
                            'status': c.get('status'),
                            'created': c.get('created_at')
                        }
                        for c in campaigns[:10]
                    ]
                }
            except:
                return {'error': 'Could not list campaigns - check API key'}

        elif resource == 'email_accounts':
            try:
                accounts = self.list_email_accounts()
                return {
                    'total': len(accounts),
                    'accounts': [
                        {
                            'id': a.get('id'),
                            'email': a.get('email'),
                            'warmup_enabled': a.get('warmup_enabled'),
                            'status': a.get('status')
                        }
                        for a in accounts[:10]
                    ]
                }
            except:
                return {'error': 'Could not list email accounts - check API key'}

        elif resource == 'webhooks':
            return {
                'available_events': [
                    'EMAIL_SENT',
                    'EMAIL_OPENED',
                    'EMAIL_CLICKED',
                    'EMAIL_REPLY',
                    'EMAIL_BOUNCED',
                    'LEAD_UNSUBSCRIBED',
                    'LEAD_CATEGORY_UPDATED',
                    'CAMPAIGN_STATUS_CHANGE',
                    'MANUAL_STEP_REACHED'
                ],
                'scopes': ['user', 'client', 'campaign']
            }
        else:
            # General discovery
            return {
                'api_version': 'v1',
                'base_url': self.base_url,
                'resources': ['campaigns', 'leads', 'email_accounts', 'analytics', 'webhooks'],
                'rate_limit': '10 requests per 2 seconds',
                'features': [
                    'Campaign management',
                    'Lead tracking',
                    'Email account management',
                    'Email warmup',
                    'Analytics & reporting',
                    'Webhook automation',
                    'CSV/JSON exports'
                ]
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
            self._make_request('GET', 'campaigns/list', params={'limit': 1})
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
                print(f"  - {c.get('name')} (ID: {c.get('id')}, Status: {c.get('status')})")

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