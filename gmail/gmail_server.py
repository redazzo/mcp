# gmail_server.py
import os
import base64
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from contextlib import asynccontextmanager
from typing import AsyncIterator, List, Dict, Any, Optional
from datetime import datetime

# MCP imports
from mcp.server.fastmcp import FastMCP

# Google API imports
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build, Resource

# Define the Gmail API scopes needed
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.labels'
]

# Global variable for Gmail service
gmail_service = None


# Gmail credential helpers
def get_credentials():
    """Get valid user credentials from storage or initiate OAuth2 flow.

    This function handles Gmail authentication by:
    1. Checking for existing credentials in token.json
    2. Refreshing expired credentials if possible
    3. Initiating a new OAuth2 flow if needed
    4. Saving valid credentials for future use

    Returns:
        Google OAuth2 credentials object for Gmail API access
    """
    creds = None
    script_dir = os.path.dirname(os.path.abspath(__file__))
    token_path = os.path.join(script_dir, 'token.json')
    credentials_path = os.path.join(script_dir, 'credentials.json')

    # Check if token.json exists (stored credentials)
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_info(
            json.loads(open(token_path).read()), SCOPES)

    # If no credentials or they're invalid, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return creds


@asynccontextmanager
async def gmail_lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Initialize Gmail API client and manage its lifecycle.

    This async context manager:
    1. Authenticates with Gmail using OAuth2
    2. Creates a global Gmail service instance for use by all MCP tools and resources
    3. Ensures proper cleanup when the server shuts down

    This is a critical component that must execute successfully for any Gmail
    operations to work.
    """
    global gmail_service
    try:
        # Get credentials and build the service
        creds = get_credentials()
        gmail_service = build('gmail', 'v1', credentials=creds)
        yield
    finally:
        gmail_service = None


# Create the MCP server with Gmail lifespan
mcp = FastMCP("Gmail Server", lifespan=gmail_lifespan)


# Helper functions for Gmail operations
def format_email_metadata(message):
    """Format email metadata from Gmail API response into a readable dictionary.

    This function extracts key information from the complex Gmail API message object,
    making it easier to access common email fields like sender, recipient, subject, etc.

    Args:
        message: Raw Gmail API message object with nested structure

    Returns:
        Dictionary containing formatted email metadata with keys:
        - id: Unique message identifier
        - threadId: Conversation thread identifier
        - labelIds: List of Gmail labels applied to the message
        - snippet: Brief preview of the message content
        - from: Sender's email address
        - to: Recipient's email address
        - subject: Email subject line
        - date: Timestamp of the message
    """
    headers = {h["name"]: h["value"] for h in message["payload"]["headers"]}
    return {
        "id": message["id"],
        "threadId": message["threadId"],
        "labelIds": message.get("labelIds", []),
        "snippet": message.get("snippet", ""),
        "from": headers.get("From", ""),
        "to": headers.get("To", ""),
        "subject": headers.get("Subject", ""),
        "date": headers.get("Date", "")
    }


def get_message_content(message):
    """Extract the plain text content from a Gmail message.

    Gmail messages can have complex MIME structures with multiple parts.
    This function navigates through the message parts to find and extract
    the plain text content, handling base64 encoding.

    Args:
        message: Raw Gmail API message object

    Returns:
        String containing the decoded plain text content of the email.
        Returns empty string if no plain text content is found.

    Note:
        This function prioritizes text/plain content and doesn't extract HTML
        or attachments. For a complete message with all parts, you would need
        additional processing.
    """
    parts = [message["payload"]]
    content = ""

    while parts:
        part = parts.pop(0)
        if part.get("parts"):
            parts.extend(part["parts"])

        if part.get("mimeType") == "text/plain" and part.get("body") and part["body"].get("data"):
            content += base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")

    return content


# === MCP RESOURCES ===
# Resources provide readonly access to Gmail data and are accessed using
# access_mcp_resource() with a specific URI pattern.

@mcp.resource("gmail://labels")
def get_labels() -> str:
    """Get all Gmail labels and their IDs.

    This resource retrieves all labels from the user's Gmail account,
    including system labels (like INBOX, SENT, TRASH) and user-created labels.

    IMPORTANT: This is the CORRECT way to retrieve Gmail labels. Do NOT use
    search_emails_tool with query="label" instead.

    Access this resource with: access_mcp_resource with uri="gmail://labels"

    Returns:
        Formatted string listing all Gmail labels with their IDs

    Example output:
        Gmail Labels:
        - INBOX (ID: INBOX)
        - SENT (ID: SENT)
        - Work (ID: Label_123)

    Example usage:
        labels = access_mcp_resource(
            server_name="gmail",
            uri="gmail://labels"
        )
    """
    global gmail_service

    results = gmail_service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])

    if not labels:
        return "No labels found."

    formatted = []
    for label in labels:
        formatted.append(f"- {label['name']} (ID: {label['id']})")

    return "Gmail Labels:\n" + "\n".join(formatted)


@mcp.resource("gmail://inbox")
def get_inbox() -> str:
    """Get the 10 most recent messages from the Gmail inbox.

    This resource retrieves recent emails from the inbox and formats them
    with key information like sender, subject, date, and a snippet of content.

    Access this resource with: access_mcp_resource with uri="gmail://inbox"

    Returns:
        Formatted string containing details of up to 10 recent inbox messages

    Example output:
        Recent Inbox Messages:

        From: sender@example.com
        Subject: Meeting Tomorrow
        Date: Mon, 10 Mar 2025 10:30:45 +0000
        Snippet: Let's discuss the project status...

        ---

        From: another@example.com
        Subject: Weekly Report
        Date: Mon, 10 Mar 2025 09:15:22 +0000
        Snippet: Attached is the weekly report for...

    Example usage:
        inbox_messages = access_mcp_resource(
            server_name="gmail",
            uri="gmail://inbox"
        )
    """
    global gmail_service

    results = gmail_service.users().messages().list(
        userId='me', labelIds=['INBOX'], maxResults=10).execute()
    messages = results.get('messages', [])

    if not messages:
        return "No messages found in inbox."

    formatted = []
    for msg in messages:
        message = gmail_service.users().messages().get(userId='me', id=msg['id']).execute()
        meta = format_email_metadata(message)
        formatted.append(
            f"From: {meta['from']}\n"
            f"Subject: {meta['subject']}\n"
            f"Date: {meta['date']}\n"
            f"Snippet: {meta['snippet']}\n"
        )

    return "Recent Inbox Messages:\n\n" + "\n---\n".join(formatted)


@mcp.resource("gmail://message/{message_id}")
def get_message(message_id: str) -> str:
    """Get the full content of a specific email message by its ID.

    This resource retrieves a complete email message including headers and body content.
    The message_id parameter is part of the URI path.

    IMPORTANT: To use this, you need a specific message ID, which you can obtain from
    other resources like gmail://inbox or by using search_emails_tool.

    Access this resource with: access_mcp_resource with uri="gmail://message/{message_id}"
    where {message_id} is replaced with an actual message ID.

    Args:
        message_id: The unique identifier of the email message

    Returns:
        Formatted string containing the email headers and body content

    Example output:
        From: sender@example.com
        To: recipient@example.com
        Subject: Meeting Agenda
        Date: Mon, 10 Mar 2025 10:30:45 +0000

        Hello,

        Here's the agenda for our meeting tomorrow...

    Example usage:
        message_content = access_mcp_resource(
            server_name="gmail",
            uri=f"gmail://message/{message_id}"
        )
    """
    global gmail_service
    
    # Ensure message_id is a string and remove "id_" prefix if present
    message_id_str = str(message_id)
    if message_id_str.startswith("id_"):
        message_id_str = message_id_str[3:]

    message = gmail_service.users().messages().get(userId='me', id=message_id_str).execute()
    meta = format_email_metadata(message)
    content = get_message_content(message)

    return (
        f"From: {meta['from']}\n"
        f"To: {meta['to']}\n"
        f"Subject: {meta['subject']}\n"
        f"Date: {meta['date']}\n\n"
        f"{content}"
    )


@mcp.resource("gmail://search/{query}")
def search_emails(query: str) -> str:
    """Search for emails using Gmail search syntax and return matching messages.

    This resource allows searching emails using Gmail's powerful search operators.
    The query parameter is part of the URI path and should be URL-encoded.

    IMPORTANT: This is a READ-ONLY resource. To perform a more customizable search with
    control over the number of results, use the search_emails_tool instead.

    Access this resource with: access_mcp_resource with uri="gmail://search/{query}"
    where {query} is replaced with a URL-encoded Gmail search query.

    Args:
        query: Gmail search query (e.g., "from:example@gmail.com", "subject:meeting", "label:work")

    Returns:
        Formatted string containing up to 10 matching email messages with their IDs

    Example search queries:
        - "from:example@gmail.com" - Emails from a specific sender
        - "subject:meeting" - Emails with "meeting" in the subject
        - "label:work" - Emails with the "work" label
        - "is:unread" - Unread emails
        - "after:2025/03/01" - Emails after March 1, 2025

    Example usage:
        search_results = access_mcp_resource(
            server_name="gmail",
            uri="gmail://search/is:unread"
        )
    """
    global gmail_service

    results = gmail_service.users().messages().list(
        userId='me', q=query, maxResults=10).execute()
    messages = results.get('messages', [])

    if not messages:
        return f"No messages found matching: {query}"

    formatted = []
    for msg in messages:
        message = gmail_service.users().messages().get(userId='me', id=msg['id']).execute()
        meta = format_email_metadata(message)
        formatted.append(
            f"ID: {meta['id']}\n"
            f"From: {meta['from']}\n"
            f"Subject: {meta['subject']}\n"
            f"Date: {meta['date']}\n"
            f"Snippet: {meta['snippet']}\n"
        )

    return f"Search Results for '{query}':\n\n" + "\n---\n".join(formatted)


# === MCP TOOLS ===
# Tools provide interactive functionality that modifies Gmail data.
# They are accessed using use_mcp_tool() with specific arguments.

# === CONVERTED RESOURCES INTO TOOLS ===

@mcp.tool()
def get_labels_tool() -> str:
    """Get all Gmail labels and their IDs.

    This tool retrieves all labels from the user's Gmail account,
    including system labels (like INBOX, SENT, TRASH) and user-created labels.

    Use this tool with: use_mcp_tool with tool_name="get_labels_tool"

    Returns:
        Formatted string listing all Gmail labels with their IDs

    Example output:
        Gmail Labels:
        - INBOX (ID: INBOX)
        - SENT (ID: SENT)
        - Work (ID: Label_123)

    Example usage:
        labels = use_mcp_tool(
            server_name="gmail",
            tool_name="get_labels_tool"
        )
    """
    global gmail_service

    results = gmail_service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])

    if not labels:
        return "No labels found."

    formatted = []
    for label in labels:
        formatted.append(f"- {label['name']} (ID: {label['id']})")

    return "Gmail Labels:\n" + "\n".join(formatted)


@mcp.tool()
def get_inbox_messages(max_results: int = 10) -> str:
    """Get recent messages from the Gmail inbox with customizable result count.

    This tool retrieves recent emails from the inbox and formats them
    with key information like sender, subject, date, and a snippet of content.

    Use this tool with: use_mcp_tool with tool_name="get_inbox_messages"

    Args:
        max_results: Maximum number of inbox messages to retrieve (default: 10)

    Returns:
        Formatted string containing details of inbox messages

    Example output:
        Recent Inbox Messages:

        From: sender@example.com
        Subject: Meeting Tomorrow
        Date: Mon, 10 Mar 2025 10:30:45 +0000
        Snippet: Let's discuss the project status...

        ---

        From: another@example.com
        Subject: Weekly Report
        Date: Mon, 10 Mar 2025 09:15:22 +0000
        Snippet: Attached is the weekly report for...

    Example usage:
        inbox_messages = use_mcp_tool(
            server_name="gmail",
            tool_name="get_inbox_messages",
            arguments={
                "max_results": 5
            }
        )
    """
    global gmail_service

    # Validate max_results
    max_results = min(max(1, max_results), 50)

    results = gmail_service.users().messages().list(
        userId='me', labelIds=['INBOX'], maxResults=max_results).execute()
    messages = results.get('messages', [])

    if not messages:
        return "No messages found in inbox."

    formatted = []
    for msg in messages:
        message = gmail_service.users().messages().get(userId='me', id=msg['id']).execute()
        meta = format_email_metadata(message)
        formatted.append(
            f"ID: {meta['id']}\n"
            f"From: {meta['from']}\n"
            f"Subject: {meta['subject']}\n"
            f"Date: {meta['date']}\n"
            f"Snippet: {meta['snippet']}\n"
        )

    return "Recent Inbox Messages:\n\n" + "\n---\n".join(formatted)


@mcp.tool()
def get_message_content_tool(message_id: str) -> str:
    """Get the full content of a specific email message by its ID.

    This tool retrieves a complete email message including headers and body content.

    Use this tool with: use_mcp_tool with tool_name="get_message_content_tool"

    Args:
        message_id: The unique identifier of the email message

    Returns:
        Formatted string containing the email headers and body content

    Example output:
        From: sender@example.com
        To: recipient@example.com
        Subject: Meeting Agenda
        Date: Mon, 10 Mar 2025 10:30:45 +0000

        Hello,

        Here's the agenda for our meeting tomorrow...

    Example usage:
        message_content = use_mcp_tool(
            server_name="gmail",
            tool_name="get_message_content_tool",
            arguments={
                "message_id": "18abc123def456"
            }
        )
    """
    global gmail_service

    try:
        # Ensure message_id is a string and remove "id_" prefix if present
        message_id_str = str(message_id)
        if message_id_str.startswith("id_"):
            message_id_str = message_id_str[3:]
        
        message = gmail_service.users().messages().get(userId='me', id=message_id_str).execute()
        meta = format_email_metadata(message)
        content = get_message_content(message)

        return (
            f"From: {meta['from']}\n"
            f"To: {meta['to']}\n"
            f"Subject: {meta['subject']}\n"
            f"Date: {meta['date']}\n\n"
            f"{content}"
        )
    except Exception as e:
        return f"Error retrieving message: {str(e)}"

@mcp.tool()
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email from your Gmail account to a specified recipient.

    This tool composes and sends a plain text email using your authenticated Gmail account.
    The email will appear in the recipient's inbox as coming from your email address.

    Use this tool with: use_mcp_tool with tool_name="send_email"

    Args:
        to: Recipient email address (e.g., "recipient@example.com")
        subject: Email subject line
        body: Plain text content for the email body

    Returns:
        Confirmation message with the sent email's message ID

    Example:
        To send a meeting invitation:
        use_mcp_tool(
            server_name="gmail",
            tool_name="send_email",
            arguments={
                "to": "colleague@company.com",
                "subject": "Team Meeting Tomorrow",
                "body": "Hi team,\n\nLet's meet tomorrow at 2pm to discuss the project.\n\nRegards,\nYour Name"
            }
        )
    """
    global gmail_service

    message = MIMEText(body)
    message['to'] = to
    message['subject'] = subject

    raw_message = base64.urlsafe_b64encode(message.as_string().encode('utf-8')).decode('utf-8')

    try:
        message = gmail_service.users().messages().send(
            userId='me', body={'raw': raw_message}).execute()
        return f"Email sent successfully to {to}. Message ID: {message['id']}"
    except Exception as e:
        return f"Error sending email: {str(e)}"


