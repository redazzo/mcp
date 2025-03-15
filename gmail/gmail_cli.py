#!/usr/bin/env python3
import argparse
import sys
import os
import json
from gmail_server import (
    get_credentials, 
    build, 
    format_email_metadata, 
    get_message_content,
    SCOPES
)

def initialize_gmail_service():
    """Initialize the Gmail API service"""
    try:
        creds = get_credentials()
        service = build('gmail', 'v1', credentials=creds)
        return service
    except Exception as e:
        print(f"Error initializing Gmail service: {str(e)}")
        sys.exit(1)

def list_labels(service):
    """List all Gmail labels"""
    try:
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        
        if not labels:
            print("No labels found.")
            return
        
        print("Gmail Labels:")
        for label in labels:
            print(f"- {label['name']} (ID: {label['id']})")
    except Exception as e:
        print(f"Error listing labels: {str(e)}")

def list_inbox(service, max_results=10):
    """List recent messages from the inbox"""
    try:
        results = service.users().messages().list(
            userId='me', labelIds=['INBOX'], maxResults=max_results).execute()
        messages = results.get('messages', [])
        
        if not messages:
            print("No messages found in inbox.")
            return
        
        print(f"Recent Inbox Messages (showing {len(messages)} of {max_results} requested):")
        for msg in messages:
            message = service.users().messages().get(userId='me', id=msg['id']).execute()
            meta = format_email_metadata(message)
            print(f"\nID: {meta['id']}")
            print(f"From: {meta['from']}")
            print(f"Subject: {meta['subject']}")
            print(f"Date: {meta['date']}")
            print(f"Snippet: {meta['snippet']}")
            print("---")
    except Exception as e:
        print(f"Error listing inbox: {str(e)}")

def get_message(service, message_id):
    """Get a specific message by ID"""
    try:
        message = service.users().messages().get(userId='me', id=message_id).execute()
        meta = format_email_metadata(message)
        content = get_message_content(message)
        
        print(f"From: {meta['from']}")
        print(f"To: {meta['to']}")
        print(f"Subject: {meta['subject']}")
        print(f"Date: {meta['date']}")
        print("\nContent:")
        print(content)
    except Exception as e:
        print(f"Error getting message: {str(e)}")

def search_emails(service, query, max_results=10):
    """Search for emails using Gmail search syntax"""
    try:
        results = service.users().messages().list(
            userId='me', q=query, maxResults=max_results).execute()
        messages = results.get('messages', [])
        
        if not messages:
            print(f"No messages found matching: {query}")
            return
        
        print(f"Search Results for '{query}' (showing {len(messages)} of {max_results} requested):")
        for msg in messages:
            message = service.users().messages().get(userId='me', id=msg['id']).execute()
            meta = format_email_metadata(message)
            print(f"\nID: {meta['id']}")
            print(f"From: {meta['from']}")
            print(f"Subject: {meta['subject']}")
            print(f"Date: {meta['date']}")
            print(f"Snippet: {meta['snippet']}")
            print("---")
    except Exception as e:
        print(f"Error searching emails: {str(e)}")

def send_email(service, to, subject, body):
    """Send an email"""
    from email.mime.text import MIMEText
    import base64
    
    try:
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        
        raw_message = base64.urlsafe_b64encode(message.as_string().encode('utf-8')).decode('utf-8')
        
        message = service.users().messages().send(
            userId='me', body={'raw': raw_message}).execute()
        print(f"Email sent successfully to {to}. Message ID: {message['id']}")
    except Exception as e:
        print(f"Error sending email: {str(e)}")

def create_draft(service, to, subject, body):
    """Create a draft email"""
    from email.mime.text import MIMEText
    import base64
    
    try:
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        
        raw_message = base64.urlsafe_b64encode(message.as_string().encode('utf-8')).decode('utf-8')
        
        draft = service.users().drafts().create(
            userId='me', 
            body={'message': {'raw': raw_message}}
        ).execute()
        print(f"Draft created successfully. Draft ID: {draft['id']}")
    except Exception as e:
        print(f"Error creating draft: {str(e)}")

def add_label(service, message_id, label_name):
    """Add a label to a specific message"""
    try:
        # First check if label exists
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        
        label_id = None
        for label in labels:
            if label['name'].lower() == label_name.lower():
                label_id = label['id']
                break
        
        # If label doesn't exist, create it
        if not label_id:
            created_label = service.users().labels().create(
                userId='me',
                body={'name': label_name}
            ).execute()
            label_id = created_label['id']
            print(f"Created new label: {label_name}")
        
        # Add label to message
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'addLabelIds': [label_id]}
        ).execute()
        print(f"Label '{label_name}' added to message {message_id}")
    except Exception as e:
        print(f"Error adding label to message: {str(e)}")

