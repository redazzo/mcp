# utils.py
import base64
from typing import Dict, Any

def format_email_metadata(message: Dict[str, Any]) -> Dict[str, Any]:
    """Format email metadata from Gmail API response into a readable dictionary.

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

def get_message_content(message: Dict[str, Any]) -> str:
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

def normalize_message_id(message_id: str) -> str:
    """Normalize a message ID by removing any 'id_' prefix.
    
    Args:
        message_id: The message ID to normalize
        
    Returns:
        Normalized message ID
    """
    message_id_str = str(message_id)
    if message_id_str.startswith("id_"):
        return message_id_str[3:]
    return message_id_str