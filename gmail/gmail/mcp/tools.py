# mcp/tools.py
from typing import Dict, Any, List, Optional
from ..api.labels import LabelOperations
from ..api.messages import MessageOperations
from ..api.drafts import DraftOperations
from ..api.threads import ThreadOperations
from ..utils import format_email_metadata, get_message_content, normalize_message_id

class GmailTools:
    """MCP tools for Gmail operations."""
    
    def __init__(self, mcp_server, gmail_client):
        """Initialize with an MCP server and Gmail client."""
        self.mcp = mcp_server
        self.gmail_client = gmail_client
        self.register_tools()
    
    def register_tools(self):
        """Register all Gmail tools with the MCP server."""
        self.mcp.tool()(self.get_labels_tool)
        self.mcp.tool()(self.get_inbox_messages)
        self.mcp.tool()(self.get_message_content_tool)
        self.mcp.tool()(self.send_email)
        self.mcp.tool()(self.search_emails_tool)
        self.mcp.tool()(self.create_draft)
        self.mcp.tool()(self.add_label_to_message)
        self.mcp.tool()(self.get_thread)
        self.mcp.tool()(self.mark_as_read)
        self.mcp.tool()(self.mark_as_unread)
        self.mcp.tool()(self.archive_message)
        self.mcp.tool()(self.trash_message)
    
    def get_labels_tool(self) -> str:
        """Get all Gmail labels and their IDs."""
        service = self.gmail_client.service
        label_ops = LabelOperations(service)
        labels = label_ops.list_labels()
        
        if not labels:
            return "No labels found."
        
        formatted = []
        for label in labels:
            formatted.append(f"- {label['name']} (ID: {label['id']})")
        
        return "Gmail Labels:\n" + "\n".join(formatted)
    
    def get_inbox_messages(self, max_results: int = 10) -> str:
        """Get recent messages from the Gmail inbox with customizable result count."""
        service = self.gmail_client.service
        message_ops = MessageOperations(service)
        
        # Validate max_results
        max_results = min(max(1, max_results), 50)
        
        messages = message_ops.list_messages(label_ids=['INBOX'], max_results=max_results)
        
        if not messages:
            return "No messages found in inbox."
        
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
        
        return "Recent Inbox Messages:\n\n" + "\n---\n".join(formatted)
    
    def get_message_content_tool(self, message_id: str) -> str:
        """Get the full content of a specific email message by its ID."""
        try:
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
        except Exception as e:
            return f"Error retrieving message: {str(e)}"
    
    def send_email(self, to: str, subject: str, body: str) -> str:
        """Send an email from your Gmail account to a specified recipient."""
        try:
            service = self.gmail_client.service
            message_ops = MessageOperations(service)
            
            result = message_ops.send_message(to, subject, body)
            return f"Email sent successfully to {to}. Message ID: {result['id']}"
        except Exception as e:
            return f"Error sending email: {str(e)}"
    
    def search_emails_tool(self, query: str, max_results: int = 10) -> str:
        """Search for emails using Gmail search syntax and control the number of results."""
        service = self.gmail_client.service
        message_ops = MessageOperations(service)
        
        # Validate max_results
        max_results = min(max(1, max_results), 100)
        
        messages = message_ops.list_messages(query=query, max_results=max_results)
        
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
                f"Snippet: {meta['snippet']}"
            )
        
        return f"Search Results for '{query}':\n\n" + "\n---\n".join(formatted)
    
    def create_draft(self, to: str, subject: str, body: str) -> str:
        """Create a draft email in your Gmail account."""
        try:
            service = self.gmail_client.service
            draft_ops = DraftOperations(service)
            
            result = draft_ops.create_draft(to, subject, body)
            return f"Draft created successfully. Draft ID: {result['id']}"
        except Exception as e:
            return f"Error creating draft: {str(e)}"
    
    def add_label_to_message(self, message_id: str, label_name: str) -> str:
        """Add a label to a specific email message."""
        service = self.gmail_client.service
        label_ops = LabelOperations(service)
        message_ops = MessageOperations(service)
        
        # Normalize message ID
        message_id_str = normalize_message_id(message_id)
        
        # First check if label exists
        labels = label_ops.list_labels()
        
        label_id = None
        for label in labels:
            if label['name'].lower() == label_name.lower():
                label_id = label['id']
                break
        
        # If label doesn't exist, create it
        if not label_id:
            try:
                created_label = label_ops.create_label(label_name)
                label_id = created_label['id']
            except Exception as e:
                return f"Error creating label: {str(e)}"
        
        # Add label to message
        try:
            message_ops.modify_message(message_id_str, add_label_ids=[label_id])
            return f"Label '{label_name}' added to message {message_id_str}"
        except Exception as e:
            return f"Error adding label to message: {str(e)}"
    
    def get_thread(self, thread_id: str) -> str:
        """Get all messages in an email conversation thread."""
        try:
            service = self.gmail_client.service
            thread_ops = ThreadOperations(service)
            
            # Normalize thread ID
            thread_id_str = normalize_message_id(thread_id)
            
            thread = thread_ops.get_thread(thread_id_str)
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
    
    def mark_as_read(self, message_id: str) -> str:
        """Mark an email message as read (removes the UNREAD label)."""
        try:
            service = self.gmail_client.service
            message_ops = MessageOperations(service)
            
            # Normalize message ID
            message_id_str = normalize_message_id(message_id)
            
            message_ops.mark_as_read(message_id_str)
            return f"Message {message_id_str} marked as read"
        except Exception as e:
            return f"Error marking message as read: {str(e)}"
    
    def mark_as_unread(self, message_id: str) -> str:
        """Mark an email message as unread (adds the UNREAD label)."""
        try:
            service = self.gmail_client.service
            message_ops = MessageOperations(service)
            
            # Normalize message ID
            message_id_str = normalize_message_id(message_id)
            
            message_ops.mark_as_unread(message_id_str)
            return f"Message {message_id_str} marked as unread"
        except Exception as e:
            return f"Error marking message as unread: {str(e)}"
    
    def archive_message(self, message_id: str) -> str:
        """Archive an email message (removes the INBOX label)."""
        try:
            service = self.gmail_client.service
            message_ops = MessageOperations(service)
            
            # Normalize message ID
            message_id_str = normalize_message_id(message_id)
            
            message_ops.archive_message(message_id_str)
            return f"Message {message_id_str} archived"
        except Exception as e:
            return f"Error archiving message: {str(e)}"
    
    def trash_message(self, message_id: str) -> str:
        """Move an email message to the Gmail trash."""
        try:
            service = self.gmail_client.service
            message_ops = MessageOperations(service)
            
            # Normalize message ID
            message_id_str = normalize_message_id(message_id)
            
            message_ops.trash_message(message_id_str)
            return f"Message {message_id_str} moved to trash"
        except Exception as e:
            return f"Error moving message to trash: {str(e)}"