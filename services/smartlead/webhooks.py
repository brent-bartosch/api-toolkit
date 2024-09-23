#!/usr/bin/env python3
"""
Smartlead Webhook Utilities

Helper functions for working with Smartlead webhooks.
"""

import json
import hashlib
import hmac
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

class SmartleadWebhookHandler:
    """
    Handler for Smartlead webhook events.

    Webhook Event Types:
    - EMAIL_SENT: Email was sent to lead
    - EMAIL_OPENED: Lead opened the email
    - EMAIL_CLICKED: Lead clicked a link
    - EMAIL_REPLY: Lead replied to email
    - EMAIL_BOUNCED: Email bounced
    - LEAD_UNSUBSCRIBED: Lead unsubscribed
    - LEAD_CATEGORY_UPDATED: Lead category changed
    - CAMPAIGN_STATUS_CHANGE: Campaign status changed
    - MANUAL_STEP_REACHED: Manual workflow step reached
    """

    # Event type constants
    EMAIL_SENT = 'EMAIL_SENT'
    EMAIL_OPENED = 'EMAIL_OPENED'
    EMAIL_CLICKED = 'EMAIL_CLICKED'
    EMAIL_REPLY = 'EMAIL_REPLY'
    EMAIL_BOUNCED = 'EMAIL_BOUNCED'
    LEAD_UNSUBSCRIBED = 'LEAD_UNSUBSCRIBED'
    LEAD_CATEGORY_UPDATED = 'LEAD_CATEGORY_UPDATED'
    CAMPAIGN_STATUS_CHANGE = 'CAMPAIGN_STATUS_CHANGE'
    MANUAL_STEP_REACHED = 'MANUAL_STEP_REACHED'

    def __init__(self, webhook_secret: Optional[str] = None):
        """
        Initialize webhook handler.

        Args:
            webhook_secret: Optional webhook secret for signature validation
        """
        self.webhook_secret = webhook_secret

    def parse_payload(self, payload: Union[str, Dict]) -> Dict:
        """
        Parse webhook payload.

        Args:
            payload: Raw webhook payload (JSON string or dict)

        Returns:
            Parsed webhook data
        """
        if isinstance(payload, str):
            return json.loads(payload)
        return payload

    def validate_signature(self, payload: str, signature: str) -> bool:
        """
        Validate webhook signature.

        Args:
            payload: Raw payload string
            signature: Signature from webhook headers

        Returns:
            True if signature is valid
        """
        if not self.webhook_secret:
            return True  # Skip validation if no secret configured

        expected = hmac.new(
            self.webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected, signature)

    def extract_event_type(self, payload: Dict) -> str:
        """Extract event type from payload"""
        return payload.get('event', 'UNKNOWN')

    def extract_campaign_info(self, payload: Dict) -> Dict:
        """
        Extract campaign information from payload.

        Returns:
            Dict with campaign_id, campaign_name
        """
        return {
            'campaign_id': payload.get('campaignId'),
            'campaign_name': payload.get('campaignName'),
            'client_id': payload.get('clientId')
        }

    def extract_lead_info(self, payload: Dict) -> Dict:
        """
        Extract lead information from payload.

        Returns:
            Dict with lead details
        """
        return {
            'lead_id': payload.get('leadId'),
            'email': payload.get('email'),
            'first_name': payload.get('firstName'),
            'last_name': payload.get('lastName'),
            'company': payload.get('companyName')
        }

    def extract_email_reply_details(self, payload: Dict) -> Dict:
        """
        Extract enhanced email reply details.

        Handles the new leadCorrespondence object for:
        - Direct replies
        - Colleague replies (same company)
        - Different company replies

        Returns:
            Dict with reply details including correspondence info
        """
        correspondence = payload.get('leadCorrespondence', {})

        return {
            'reply_from': payload.get('from'),
            'reply_to': payload.get('to'),
            'subject': payload.get('subject'),
            'message': payload.get('message'),
            'timestamp': payload.get('timestamp'),

            # Enhanced correspondence tracking
            'target_lead_email': correspondence.get('targetLeadEmail'),
            'reply_received_from': correspondence.get('replyReceivedFrom'),
            'replied_company_domain': correspondence.get('repliedCompanyDomain'),
            'is_same_company': correspondence.get('repliedCompanyDomain') == 'SAME_COMPANY',
            'is_different_company': correspondence.get('repliedCompanyDomain') == 'DIFFERENT_COMPANY'
        }

    def handle_event(self, payload: Dict) -> Dict:
        """
        Main event handler - routes to specific handlers.

        Args:
            payload: Parsed webhook payload

        Returns:
            Processing result
        """
        event_type = self.extract_event_type(payload)

        handlers = {
            self.EMAIL_REPLY: self._handle_email_reply,
            self.EMAIL_OPENED: self._handle_email_opened,
            self.EMAIL_CLICKED: self._handle_email_clicked,
            self.EMAIL_BOUNCED: self._handle_email_bounced,
            self.LEAD_UNSUBSCRIBED: self._handle_lead_unsubscribed,
            self.LEAD_CATEGORY_UPDATED: self._handle_category_updated
        }

        handler = handlers.get(event_type, self._handle_unknown)
        return handler(payload)

    def _handle_email_reply(self, payload: Dict) -> Dict:
        """Handle email reply event"""
        return {
            'event': self.EMAIL_REPLY,
            'campaign': self.extract_campaign_info(payload),
            'lead': self.extract_lead_info(payload),
            'reply': self.extract_email_reply_details(payload),
            'processed_at': datetime.now().isoformat()
        }

    def _handle_email_opened(self, payload: Dict) -> Dict:
        """Handle email opened event"""
        return {
            'event': self.EMAIL_OPENED,
            'campaign': self.extract_campaign_info(payload),
            'lead': self.extract_lead_info(payload),
            'opened_at': payload.get('timestamp'),
            'processed_at': datetime.now().isoformat()
        }

    def _handle_email_clicked(self, payload: Dict) -> Dict:
        """Handle link click event"""
        return {
            'event': self.EMAIL_CLICKED,
            'campaign': self.extract_campaign_info(payload),
            'lead': self.extract_lead_info(payload),
            'link': payload.get('link'),
            'clicked_at': payload.get('timestamp'),
            'processed_at': datetime.now().isoformat()
        }

    def _handle_email_bounced(self, payload: Dict) -> Dict:
        """Handle email bounce event"""
        return {
            'event': self.EMAIL_BOUNCED,
            'campaign': self.extract_campaign_info(payload),
            'lead': self.extract_lead_info(payload),
            'bounce_type': payload.get('bounceType'),
            'bounce_reason': payload.get('bounceReason'),
            'bounced_at': payload.get('timestamp'),
            'processed_at': datetime.now().isoformat()
        }

    def _handle_lead_unsubscribed(self, payload: Dict) -> Dict:
        """Handle unsubscribe event"""
        return {
            'event': self.LEAD_UNSUBSCRIBED,
            'campaign': self.extract_campaign_info(payload),
            'lead': self.extract_lead_info(payload),
            'unsubscribed_at': payload.get('timestamp'),
            'processed_at': datetime.now().isoformat()
        }

    def _handle_category_updated(self, payload: Dict) -> Dict:
        """Handle lead category update"""
        return {
            'event': self.LEAD_CATEGORY_UPDATED,
            'campaign': self.extract_campaign_info(payload),
            'lead': self.extract_lead_info(payload),
            'old_category': payload.get('oldCategory'),
            'new_category': payload.get('newCategory'),
            'updated_at': payload.get('timestamp'),
            'processed_at': datetime.now().isoformat()
        }

    def _handle_unknown(self, payload: Dict) -> Dict:
        """Handle unknown event types"""
        return {
            'event': 'UNKNOWN',
            'raw_event': self.extract_event_type(payload),
            'payload': payload,
            'processed_at': datetime.now().isoformat()
        }