@mcp.tool()
def search_emails_tool(query: str, max_results: int) -> str:
    """Search for emails using Gmail search syntax and control the number of results.

    This tool allows searching emails using Gmail's powerful search operators while
    giving you control over how many results to return.

    IMPORTANT: This is NOT the tool to use for retrieving Gmail labels. For labels,
    use access_mcp_resource with uri="gmail://labels" instead.

    Use this tool with: use_mcp_tool with tool_name="search_emails_tool"

    Args:
        query: Gmail search query (e.g., "from:example@gmail.com", "subject:meeting")
        max_results: Maximum number of results to return (1-100)

    Returns:
        Formatted string containing matching email messages with their IDs

    Example search queries:
        - "from:example@gmail.com" - Emails from a specific sender
        - "subject:meeting" - Emails with "meeting" in the subject
        - "label:work" - Emails with the "work" label
        - "is:unread" - Unread emails
        - "after:2025/03/01" - Emails after March 1, 2025

    Example usage:
        search_results = use_mcp_tool(
            server_name="gmail",
            tool_name="search_emails_tool",
            arguments={
                "query": "is:unread",
                "max_results": 20
            }
        )
    """
    global gmail_service

    # Validate max_results
    max_results = min(max(1, max_results), 100)

    results = gmail_service.users().messages().list(
        userId='me', q=query, maxResults=max_results).execute()
    messages = results.get('messages', [])

    if not messages:
        return f"No messages found matching: {query}"

    formatted = []
    for msg in messages:
        message = gmail_service.users().messages().get(userId='me', id=msg['id']).execute()
        meta = format_email_metadata(message)
        formatted.append(
            f"ID: {meta['id']}\n"
            f"From: {meta['from']}\n"
            f"Subject: {meta['subject']}\n"
            f"Date: {meta['date']}\n"
            f"Snippet: {meta['snippet']}"
        )

    return f"Search Results for '{query}':\n\n" + "\n---\n".join(formatted)


