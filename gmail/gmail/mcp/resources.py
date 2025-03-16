# mcp/resources.py
from typing import Dict, Any, List, Optional
from ..api.labels import LabelOperations
from ..api.messages import MessageOperations
from ..utils import format_email_metadata, get_message_content, normalize_message_id

class GmailResources:
    """MCP resources for Gmail operations."""
    
    def __init__(self, mcp_server, gmail_client):
        """Initialize with an MCP server and Gmail client."""
        self.mcp = mcp_server
        self.gmail_client = gmail_client
        self.register_resources()
    
    def register_resources(self):
        """Register all Gmail resources with the MCP server."""
        self.mcp.resource("gmail://labels")(self.get_labels)
        self.mcp.resource("gmail://inbox")(self.get_inbox)
        self.mcp.resource("gmail://message/{message_id}")(self.get_message)
        self.mcp.resource("gmail://search/{query}")(self.search_emails)
    
    def get_labels(self) -> str:
        """Get all Gmail labels and their IDs.
        
        This resource retrieves all labels from the user's Gmail account,
        including system labels (like INBOX, SENT, TRASH) and user-created labels.
        
        Returns:
            Formatted string listing all Gmail labels with their IDs
        """
        service = self.gmail_client.service
        label_ops = LabelOperations(service)
        labels = label_ops.list_labels()
        
        if not labels:
            return "No labels found."
        
        formatted = []
        for label in labels:
            formatted.append(f"- {label['name']} (ID: {label['id']})")
        
        return "Gmail Labels:\n" + "\n".join(formatted)
    
    def get_inbox(self) -> str:
        """Get the 10 most recent messages from the Gmail inbox.
        
        This resource retrieves recent emails from the inbox and formats them
        with key information like sender, subject, date, and a snippet of content.
        
        Returns:
            Formatted string containing details of up to 10 recent inbox messages
        """
        service = self.gmail_client.service
        message_ops = MessageOperations(service)
        messages = message_ops.list_messages(label_ids=['INBOX'], max_results=10)
        
        if not messages:
            return "No messages found in inbox."
        
        formatted = []
        for msg in messages:
            message = message_ops.get_message(msg['id'])
            meta = format_email_metadata(message)
            formatted.append(
                f"From: {meta['from']}\n"
                f"Subject: {meta['subject']}\n"
                f"Date: {meta['date']}\n"
                f"Snippet: {meta['snippet']}\n"
            )
        
        return "Recent Inbox Messages:\n\n" + "\n---\n".join(formatted)
    
    def get_message(self, message_id: str) -> str:
        """Get the full content of a specific email message by its ID.
        
        This resource retrieves a complete email message including headers and body content.
        
        Args:
            message_id: The unique identifier of the email message
            
        Returns:
            Formatted string containing the email headers and body content
        """
        service = self.gmail_client.service
        message_ops = MessageOperations(service)
        
        # Normalize message ID
        message_id_str = normalize_message_id(message_id)
        
        message = message_ops.get_message(message_id_str)
        meta = format_email_metadata(message)
        content = get_message_content(message)
        
        return (
            f"From: {meta['from']}\n"
            f"To: {meta['to']}\n"
            f"Subject: {meta['subject']}\n"
            f"Date: {meta['date']}\n\n"
            f"{content}"
        )
    
    def search_emails(self, query: str) -> str:
        """Search for emails using Gmail search syntax.
        
        This resource allows searching emails using Gmail's powerful search operators.
        
        Args:
            query: Gmail search query (e.g., "from:example@gmail.com", "subject:meeting")
            
        Returns:
            Formatted string containing up to 10 matching email messages with their IDs
        """
        service = self.gmail_client.service
        message_ops = MessageOperations(service)
        
        messages = message_ops.list_messages(query=query, max_results=10)
        
        if not messages:
            return f"No messages found matching: {query}"
        
        formatted = []
        for msg in messages:
            message = message_ops.get_message(msg['id'])
            meta = format_email_metadata(message)
            formatted.append(
                f"ID: {meta['id']}\n"
                f"From: {meta['from']}\n"
                f"Subject: {meta['subject']}\n"
                f"Date: {meta['date']}\n"
                f"Snippet: {meta['snippet']}\n"
            )
        
        return f"Search Results for '{query}':\n\n" + "\n---\n".join(formatted)