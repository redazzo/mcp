# api/threads.py
from typing import Dict, Any, List

class ThreadOperations:
    """Operations for working with Gmail threads."""
    
    def __init__(self, service):
        """Initialize with a Gmail service instance."""
        self.service = service
    
    def list_threads(self, label_ids: List[str] = None, query: str = None, 
                    max_results: int = 10) -> List[Dict[str, Any]]:
        """List threads matching the specified criteria.
        
        Args:
            label_ids: Optional list of label IDs to filter by
            query: Optional Gmail search query
            max_results: Maximum number of results to return
            
        Returns:
            List of thread objects (minimal details)
        """
        params = {'userId': 'me', 'maxResults': max_results}
        if label_ids:
            params['labelIds'] = label_ids
        if query:
            params['q'] = query
            
        results = self.service.users().threads().list(**params).execute()
        return results.get('threads', [])
    
    def get_thread(self, thread_id: str) -> Dict[str, Any]:
        """Get a specific thread by ID.
        
        Args:
            thread_id: ID of the thread to retrieve
            
        Returns:
            Thread object with full details including all messages
        """
        return self.service.users().threads().get(
            userId='me', id=thread_id).execute()
    
    def modify_thread(self, thread_id: str, add_label_ids: List[str] = None, 
                     remove_label_ids: List[str] = None) -> Dict[str, Any]:
        """Modify a thread by adding or removing labels.
        
        Args:
            thread_id: ID of the thread to modify
            add_label_ids: Optional list of label IDs to add
            remove_label_ids: Optional list of label IDs to remove
            
        Returns:
            Modified thread object
        """
        body = {}
        if add_label_ids:
            body['addLabelIds'] = add_label_ids
        if remove_label_ids:
            body['removeLabelIds'] = remove_label_ids
            
        return self.service.users().threads().modify(
            userId='me', id=thread_id, body=body).execute()
    
    def trash_thread(self, thread_id: str) -> Dict[str, Any]:
        """Move a thread to trash.
        
        Args:
            thread_id: ID of the thread to trash
            
        Returns:
            Trashed thread object
        """
        return self.service.users().threads().trash(
            userId='me', id=thread_id).execute()