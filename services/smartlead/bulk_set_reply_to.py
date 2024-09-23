#!/usr/bin/env python3
"""
Bulk Set Reply-To Address for Smartlead Email Accounts

Sets a unified reply-to address across all (or selected) email accounts
so that replies are routed to a central inbox.

Usage:
    # Dry run - see what would change
    python bulk_set_reply_to.py --reply-to replies@company.com --dry-run

    # Apply to all mailboxes
    python bulk_set_reply_to.py --reply-to replies@company.com

    # Apply only to specific accounts (by email pattern)
    python bulk_set_reply_to.py --reply-to replies@company.com --filter "@gmail.com"

    # With IMAP credentials for the reply-to inbox
    python bulk_set_reply_to.py \
        --reply-to replies@company.com \
        --imap-host imap.gmail.com \
        --imap-port 993 \
        --imap-password "app-specific-password"

Requirements:
    - SMARTLEAD_API_KEY in .env or environment
    - The reply-to email should also be added as an email account in Smartlead
      for replies to appear in the Master Inbox
"""

import argparse
import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from services.smartlead.api import SmartleadAPI


def bulk_set_reply_to(
    reply_to_email: str,
    imap_host: str = None,
    imap_port: int = None,
    imap_username: str = None,
    imap_password: str = None,
    imap_port_type: str = 'SSL',
    email_filter: str = None,
    exclude_reply_to: bool = True,
    dry_run: bool = False
):
    """
    Set reply-to address for multiple email accounts.

    Args:
        reply_to_email: The unified reply-to address
        imap_host: IMAP server for the reply-to account
        imap_port: IMAP port (default: 993)
        imap_username: IMAP username (defaults to reply_to_email)
        imap_password: IMAP password/app-password
        imap_port_type: 'SSL' or 'TLS'
        email_filter: Only process accounts containing this string
        exclude_reply_to: Skip the reply-to address itself (default: True)
        dry_run: If True, show what would change without making changes

    Returns:
        dict with success/failure counts and details
    """
    api = SmartleadAPI()

    # Get all email accounts
    print("Fetching email accounts...")
    accounts = api.list_email_accounts()
    print(f"Found {len(accounts)} email accounts\n")

    results = {
        'total': len(accounts),
        'processed': 0,
        'skipped': 0,
        'success': 0,
        'failed': 0,
        'details': []
    }

    for account in accounts:
        account_id = account.get('id')
        account_email = account.get('from_email') or account.get('email')
        current_reply_to = account.get('different_reply_to_address', '')

        # Apply filters
        if email_filter and email_filter not in account_email:
            results['skipped'] += 1
            continue

        if exclude_reply_to and account_email == reply_to_email:
            print(f"SKIP: {account_email} (is the reply-to address)")
            results['skipped'] += 1
            results['details'].append({
                'email': account_email,
                'status': 'skipped',
                'reason': 'is reply-to address'
            })
            continue

        # Check if already configured
        if current_reply_to == reply_to_email:
            print(f"SKIP: {account_email} (already set to {reply_to_email})")
            results['skipped'] += 1
            results['details'].append({
                'email': account_email,
                'status': 'skipped',
                'reason': 'already configured'
            })
            continue

        # Show what would change
        old_value = current_reply_to or "(not set)"
        print(f"{'[DRY RUN] ' if dry_run else ''}UPDATE: {account_email}")
        print(f"  Reply-to: {old_value} -> {reply_to_email}")

        if dry_run:
            results['processed'] += 1
            results['details'].append({
                'email': account_email,
                'status': 'would_update',
                'old_reply_to': old_value,
                'new_reply_to': reply_to_email
            })
            continue

        # Actually update
        try:
            api.set_reply_to_address(
                account_id=account_id,
                reply_to_email=reply_to_email,
                imap_host=imap_host,
                imap_port=imap_port,
                imap_username=imap_username or reply_to_email,
                imap_password=imap_password,
                imap_port_type=imap_port_type
            )
            print(f"  SUCCESS")
            results['success'] += 1
            results['details'].append({
                'email': account_email,
                'status': 'success',
                'old_reply_to': old_value,
                'new_reply_to': reply_to_email
            })

            # Rate limit: 5 requests per second
            time.sleep(0.25)

        except Exception as e:
            print(f"  FAILED: {e}")
            results['failed'] += 1
            results['details'].append({
                'email': account_email,
                'status': 'failed',
                'error': str(e)
            })

        results['processed'] += 1

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Bulk set reply-to address for Smartlead email accounts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview changes (dry run)
  python bulk_set_reply_to.py --reply-to replies@company.com --dry-run

  # Apply to all accounts
  python bulk_set_reply_to.py --reply-to replies@company.com

  # Only update Gmail accounts
  python bulk_set_reply_to.py --reply-to replies@company.com --filter "@gmail.com"

  # With IMAP configuration
  python bulk_set_reply_to.py \\
      --reply-to replies@company.com \\
      --imap-host imap.gmail.com \\
      --imap-port 993 \\
      --imap-password "your-app-password"

Note: The reply-to email should also be added as a separate email account
      in Smartlead for replies to appear in the Master Inbox.
        """
    )

    parser.add_argument(
        '--reply-to', '-r',
        required=True,
        help='The unified reply-to email address'
    )

    parser.add_argument(
        '--imap-host',
        help='IMAP server for the reply-to account (e.g., imap.gmail.com)'
    )

    parser.add_argument(
        '--imap-port',
        type=int,
        default=993,
        help='IMAP port (default: 993)'
    )

    parser.add_argument(
        '--imap-username',
        help='IMAP username (defaults to reply-to email)'
    )

    parser.add_argument(
        '--imap-password',
        help='IMAP password or app-specific password'
    )

    parser.add_argument(
        '--imap-port-type',
        choices=['SSL', 'TLS'],
        default='SSL',
        help='IMAP connection type (default: SSL)'
    )

    parser.add_argument(
        '--filter', '-f',
        help='Only process accounts containing this string (e.g., "@gmail.com")'
    )

    parser.add_argument(
        '--include-reply-to',
        action='store_true',
        help='Also update the reply-to account itself (usually not needed)'
    )

    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Show what would change without making changes'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Smartlead Bulk Reply-To Configuration")
    print("=" * 60)
    print(f"Reply-to address: {args.reply_to}")
    if args.imap_host:
        print(f"IMAP server: {args.imap_host}:{args.imap_port} ({args.imap_port_type})")
    if args.filter:
        print(f"Filter: {args.filter}")
    if args.dry_run:
        print("\n*** DRY RUN MODE - No changes will be made ***")
    print("=" * 60 + "\n")

    results = bulk_set_reply_to(
        reply_to_email=args.reply_to,
        imap_host=args.imap_host,
        imap_port=args.imap_port,
        imap_username=args.imap_username,
        imap_password=args.imap_password,
        imap_port_type=args.imap_port_type,
        email_filter=args.filter,
        exclude_reply_to=not args.include_reply_to,
        dry_run=args.dry_run
    )

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total accounts:    {results['total']}")
    print(f"Processed:         {results['processed']}")
    print(f"Skipped:           {results['skipped']}")
    if not args.dry_run:
        print(f"Success:           {results['success']}")
        print(f"Failed:            {results['failed']}")

    if args.dry_run and results['processed'] > 0:
        print(f"\nRun without --dry-run to apply these changes.")

    if results['failed'] > 0:
        print(f"\nFailed accounts:")
        for detail in results['details']:
            if detail['status'] == 'failed':
                print(f"  - {detail['email']}: {detail.get('error', 'Unknown error')}")

    return 0 if results['failed'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