@mcp.tool()
def create_draft(to: str, subject: str, body: str) -> str:
    """Create a draft email in your Gmail account.

    This tool composes a draft email that will be saved to your Gmail drafts folder.
    The draft can later be edited and sent from Gmail directly.

    Use this tool with: use_mcp_tool with tool_name="create_draft"

    Args:
        to: Recipient email address (e.g., "recipient@example.com")
        subject: Email subject line
        body: Plain text content for the email body

    Returns:
        Confirmation message with the created draft's ID

    Example usage:
        draft_result = use_mcp_tool(
            server_name="gmail",
            tool_name="create_draft",
            arguments={
                "to": "colleague@company.com",
                "subject": "Project Updates",
                "body": "Hi,\n\nHere are the latest updates on our project...\n\nRegards,\nYour Name"
            }
        )
    """
    global gmail_service

    message = MIMEText(body)
    message['to'] = to
    message['subject'] = subject

    raw_message = base64.urlsafe_b64encode(message.as_string().encode('utf-8')).decode('utf-8')

    try:
        draft = gmail_service.users().drafts().create(
            userId='me',
            body={'message': {'raw': raw_message}}
        ).execute()
        return f"Draft created successfully. Draft ID: {draft['id']}"
    except Exception as e:
        return f"Error creating draft: {str(e)}"


