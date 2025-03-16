# api/labels.py
from typing import List, Dict, Any

class LabelOperations:
    """Operations for working with Gmail labels."""
    
    def __init__(self, service):
        """Initialize with a Gmail service instance."""
        self.service = service
    
    def list_labels(self) -> List[Dict[str, Any]]:
        """List all Gmail labels.
        
        Returns:
            List of label objects containing id and name
        """
        results = self.service.users().labels().list(userId='me').execute()
        return results.get('labels', [])
    
    def create_label(self, name: str) -> Dict[str, Any]:
        """Create a new Gmail label.
        
        Args:
            name: Name of the label to create
            
        Returns:
            Created label object
        """
        return self.service.users().labels().create(
            userId='me',
            body={'name': name}
        ).execute()
    
    def delete_label(self, label_id: str) -> None:
        """Delete a Gmail label.
        
        Args:
            label_id: ID of the label to delete
        """
        self.service.users().labels().delete(
            userId='me',
            id=label_id
        ).execute()
    
    def get_label(self, label_id: str) -> Dict[str, Any]:
        """Get a specific Gmail label.
        
        Args:
            label_id: ID of the label to retrieve
            
        Returns:
            Label object
        """
        return self.service.users().labels().get(
            userId='me',
            id=label_id
        ).execute()