def create_webhook_endpoint(handler_function):
    """
    Decorator to create a webhook endpoint handler.

    Example:
        @create_webhook_endpoint
        def handle_smartlead_webhook(event_data):
            if event_data['event'] == 'EMAIL_REPLY':
                # Process reply
                pass
    """
    def wrapper(request_data):
        handler = SmartleadWebhookHandler()
        payload = handler.parse_payload(request_data)
        processed = handler.handle_event(payload)
        return handler_function(processed)
    return wrapper


# Example webhook implementations
def log_webhook_event(event_data: Dict):
    """Simple webhook logger"""
    print(f"[{event_data['processed_at']}] {event_data['event']}")
    if 'lead' in event_data:
        print(f"  Lead: {event_data['lead']['email']}")
    if 'campaign' in event_data:
        print(f"  Campaign: {event_data['campaign']['campaign_name']}")


def route_to_crm(event_data: Dict):
    """
    Example: Route webhook data to CRM.

    This would integrate with your CRM API to:
    - Update lead status on replies
    - Log activities
    - Trigger workflows
    """
    if event_data['event'] == SmartleadWebhookHandler.EMAIL_REPLY:
        # Update CRM with reply
        lead_email = event_data['lead']['email']
        reply_text = event_data['reply']['message']
        # CRM API call here
        print(f"Updating CRM for {lead_email} with reply")

    elif event_data['event'] == SmartleadWebhookHandler.LEAD_UNSUBSCRIBED:
        # Mark as unsubscribed in CRM
        lead_email = event_data['lead']['email']
        # CRM API call here
        print(f"Marking {lead_email} as unsubscribed in CRM")