@mcp.tool()
def add_label_to_message(message_id: str, label_name: str) -> str:
    """Add a label to a specific email message.

    This tool applies a label to an email. If the label doesn't exist,
    it will be created automatically.

    Use this tool with: use_mcp_tool with tool_name="add_label_to_message"

    Args:
        message_id: ID of the message to label (obtain this from search results or inbox)
        label_name: Name of the label to add or create

    Returns:
        Confirmation message indicating the label was added

    Example usage:
        label_result = use_mcp_tool(
            server_name="gmail",
            tool_name="add_label_to_message",
            arguments={
                "message_id": "18abc123def456",
                "label_name": "Important"
            }
        )
    """
    global gmail_service

    # Ensure message_id is a string and remove "id_" prefix if present
    message_id_str = str(message_id)
    if message_id_str.startswith("id_"):
        message_id_str = message_id_str[3:]

    # First check if label exists
    results = gmail_service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])

    label_id = None
    for label in labels:
        if label['name'].lower() == label_name.lower():
            label_id = label['id']
            break

    # If label doesn't exist, create it
    if not label_id:
        try:
            created_label = gmail_service.users().labels().create(
                userId='me',
                body={'name': label_name}
            ).execute()
            label_id = created_label['id']
        except Exception as e:
            return f"Error creating label: {str(e)}"

    # Add label to message
    try:
        gmail_service.users().messages().modify(
            userId='me',
            id=message_id_str,
            body={'addLabelIds': [label_id]}
        ).execute()
        return f"Label '{label_name}' added to message {message_id_str}"
    except Exception as e:
        return f"Error adding label to message: {str(e)}"


