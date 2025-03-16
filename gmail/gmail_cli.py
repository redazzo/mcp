#!/usr/bin/env python3
import argparse
import sys
import os
import json
from gmail.auth import GmailClient, SCOPES
from gmail.utils import format_email_metadata, get_message_content
from gmail.api.labels import LabelOperations
from gmail.api.messages import MessageOperations
from gmail.api.drafts import DraftOperations
from gmail.api.threads import ThreadOperations

def initialize_gmail_service():
    """Initialize the Gmail API service"""
    try:
        client = GmailClient()
        service = client.authenticate()
        return service
    except Exception as e:
        print(f"Error initializing Gmail service: {str(e)}")
        sys.exit(1)

def list_labels(service):
    """List all Gmail labels"""
    try:
        label_ops = LabelOperations(service)
        labels = label_ops.list_labels()
        
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
        message_ops = MessageOperations(service)
        messages = message_ops.list_messages(label_ids=['INBOX'], max_results=max_results)
        
        if not messages:
            print("No messages found in inbox.")
            return
        
        print(f"Recent Inbox Messages (showing {len(messages)} of {max_results} requested):")
        for msg in messages:
            message = message_ops.get_message(msg['id'])
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
        message_ops = MessageOperations(service)
        message = message_ops.get_message(message_id)
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
        message_ops = MessageOperations(service)
        messages = message_ops.list_messages(query=query, max_results=max_results)
        
        if not messages:
            print(f"No messages found matching: {query}")
            return
        
        print(f"Search Results for '{query}' (showing {len(messages)} of {max_results} requested):")
        for msg in messages:
            message = message_ops.get_message(msg['id'])
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
    try:
        message_ops = MessageOperations(service)
        result = message_ops.send_message(to, subject, body)
        print(f"Email sent successfully to {to}. Message ID: {result['id']}")
    except Exception as e:
        print(f"Error sending email: {str(e)}")

def create_draft(service, to, subject, body):
    """Create a draft email"""
    try:
        draft_ops = DraftOperations(service)
        result = draft_ops.create_draft(to, subject, body)
        print(f"Draft created successfully. Draft ID: {result['id']}")
    except Exception as e:
        print(f"Error creating draft: {str(e)}")

def add_label(service, message_id, label_name):
    """Add a label to a specific message"""
    try:
        label_ops = LabelOperations(service)
        message_ops = MessageOperations(service)
        
        # First check if label exists
        labels = label_ops.list_labels()
        
        label_id = None
        for label in labels:
            if label['name'].lower() == label_name.lower():
                label_id = label['id']
                break
        
        # If label doesn't exist, create it
        if not label_id:
            created_label = label_ops.create_label(label_name)
            label_id = created_label['id']
            print(f"Created new label: {label_name}")
        
        # Add label to message
        message_ops.modify_message(message_id, add_label_ids=[label_id])
        print(f"Label '{label_name}' added to message {message_id}")
    except Exception as e:
        print(f"Error adding label to message: {str(e)}")

def get_thread(service, thread_id):
    """Get all messages in a thread"""
    try:
        thread_ops = ThreadOperations(service)
        thread = thread_ops.get_thread(thread_id)
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
        message_ops = MessageOperations(service)
        message_ops.mark_as_read(message_id)
        print(f"Message {message_id} marked as read")
    except Exception as e:
        print(f"Error marking message as read: {str(e)}")

def mark_as_unread(service, message_id):
    """Mark a message as unread"""
    try:
        message_ops = MessageOperations(service)
        message_ops.mark_as_unread(message_id)
        print(f"Message {message_id} marked as unread")
    except Exception as e:
        print(f"Error marking message as unread: {str(e)}")

def archive_message(service, message_id):
    """Archive a message (remove from inbox)"""
    try:
        message_ops = MessageOperations(service)
        message_ops.archive_message(message_id)
        print(f"Message {message_id} archived")
    except Exception as e:
        print(f"Error archiving message: {str(e)}")

def trash_message(service, message_id):
    """Move a message to trash"""
    try:
        message_ops = MessageOperations(service)
        message_ops.trash_message(message_id)
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