# Webhook testing utilities
def simulate_webhook_payload(event_type: str, **kwargs) -> Dict:
    """
    Generate sample webhook payload for testing.

    Args:
        event_type: Type of webhook event
        **kwargs: Additional payload fields

    Returns:
        Sample webhook payload
    """
    base_payload = {
        'event': event_type,
        'campaignId': kwargs.get('campaign_id', 123),
        'campaignName': kwargs.get('campaign_name', 'Test Campaign'),
        'leadId': kwargs.get('lead_id', 456),
        'email': kwargs.get('email', 'test@example.com'),
        'firstName': kwargs.get('first_name', 'Test'),
        'lastName': kwargs.get('last_name', 'User'),
        'timestamp': datetime.now().isoformat()
    }

    if event_type == SmartleadWebhookHandler.EMAIL_REPLY:
        base_payload.update({
            'from': kwargs.get('from', 'test@example.com'),
            'to': kwargs.get('to', 'sales@company.com'),
            'subject': kwargs.get('subject', 'Re: Your email'),
            'message': kwargs.get('message', 'Thanks for reaching out!'),
            'leadCorrespondence': {
                'targetLeadEmail': kwargs.get('target_email', 'test@example.com'),
                'replyReceivedFrom': kwargs.get('reply_from', 'test@example.com'),
                'repliedCompanyDomain': kwargs.get('company_relation', 'SAME_COMPANY')
            }
        })

    return base_payload


if __name__ == "__main__":
    # Test webhook handling
    print("Testing Smartlead Webhook Handler")
    print("=" * 50)

    handler = SmartleadWebhookHandler()

    # Test different event types
    events_to_test = [
        SmartleadWebhookHandler.EMAIL_REPLY,
        SmartleadWebhookHandler.EMAIL_OPENED,
        SmartleadWebhookHandler.EMAIL_BOUNCED,
        SmartleadWebhookHandler.LEAD_UNSUBSCRIBED
    ]

    for event_type in events_to_test:
        print(f"\nTesting {event_type}:")
        payload = simulate_webhook_payload(event_type)
        result = handler.handle_event(payload)
        print(json.dumps(result, indent=2))