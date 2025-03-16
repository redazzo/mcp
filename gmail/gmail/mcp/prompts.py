# mcp/prompts.py
from ..utils import normalize_message_id

class GmailPrompts:
    """MCP prompts for Gmail operations."""
    
    def __init__(self, mcp_server):
        """Initialize with an MCP server."""
        self.mcp = mcp_server
        self.register_prompts()
    
    def register_prompts(self):
        """Register all Gmail prompts with the MCP server."""
        self.mcp.prompt()(self.compose_email)
        self.mcp.prompt()(self.summarize_emails)
        self.mcp.prompt()(self.generate_reply)
        self.mcp.prompt()(self.organize_inbox)
    
    def compose_email(self, to: str, subject: str = "", topic: str = "") -> str:
        """Create a prompt for composing an email.
        
        Args:
            to: Recipient email address
            subject: Optional email subject
            topic: Optional topic to discuss in the email
            
        Returns:
            A formatted prompt for the LLM to compose an email
        """
        prompt = f"Please help me compose an email to {to}."
        
        if subject:
            prompt += f" The subject is '{subject}'."
        
        if topic:
            prompt += f" I need to write about the following topic: {topic}."
        
        prompt += "\n\nPlease format the email with a professional greeting, body, and signature."
        
        return prompt
    
    def summarize_emails(self, search_query: str = "in:inbox") -> str:
        """Create a prompt for summarizing emails matching a search query.
        
        Args:
            search_query: Gmail search query to find emails to summarize
            
        Returns:
            A formatted prompt for the LLM to summarize matching emails
        """
        return f"""Please help me summarize recent emails matching the search query: '{search_query}'.

First, I'll use the search_emails_tool to find these emails, and then I'd like you to:
1. Group emails by sender or topic
2. Identify key information and action items
3. Provide a brief summary of each important conversation
4. Note any emails that require urgent attention

Please organize the summary in a clear, scannable format."""
    
    def generate_reply(self, message_id: str) -> str:
        """Create a prompt for generating a reply to a specific email.
        
        Args:
            message_id: ID of the message to reply to
            
        Returns:
            A formatted prompt for the LLM to generate an email reply
        """
        # Normalize message ID
        message_id_str = normalize_message_id(message_id)
        
        return f"""Please help me draft a reply to the email with ID: {message_id_str}.

First, I'll retrieve the email content using the get_message resource, and then I'd like you to:
1. Draft a professional and appropriate response
2. Address all questions or requests from the original email
3. Maintain a similar tone to the original message
4. Keep the response concise but complete

Please format the reply so I can easily use it with the send_email tool."""
    
    def organize_inbox(self, suggestions: bool = True) -> str:
        """Create a prompt for organizing your Gmail inbox.
        
        Args:
            suggestions: Whether to include label and filter organization suggestions
            
        Returns:
            A formatted prompt for the LLM to help organize the Gmail inbox
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