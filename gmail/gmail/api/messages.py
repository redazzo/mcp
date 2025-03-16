# api/messages.py
import base64
from email.mime.text import MIMEText
from typing import Dict, Any, List, Optional

class MessageOperations:
    """Operations for working with Gmail messages."""
    
    def __init__(self, service):
        """Initialize with a Gmail service instance."""
        self.service = service
    
    def get_message(self, message_id: str) -> Dict[str, Any]:
        """Get a specific message by ID.
        
        Args:
            message_id: ID of the message to retrieve
            
        Returns:
            Message object with full details
        """
        return self.service.users().messages().get(userId='me', id=message_id).execute()
    
    def list_messages(self, label_ids: List[str] = None, query: str = None, 
                     max_results: int = 10) -> List[Dict[str, Any]]:
        """List messages matching the specified criteria.
        
        Args:
            label_ids: Optional list of label IDs to filter by
            query: Optional Gmail search query
            max_results: Maximum number of results to return
            
        Returns:
            List of message objects (minimal details)
        """
        params = {'userId': 'me', 'maxResults': max_results}
        if label_ids:
            params['labelIds'] = label_ids
        if query:
            params['q'] = query
            
        results = self.service.users().messages().list(**params).execute()
        return results.get('messages', [])
    
    def send_message(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """Send an email message.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body content
            
        Returns:
            Sent message object
        """
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        
        raw_message = base64.urlsafe_b64encode(message.as_string().encode('utf-8')).decode('utf-8')
        
        return self.service.users().messages().send(
            userId='me', body={'raw': raw_message}).execute()
    
    def modify_message(self, message_id: str, add_label_ids: List[str] = None, 
                      remove_label_ids: List[str] = None) -> Dict[str, Any]:
        """Modify a message by adding or removing labels.
        
        Args:
            message_id: ID of the message to modify
            add_label_ids: Optional list of label IDs to add
            remove_label_ids: Optional list of label IDs to remove
            
        Returns:
            Modified message object
        """
        body = {}
        if add_label_ids:
            body['addLabelIds'] = add_label_ids
        if remove_label_ids:
            body['removeLabelIds'] = remove_label_ids
            
        return self.service.users().messages().modify(
            userId='me', id=message_id, body=body).execute()
    
    def trash_message(self, message_id: str) -> Dict[str, Any]:
        """Move a message to trash.
        
        Args:
            message_id: ID of the message to trash
            
        Returns:
            Trashed message object
        """
        return self.service.users().messages().trash(userId='me', id=message_id).execute()
    
    def mark_as_read(self, message_id: str) -> Dict[str, Any]:
        """Mark a message as read by removing the UNREAD label.
        
        Args:
            message_id: ID of the message to mark as read
            
        Returns:
            Modified message object
        """
        return self.modify_message(message_id, remove_label_ids=['UNREAD'])
    
    def mark_as_unread(self, message_id: str) -> Dict[str, Any]:
        """Mark a message as unread by adding the UNREAD label.
        
        Args:
            message_id: ID of the message to mark as unread
            
        Returns:
            Modified message object
        """
        return self.modify_message(message_id, add_label_ids=['UNREAD'])
    
    def archive_message(self, message_id: str) -> Dict[str, Any]:
        """Archive a message by removing the INBOX label.
        
        Args:
            message_id: ID of the message to archive
            
        Returns:
            Modified message object
        """
        return self.modify_message(message_id, remove_label_ids=['INBOX'])