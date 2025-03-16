# api/drafts.py
import base64
from email.mime.text import MIMEText
from typing import Dict, Any, List

class DraftOperations:
    """Operations for working with Gmail drafts."""
    
    def __init__(self, service):
        """Initialize with a Gmail service instance."""
        self.service = service
    
    def list_drafts(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """List Gmail drafts.
        
        Args:
            max_results: Maximum number of drafts to retrieve
            
        Returns:
            List of draft objects
        """
        results = self.service.users().drafts().list(
            userId='me', maxResults=max_results).execute()
        return results.get('drafts', [])
    
    def get_draft(self, draft_id: str) -> Dict[str, Any]:
        """Get a specific draft by ID.
        
        Args:
            draft_id: ID of the draft to retrieve
            
        Returns:
            Draft object with full details
        """
        return self.service.users().drafts().get(
            userId='me', id=draft_id).execute()
    
    def create_draft(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """Create a new draft email.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body content
            
        Returns:
            Created draft object
        """
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        
        raw_message = base64.urlsafe_b64encode(message.as_string().encode('utf-8')).decode('utf-8')
        
        return self.service.users().drafts().create(
            userId='me',
            body={'message': {'raw': raw_message}}
        ).execute()
    
    def delete_draft(self, draft_id: str) -> None:
        """Delete a draft.
        
        Args:
            draft_id: ID of the draft to delete
        """
        self.service.users().drafts().delete(
            userId='me',
            id=draft_id
        ).execute()
    
    def send_draft(self, draft_id: str) -> Dict[str, Any]:
        """Send an existing draft.
        
        Args:
            draft_id: ID of the draft to send
            
        Returns:
            Sent message object
        """
        return self.service.users().drafts().send(
            userId='me',
            body={'id': draft_id}
        ).execute()