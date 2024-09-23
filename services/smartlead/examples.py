#!/usr/bin/env python3
"""
Smartlead API Examples

Demonstrates common patterns for cold email automation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from services.smartlead.api import SmartleadAPI
from services.smartlead.webhooks import SmartleadWebhookHandler, simulate_webhook_payload
import json
from datetime import datetime, timedelta

def example_basic_connection():
    """Example: Basic connection and authentication"""
    print("\n" + "="*50)
    print("EXAMPLE: Basic Connection")
    print("="*50)

    try:
        api = SmartleadAPI()

        if api.test_connection():
            print("✅ Connected to Smartlead")
        else:
            print("❌ Connection failed - check API key")

        # Show API info
        info = api.discover()
        print(f"\nAPI Base URL: {info['base_url']}")
        print(f"Rate Limit: {info['rate_limit']}")
        print(f"Available Resources: {', '.join(info['resources'])}")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure SMARTLEAD_API_KEY is set in your .env file")

    return api

def example_campaign_management():
    """Example: Create and manage campaigns"""
    print("\n" + "="*50)
    print("EXAMPLE: Campaign Management")
    print("="*50)

    api = SmartleadAPI()

    # List existing campaigns
    print("\nExisting Campaigns:")
    try:
        campaigns = api.list_campaigns()
        print(f"Found {len(campaigns)} campaigns:")
        for camp in campaigns[:3]:
            print(f"  - {camp.get('name')} (ID: {camp.get('id')}, Status: {camp.get('status')})")
    except Exception as e:
        print(f"Could not list campaigns: {e}")

    # Example: Create a new campaign
    print("\n" + "-"*30)
    print("Creating a campaign (example code):")
    print("""
    campaign = api.create_campaign(
        name='Q1 2025 Outreach',
        client_id=1,  # Your client/workspace ID
        settings={
            'track_opens': True,
            'track_link_clicks': True,
            'stop_on_reply': True,
            'daily_limit': 50
        }
    )
    """)

    # Example: Update campaign schedule
    print("\nSetting campaign schedule (example code):")
    print("""
    api.update_campaign_schedule(
        campaign_id=123,
        schedule={
            'days_of_week': [1, 2, 3, 4, 5],  # Monday-Friday
            'start_hour': '09:00',
            'end_hour': '17:00',
            'timezone': 'America/New_York'
        }
    )
    """)

def example_lead_management():
    """Example: Add and manage leads"""
    print("\n" + "="*50)
    print("EXAMPLE: Lead Management")
    print("="*50)

    api = SmartleadAPI()

    # Example: Add leads to campaign
    print("Adding leads to campaign (example code):")
    print("""
    leads = [
        {
            'email': 'john.doe@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'company_name': 'Example Inc',
            'website': 'example.com',
            'custom_field_1': 'Value1'
        },
        {
            'email': 'jane.smith@company.com',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'company_name': 'Company Corp',
            'title': 'Marketing Director'
        }
    ]

    result = api.add_leads_to_campaign(
        campaign_id=123,
        leads=leads,
        settings={
            'ignore_global_block_list': False,
            'ignore_unsubscribe_list': False
        }
    )
    print(f"Added {result['added_count']} leads")
    """)

    # Example: Check lead status
    print("\n" + "-"*30)
    print("Checking lead status (example code):")
    print("""
    status = api.get_lead_status(
        campaign_id=123,
        email='john.doe@example.com'
    )
    print(f"Lead Status: {status['status']}")
    # Status can be: STARTED, INPROGRESS, COMPLETED, BLOCKED
    """)

    # Example: Update lead category
    print("\nCategorizing leads (example code):")
    print("""
    # After a lead replies, categorize them
    api.update_lead_category(
        lead_id=456,
        category='interested'  # or 'not_interested', 'meeting_booked', etc.
    )
    """)

def example_email_sequences():
    """Example: Configure email sequences"""
    print("\n" + "="*50)
    print("EXAMPLE: Email Sequences")
    print("="*50)

    api = SmartleadAPI()

    print("Email sequence configuration happens during campaign creation.")
    print("\nExample sequence setup:")
    print("""
    # Sequences are configured when creating campaigns
    # You can set up multiple sequence variants for A/B testing

    campaign_data = {
        'name': 'Product Launch Campaign',
        'client_id': 1,
        'sequences': [
            {
                'variant': 'A',
                'weight': 50,  # 50% of leads get this variant
                'emails': [
                    {
                        'subject': 'Quick question about {{company_name}}',
                        'body': 'Hi {{first_name}}, ...',
                        'delay_days': 0  # Send immediately
                    },
                    {
                        'subject': 'Following up',
                        'body': 'Hi {{first_name}}, Just wanted to follow up...',
                        'delay_days': 3  # Send 3 days after previous
                    }
                ]
            },
            {
                'variant': 'B',
                'weight': 50,  # Other 50% get this variant
                'emails': [
                    {
                        'subject': 'Helping {{company_name}} grow',
                        'body': 'Hey {{first_name}}, ...',
                        'delay_days': 0
                    }
                ]
            }
        ]
    }
    """)

    # Get sequence for existing campaign
    try:
        # This would work with a real campaign ID
        # sequences = api.get_campaign_sequence(123)
        print("\nTo retrieve sequences: api.get_campaign_sequence(campaign_id)")
    except:
        pass

def example_analytics_reporting():
    """Example: Get analytics and reports"""
    print("\n" + "="*50)
    print("EXAMPLE: Analytics & Reporting")
    print("="*50)

    api = SmartleadAPI()

    # Get campaign analytics
    print("Fetching campaign analytics (example code):")
    print("""
    analytics = api.get_campaign_analytics(campaign_id=123)

    print(f"Campaign Performance:")
    print(f"  Sent: {analytics['sent']}")
    print(f"  Opened: {analytics['opened']} ({analytics['open_rate']}%)")
    print(f"  Clicked: {analytics['clicked']} ({analytics['click_rate']}%)")
    print(f"  Replied: {analytics['replied']} ({analytics['reply_rate']}%)")
    print(f"  Bounced: {analytics['bounced']}")
    print(f"  Unsubscribed: {analytics['unsubscribed']}")
    """)

    # Get email replies
    print("\n" + "-"*30)
    print("Fetching email replies (example code):")
    print("""
    replies = api.get_email_replies(campaign_id=123)

    for reply in replies:
        print(f"From: {reply['from_email']}")
        print(f"Subject: {reply['subject']}")
        print(f"Message: {reply['message'][:100]}...")
        print(f"Received: {reply['timestamp']}")
        print("-" * 20)
    """)

    # Export data
    print("\nExporting campaign data (example code):")
    print("""
    # Export as CSV
    csv_data = api.export_campaign_data(
        campaign_id=123,
        export_type='csv'
    )

    # Export as JSON
    json_data = api.export_campaign_data(
        campaign_id=123,
        export_type='json'
    )
    """)

def example_webhook_setup():
    """Example: Setting up webhooks"""
    print("\n" + "="*50)
    print("EXAMPLE: Webhook Setup")
    print("="*50)

    api = SmartleadAPI()

    # Show available webhook events
    webhook_info = api.discover('webhooks')
    print("Available Webhook Events:")
    for event in webhook_info['available_events']:
        print(f"  • {event}")

    print(f"\nWebhook Scopes: {', '.join(webhook_info['scopes'])}")

    # Register webhook example
    print("\n" + "-"*30)
    print("Registering a webhook (example code):")
    print("""
    webhook = api.register_webhook(
        url='https://your-app.com/webhooks/smartlead',
        events=['EMAIL_REPLY', 'EMAIL_BOUNCED', 'LEAD_UNSUBSCRIBED'],
        scope='user'  # or 'campaign' or 'client'
    )
    print(f"Webhook registered: {webhook['id']}")
    """)

    # List webhooks
    print("\nListing webhooks (example code):")
    print("""
    webhooks = api.list_webhooks()
    for webhook in webhooks:
        print(f"URL: {webhook['url']}")
        print(f"Events: {', '.join(webhook['events'])}")
        print(f"Scope: {webhook['scope']}")
    """)

def example_webhook_handling():
    """Example: Processing webhook events"""
    print("\n" + "="*50)
    print("EXAMPLE: Webhook Event Processing")
    print("="*50)

    handler = SmartleadWebhookHandler()

    # Simulate different webhook events
    events = [
        ('EMAIL_REPLY', {
            'message': 'Thanks for reaching out! I\'d love to learn more.',
            'leadCorrespondence': {
                'targetLeadEmail': 'john@example.com',
                'replyReceivedFrom': 'john@example.com',
                'repliedCompanyDomain': 'SAME_COMPANY'
            }
        }),
        ('EMAIL_BOUNCED', {
            'bounceType': 'hard',
            'bounceReason': 'Invalid email address'
        }),
        ('LEAD_UNSUBSCRIBED', {}),
        ('EMAIL_OPENED', {})
    ]

    for event_type, extra_data in events:
        print(f"\n{event_type} Event:")
        print("-" * 30)

        # Simulate webhook payload
        payload = simulate_webhook_payload(event_type, **extra_data)

        # Process the webhook
        result = handler.handle_event(payload)

        # Display processed result
        print(f"Processed Event: {result['event']}")
        if 'lead' in result:
            print(f"Lead: {result['lead']['email']}")
        if 'campaign' in result:
            print(f"Campaign: {result['campaign']['campaign_name']}")

        # Event-specific details
        if event_type == 'EMAIL_REPLY' and 'reply' in result:
            print(f"Reply from: {result['reply']['reply_received_from']}")
            print(f"Same company: {result['reply']['is_same_company']}")
        elif event_type == 'EMAIL_BOUNCED':
            print(f"Bounce type: {result.get('bounce_type')}")
            print(f"Reason: {result.get('bounce_reason')}")

def example_automation_workflow():
    """Example: Complete automation workflow"""
    print("\n" + "="*50)
    print("EXAMPLE: Complete Automation Workflow")
    print("="*50)

    print("Here's a complete workflow for cold email automation:")
    print("""
    # 1. Initialize API
    api = SmartleadAPI()

    # 2. Create Campaign
    campaign = api.create_campaign(
        name='B2B SaaS Outreach Q1',
        client_id=1,
        settings={
            'track_opens': True,
            'track_link_clicks': True,
            'stop_on_reply': True,
            'daily_limit': 100
        }
    )

    # 3. Set Schedule
    api.update_campaign_schedule(
        campaign_id=campaign['id'],
        schedule={
            'days_of_week': [1, 2, 3, 4, 5],
            'start_hour': '09:00',
            'end_hour': '17:00',
            'timezone': 'America/New_York'
        }
    )

    # 4. Import Leads
    leads = load_leads_from_csv('prospects.csv')
    api.add_leads_to_campaign(campaign['id'], leads)

    # 5. Setup Webhooks
    api.register_webhook(
        url='https://your-app.com/smartlead-webhook',
        events=['EMAIL_REPLY', 'EMAIL_BOUNCED'],
        scope='campaign',
        campaign_id=campaign['id']
    )

    # 6. Start Campaign
    api.resume_campaign(campaign['id'])

    # 7. Monitor Performance
    while campaign_is_running:
        analytics = api.get_campaign_analytics(campaign['id'])
        print(f"Reply rate: {analytics['reply_rate']}%")

        # Process replies
        replies = api.get_email_replies(campaign['id'])
        for reply in replies:
            # Categorize and route to sales
            if 'interested' in reply['message'].lower():
                api.update_lead_category(reply['lead_id'], 'qualified')
                notify_sales_team(reply)

        time.sleep(3600)  # Check every hour
    """)

def example_error_handling():
    """Example: Proper error handling"""
    print("\n" + "="*50)
    print("EXAMPLE: Error Handling")
    print("="*50)

    api = SmartleadAPI()

    # Rate limit handling
    print("Handling rate limits:")
    print("""
    import time

    def safe_api_call(func, *args, **kwargs):
        max_retries = 3
        retry_delay = 2  # Start with 2 seconds

        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except APIError as e:
                if 'rate limit' in str(e).lower():
                    print(f"Rate limited, waiting {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise
        raise Exception("Max retries exceeded")

    # Use it
    result = safe_api_call(api.list_campaigns)
    """)

    # Invalid campaign handling
    print("\n" + "-"*30)
    print("Handling missing resources:")
    print("""
    try:
        campaign = api.get_campaign(999999)
    except APIError as e:
        if '404' in str(e) or 'not found' in str(e).lower():
            print("Campaign not found")
            # Create new campaign or handle accordingly
        else:
            raise
    """)

    print("\nValidation before operations:")
    print("""
    # Validate email before adding to campaign
    import re

    def is_valid_email(email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    leads_to_add = []
    for lead in raw_leads:
        if is_valid_email(lead['email']):
            leads_to_add.append(lead)
        else:
            print(f"Skipping invalid email: {lead['email']}")

    if leads_to_add:
        api.add_leads_to_campaign(campaign_id, leads_to_add)
    """)

# ============= MAIN EXECUTION =============

if __name__ == "__main__":
    if len(sys.argv) > 1:
        example_name = sys.argv[1]

        examples = {
            'basic': example_basic_connection,
            'campaigns': example_campaign_management,
            'leads': example_lead_management,
            'sequences': example_email_sequences,
            'analytics': example_analytics_reporting,
            'webhook_setup': example_webhook_setup,
            'webhook_handling': example_webhook_handling,
            'workflow': example_automation_workflow,
            'errors': example_error_handling
        }

        if example_name in examples:
            examples[example_name]()
        else:
            print(f"Unknown example: {example_name}")
            print(f"Available: {', '.join(examples.keys())}")
    else:
        print("Smartlead API Examples")
        print("="*40)
        print("\nUsage: python examples.py [example_name]")
        print("\nAvailable examples:")
        print("  basic           - Test connection")
        print("  campaigns       - Campaign management")
        print("  leads           - Lead management")
        print("  sequences       - Email sequences")
        print("  analytics       - Analytics & reporting")
        print("  webhook_setup   - Setting up webhooks")
        print("  webhook_handling - Processing webhooks")
        print("  workflow        - Complete workflow")
        print("  errors          - Error handling")
        print("\nRunning all examples...")

        # Run all examples
        example_basic_connection()
        example_campaign_management()
        example_lead_management()
        example_email_sequences()
        example_analytics_reporting()
        example_webhook_setup()
        example_webhook_handling()
        example_automation_workflow()
        example_error_handling()