@mcp.tool()
def get_thread(thread_id: str) -> str:
    """Get all messages in an email conversation thread.

    This tool retrieves all messages in a Gmail conversation thread,
    including back-and-forth replies. This is useful for seeing the
    complete context of an email conversation.

    Use this tool with: use_mcp_tool with tool_name="get_thread"

    Args:
        thread_id: ID of the thread to retrieve (obtain this from message metadata,
                  where it's listed as "threadId")

    Returns:
        Formatted string containing all messages in the thread, ordered chronologically

    Example usage:
        thread_content = use_mcp_tool(
            server_name="gmail",
            tool_name="get_thread",
            arguments={
                "thread_id": "18abc123def456"
            }
        )
    """
    global gmail_service

    try:
        # Ensure thread_id is a string and remove "id_" prefix if present
        thread_id_str = str(thread_id)
        if thread_id_str.startswith("id_"):
            thread_id_str = thread_id_str[3:]
        
        thread = gmail_service.users().threads().get(userId='me', id=thread_id_str).execute()
        messages = thread.get('messages', [])

        if not messages:
            return f"No messages found in thread {thread_id_str}"

        result = []
        for message in messages:
            meta = format_email_metadata(message)
            content = get_message_content(message)
            result.append(
                f"From: {meta['from']}\n"
                f"Date: {meta['date']}\n"
                f"Subject: {meta['subject']}\n\n"
                f"{content}"
            )

        return f"Thread {thread_id_str}:\n\n" + "\n\n====================\n\n".join(result)
    except Exception as e:
        return f"Error retrieving thread: {str(e)}"