def get_thread(service, thread_id):
    """Get all messages in a thread"""
    try:
        thread = service.users().threads().get(userId='me', id=thread_id).execute()
        messages = thread.get('messages', [])
        
        if not messages:
            print(f"No messages found in thread {thread_id}")
            return
        
        print(f"Thread {thread_id} ({len(messages)} messages):")
        for i, message in enumerate(messages, 1):
            meta = format_email_metadata(message)
            content = get_message_content(message)
            print(f"\n--- Message {i} of {len(messages)} ---")
            print(f"From: {meta['from']}")
            print(f"Date: {meta['date']}")
            print(f"Subject: {meta['subject']}")
            print("\nContent:")
            print(content)
            print("\n" + "="*50)
    except Exception as e:
        print(f"Error retrieving thread: {str(e)}")

def mark_as_read(service, message_id):
    """Mark a message as read"""
    try:
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        print(f"Message {message_id} marked as read")
    except Exception as e:
        print(f"Error marking message as read: {str(e)}")

def mark_as_unread(service, message_id):
    """Mark a message as unread"""
    try:
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'addLabelIds': ['UNREAD']}
        ).execute()
        print(f"Message {message_id} marked as unread")
    except Exception as e:
        print(f"Error marking message as unread: {str(e)}")

def archive_message(service, message_id):
    """Archive a message (remove from inbox)"""
    try:
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['INBOX']}
        ).execute()
        print(f"Message {message_id} archived")
    except Exception as e:
        print(f"Error archiving message: {str(e)}")

def trash_message(service, message_id):
    """Move a message to trash"""
    try:
        service.users().messages().trash(userId='me', id=message_id).execute()
        print(f"Message {message_id} moved to trash")
    except Exception as e:
        print(f"Error moving message to trash: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Gmail Command Line Interface')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Labels command
    labels_parser = subparsers.add_parser('labels', help='List all Gmail labels')
    
    # Inbox command
    inbox_parser = subparsers.add_parser('inbox', help='List recent messages from inbox')
    inbox_parser.add_argument('--max', type=int, default=10, help='Maximum number of messages to retrieve')
    
    # Get message command
    message_parser = subparsers.add_parser('message', help='Get a specific message by ID')
    message_parser.add_argument('message_id', help='ID of the message to retrieve')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for emails using Gmail search syntax')
    search_parser.add_argument('query', help='Gmail search query')
    search_parser.add_argument('--max', type=int, default=10, help='Maximum number of results')
    
    # Send email command
    send_parser = subparsers.add_parser('send', help='Send an email')
    send_parser.add_argument('--to', required=True, help='Recipient email address')
    send_parser.add_argument('--subject', required=True, help='Email subject')
    send_parser.add_argument('--body', required=True, help='Email body content')
    
    # Create draft command
    draft_parser = subparsers.add_parser('draft', help='Create a draft email')
    draft_parser.add_argument('--to', required=True, help='Recipient email address')
    draft_parser.add_argument('--subject', required=True, help='Email subject')
    draft_parser.add_argument('--body', required=True, help='Email body content')
    
    # Add label command
    label_parser = subparsers.add_parser('add-label', help='Add a label to a message')
    label_parser.add_argument('message_id', help='ID of the message')
    label_parser.add_argument('label_name', help='Name of the label to add')
    
    # Get thread command
    thread_parser = subparsers.add_parser('thread', help='Get all messages in a thread')
    thread_parser.add_argument('thread_id', help='ID of the thread')
    
    # Mark as read command
    read_parser = subparsers.add_parser('mark-read', help='Mark a message as read')
    read_parser.add_argument('message_id', help='ID of the message')
    
    # Mark as unread command
    unread_parser = subparsers.add_parser('mark-unread', help='Mark a message as unread')
    unread_parser.add_argument('message_id', help='ID of the message')
    
    # Archive message command
    archive_parser = subparsers.add_parser('archive', help='Archive a message')
    archive_parser.add_argument('message_id', help='ID of the message')
    
    # Trash message command
    trash_parser = subparsers.add_parser('trash', help='Move a message to trash')
    trash_parser.add_argument('message_id', help='ID of the message')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize Gmail service
    service = initialize_gmail_service()
    
    # Execute the requested command
    if args.command == 'labels':
        list_labels(service)
    elif args.command == 'inbox':
        list_inbox(service, args.max)
    elif args.command == 'message':
        get_message(service, args.message_id)
    elif args.command == 'search':
        search_emails(service, args.query, args.max)
    elif args.command == 'send':
        send_email(service, args.to, args.subject, args.body)
    elif args.command == 'draft':
        create_draft(service, args.to, args.subject, args.body)
    elif args.command == 'add-label':
        add_label(service, args.message_id, args.label_name)
    elif args.command == 'thread':
        get_thread(service, args.thread_id)
    elif args.command == 'mark-read':
        mark_as_read(service, args.message_id)
    elif args.command == 'mark-unread':
        mark_as_unread(service, args.message_id)
    elif args.command == 'archive':
        archive_message(service, args.message_id)
    elif args.command == 'trash':
        trash_message(service, args.message_id)

if __name__ == "__main__":
    main()