@mcp.tool()
def mark_as_read(message_id: str) -> str:
    """Mark an email message as read (removes the UNREAD label).

    This tool marks a specific email message as read, which removes
    the UNREAD label from the message in Gmail.

    Use this tool with: use_mcp_tool with tool_name="mark_as_read"

    Args:
        message_id: ID of the message to mark as read

    Returns:
        Confirmation message indicating the message was marked as read

    Example usage:
        read_result = use_mcp_tool(
            server_name="gmail",
            tool_name="mark_as_read",
            arguments={
                "message_id": "18abc123def456"
            }
        )
    """
    global gmail_service

    try:
        # Ensure message_id is a string and remove "id_" prefix if present
        message_id_str = str(message_id)
        if message_id_str.startswith("id_"):
            message_id_str = message_id_str[3:]
        
        gmail_service.users().messages().modify(
            userId='me',
            id=message_id_str,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        return f"Message {message_id_str} marked as read"
    except Exception as e:
        return f"Error marking message as read: {str(e)}"


@mcp.tool()
def mark_as_unread(message_id: str) -> str:
    """Mark an email message as unread (adds the UNREAD label).

    This tool marks a specific email message as unread, which adds
    the UNREAD label to the message in Gmail.

    Use this tool with: use_mcp_tool with tool_name="mark_as_unread"

    Args:
        message_id: ID of the message to mark as unread

    Returns:
        Confirmation message indicating the message was marked as unread

    Example usage:
        unread_result = use_mcp_tool(
            server_name="gmail",
            tool_name="mark_as_unread",
            arguments={
                "message_id": "18abc123def456"
            }
        )
    """
    global gmail_service

    try:
        # Ensure message_id is a string and remove "id_" prefix if present
        message_id_str = str(message_id)
        if message_id_str.startswith("id_"):
            message_id_str = message_id_str[3:]
        
        gmail_service.users().messages().modify(
            userId='me',
            id=message_id_str,
            body={'addLabelIds': ['UNREAD']}
        ).execute()
        return f"Message {message_id_str} marked as unread"
    except Exception as e:
        return f"Error marking message as unread: {str(e)}"


@mcp.tool()
def archive_message(message_id: str) -> str:
    """Archive an email message (removes the INBOX label).

    This tool archives a specific email message, which removes it from your
    inbox while keeping it in your Gmail account. Technically, this removes
    the INBOX label from the message.

    Use this tool with: use_mcp_tool with tool_name="archive_message"

    Args:
        message_id: ID of the message to archive

    Returns:
        Confirmation message indicating the message was archived

    Example usage:
        archive_result = use_mcp_tool(
            server_name="gmail",
            tool_name="archive_message",
            arguments={
                "message_id": "18abc123def456"
            }
        )
    """
    global gmail_service

    try:
        # Ensure message_id is a string and remove "id_" prefix if present
        message_id_str = str(message_id)
        if message_id_str.startswith("id_"):
            message_id_str = message_id_str[3:]
        
        gmail_service.users().messages().modify(
            userId='me',
            id=message_id_str,
            body={'removeLabelIds': ['INBOX']}
        ).execute()
        return f"Message {message_id_str} archived"
    except Exception as e:
        return f"Error archiving message: {str(e)}"


@mcp.tool()
def trash_message(message_id: str) -> str:
    """Move an email message to the Gmail trash.

    This tool moves a specific email message to the trash in Gmail.
    The message will be permanently deleted after 30 days unless
    manually restored.

    Use this tool with: use_mcp_tool with tool_name="trash_message"

    Args:
        message_id: ID of the message to move to trash

    Returns:
        Confirmation message indicating the message was moved to trash

    Example usage:
        trash_result = use_mcp_tool(
            server_name="gmail",
            tool_name="trash_message",
            arguments={
                "message_id": "18abc123def456"
            }
        )
    """
    global gmail_service

    try:
        # Ensure message_id is a string and remove "id_" prefix if present
        message_id_str = str(message_id)
        if message_id_str.startswith("id_"):
            message_id_str = message_id_str[3:]
        
        gmail_service.users().messages().trash(userId='me', id=message_id_str).execute()
        return f"Message {message_id_str} moved to trash"
    except Exception as e:
        return f"Error moving message to trash: {str(e)}"


# === MCP PROMPTS ===
# Prompts are templates that help generate customized prompts for the LLM.
# They are accessed using get_mcp_prompt() with specific arguments.

@mcp.prompt()
def compose_email(to: str, subject: str = "", topic: str = "") -> str:
    """Create a prompt for composing an email.

    This prompt template helps generate a prompt for the LLM to compose
    an email to a specific recipient. It includes optional subject and topic.

    Use this prompt with: get_mcp_prompt with prompt_name="compose_email"

    Args:
        to: Recipient email address
        subject: Optional email subject
        topic: Optional topic to discuss in the email

    Returns:
        A formatted prompt for the LLM to compose an email

    Example usage:
        prompt = get_mcp_prompt(
            server_name="gmail",
            prompt_name="compose_email",
            arguments={
                "to": "colleague@company.com",
                "subject": "Project Update",
                "topic": "recent progress and next steps"
            }
        )
    """
    prompt = f"Please help me compose an email to {to}."

    if subject:
        prompt += f" The subject is '{subject}'."

    if topic:
        prompt += f" I need to write about the following topic: {topic}."

    prompt += "\n\nPlease format the email with a professional greeting, body, and signature."

    return prompt


@mcp.prompt()
def summarize_emails(search_query: str = "in:inbox") -> str:
    """Create a prompt for summarizing emails matching a search query.

    This prompt template helps generate a prompt for the LLM to summarize
    emails matching a specific Gmail search query.

    Use this prompt with: get_mcp_prompt with prompt_name="summarize_emails"

    Args:
        search_query: Gmail search query to find emails to summarize

    Returns:
        A formatted prompt for the LLM to summarize matching emails

    Example usage:
        prompt = get_mcp_prompt(
            server_name="gmail",
            prompt_name="summarize_emails",
            arguments={
                "search_query": "from:boss@company.com after:2025/01/01"
            }
        )
    """
    return f"""Please help me summarize recent emails matching the search query: '{search_query}'.

First, I'll use the search_emails_tool to find these emails, and then I'd like you to:
1. Group emails by sender or topic
2. Identify key information and action items
3. Provide a brief summary of each important conversation
4. Note any emails that require urgent attention

Please organize the summary in a clear, scannable format."""


@mcp.prompt()
def generate_reply(message_id: str) -> str:
    """Create a prompt for generating a reply to a specific email.

    This prompt template helps generate a prompt for the LLM to draft
    a reply to a specific email message identified by its ID.

    Use this prompt with: get_mcp_prompt with prompt_name="generate_reply"

    Args:
        message_id: ID of the message to reply to (obtain this from search results or inbox)

    Returns:
        A formatted prompt for the LLM to generate an email reply

    Example usage:
        prompt = get_mcp_prompt(
            server_name="gmail",
            prompt_name="generate_reply",
            arguments={
                "message_id": "18abc123def456"
            }
        )
    """
    # Ensure message_id is a string and remove "id_" prefix if present
    message_id_str = str(message_id)
    if message_id_str.startswith("id_"):
        message_id_str = message_id_str[3:]
    
    return f"""Please help me draft a reply to the email with ID: {message_id_str}.

First, I'll retrieve the email content using the get_message resource, and then I'd like you to:
1. Draft a professional and appropriate response
2. Address all questions or requests from the original email
3. Maintain a similar tone to the original message
4. Keep the response concise but complete

Please format the reply so I can easily use it with the send_email tool."""


@mcp.prompt()
def organize_inbox(suggestions: bool = True) -> str:
    """Create a prompt for organizing your Gmail inbox.

    This prompt template helps generate a prompt for the LLM to assist
    with organizing your Gmail inbox, optionally including suggestions
    for labels and filters.

    Use this prompt with: get_mcp_prompt with prompt_name="organize_inbox"

    Args:
        suggestions: Whether to include label and filter organization suggestions

    Returns:
        A formatted prompt for the LLM to help organize the Gmail inbox

    Example usage:
        prompt = get_mcp_prompt(
            server_name="gmail",
            prompt_name="organize_inbox",
            arguments={
                "suggestions": True
            }
        )
    """
    prompt = """Please help me organize my Gmail inbox.

First, I'll retrieve my current labels and recent inbox messages, and then I'd like you to:
1. Analyze my email patterns
2. Suggest actions for specific emails (archive, label, etc.)
3. Help me process emails that need responses"""

    if suggestions:
        prompt += """
4. Suggest a labeling system to better organize my emails
5. Recommend filters that might help manage my incoming mail"""

    return prompt


# Add error handling for the main execution
if __name__ == "__main__":
    import sys
    import traceback
    import logging
    
    # Configure detailed logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.StreamHandler(sys.stderr)
        ]
    )
    
    # Enable debug logging for MCP and anyio
    logging.getLogger('mcp').setLevel(logging.DEBUG)
    logging.getLogger('anyio').setLevel(logging.DEBUG)
    
    print("Starting Gmail MCP Server with enhanced logging...", file=sys.stderr)
    
    try:
        # Add custom error handler to log more details
        def custom_error_handler(error):
            print(f"MCP ERROR DETAILS: {type(error).__name__}: {str(error)}", file=sys.stderr)
            if hasattr(error, '__context__') and error.__context__:
                print(f"CAUSED BY: {type(error.__context__).__name__}: {str(error.__context__)}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
        
        mcp.onerror = custom_error_handler
        mcp.run()
    except Exception as e:
        print(f"Error in Gmail MCP Server: {str(e)}", file=sys.stderr)
        print(f"Error type: {type(e).__name__}", file=sys.stderr)
        if hasattr(e, '__context__') and e.__context__:
            print(f"Caused by: {type(e.__context__).__name__}: {str(e.__context__)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)