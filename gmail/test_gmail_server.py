import unittest
import os
import json
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('TestGmailServer')

# Import the modules from gmail_server.py
from gmail_server import (
    get_credentials,
    format_email_metadata,
    get_message_content,
    gmail_service
)

# Import Google API libraries
from googleapiclient.discovery import build

class TestGmailServer(unittest.TestCase):
    """Tests for the Gmail MCP Server functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up the Gmail service for all tests"""
        logger.info("Setting up TestGmailServer test suite")
        
        # Get credentials and build the service
        logger.info("Getting Gmail API credentials")
        cls.creds = get_credentials()
        logger.info("Building Gmail service")
        cls.service = build('gmail', 'v1', credentials=cls.creds)
        
        # Create a unique label for testing
        timestamp = int(time.time())
        cls.test_label_name = f"TestLabel_{timestamp}"
        logger.info(f"Creating test label: {cls.test_label_name}")
        try:
            cls.test_label = cls.service.users().labels().create(
                userId='me',
                body={'name': cls.test_label_name}
            ).execute()
            logger.info(f"Created test label with ID: {cls.test_label['id']}")
        except Exception as e:
            logger.warning(f"Could not create test label: {str(e)}")
            cls.test_label = None
            
        # Create a test draft for testing
        logger.info("Creating test draft email")
        message = {
            'raw': 'RnJvbTogdGVzdEBleGFtcGxlLmNvbQpUbzogdGVzdEBleGFtcGxlLmNvbQpTdWJqZWN0OiBUZXN0IEVtYWlsIGZvciBHbWFpbCBNQ1AgU2VydmVyIFRlc3RzCgpUaGlzIGlzIGEgdGVzdCBlbWFpbCBmb3IgdGVzdGluZyB0aGUgR21haWwgTUNQIFNlcnZlci4='
        }
        try:
            cls.test_draft = cls.service.users().drafts().create(
                userId='me',
                body={'message': message}
            ).execute()
            
            # Get the message ID from the draft
            cls.test_message_id = cls.test_draft['message']['id']
            logger.info(f"Created test draft with message ID: {cls.test_message_id}")
        except Exception as e:
            logger.warning(f"Could not create test draft: {str(e)}")
            cls.test_draft = None
            cls.test_message_id = None
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        logger.info("Cleaning up TestGmailServer test suite")
        
        # Delete the test label if it was created
        if cls.test_label:
            logger.info(f"Deleting test label: {cls.test_label_name}")
            try:
                cls.service.users().labels().delete(
                    userId='me',
                    id=cls.test_label['id']
                ).execute()
                logger.info("Test label deleted successfully")
            except Exception as e:
                logger.warning(f"Could not delete test label: {str(e)}")
        
        # Delete the test draft if it was created
        if cls.test_draft:
            logger.info(f"Deleting test draft")
            try:
                cls.service.users().drafts().delete(
                    userId='me',
                    id=cls.test_draft['id']
                ).execute()
                logger.info("Test draft deleted successfully")
            except Exception as e:
                logger.warning(f"Could not delete test draft: {str(e)}")
    
    def test_get_credentials(self):
        """Test that credentials can be obtained and are valid"""
        logger.info("Testing credential retrieval")
        creds = get_credentials()
        logger.info(f"Credentials obtained, valid: {creds.valid}")
        self.assertIsNotNone(creds, "Credentials should not be None")
        self.assertTrue(creds.valid, "Credentials should be valid")
        logger.info("Credential test completed successfully")
    
    def test_format_email_metadata(self):
        """Test formatting email metadata from Gmail API response"""
        logger.info("Testing email metadata formatting")
        
        # Create a sample message structure
        logger.info("Creating sample message structure")
        message = {
            "id": "12345",
            "threadId": "thread123",
            "labelIds": ["INBOX", "UNREAD"],
            "snippet": "This is a test email",
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "To", "value": "recipient@example.com"},
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "Date", "value": "Mon, 10 Mar 2025 10:30:00 +1300"}
                ]
            }
        }
        
        # Format the metadata
        logger.info("Calling format_email_metadata function")
        metadata = format_email_metadata(message)
        logger.info(f"Metadata formatted: {json.dumps(metadata, indent=2)}")
        
        # Verify the metadata
        logger.info("Verifying metadata fields")
        self.assertEqual(metadata["id"], "12345", "ID should match")
        self.assertEqual(metadata["threadId"], "thread123", "Thread ID should match")
        self.assertEqual(metadata["labelIds"], ["INBOX", "UNREAD"], "Labels should match")
        self.assertEqual(metadata["snippet"], "This is a test email", "Snippet should match")
        self.assertEqual(metadata["from"], "sender@example.com", "From field should match")
        self.assertEqual(metadata["to"], "recipient@example.com", "To field should match")
        self.assertEqual(metadata["subject"], "Test Subject", "Subject should match")
        self.assertEqual(metadata["date"], "Mon, 10 Mar 2025 10:30:00 +1300", "Date should match")
        
        logger.info("Email metadata formatting test completed successfully")
    
    def test_get_labels(self):
        """Test retrieving Gmail labels from the API"""
        logger.info("Testing Gmail label retrieval")
        
        # Get labels from the API
        logger.info("Calling Gmail API to list labels")
        results = self.service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        
        # Log the labels
        logger.info(f"Retrieved {len(labels)} labels")
        for label in labels[:5]:  # Log first 5 labels only to avoid too much output
            logger.info(f"Label: {label['name']} (ID: {label['id']})")
        
        # Verify the labels
        self.assertIsNotNone(labels, "Labels should not be None")
        self.assertIsInstance(labels, list, "Labels should be a list")
        
        # Check if our test label is in the list
        if self.test_label:
            logger.info(f"Checking if test label {self.test_label_name} is in the list")
            label_ids = [label['id'] for label in labels]
            self.assertIn(self.test_label['id'], label_ids, "Test label should be in the list")
            logger.info("Test label found in the list")
        
        logger.info("Gmail label retrieval test completed successfully")
    
    def test_get_inbox_messages(self):
        """Test retrieving messages from the Gmail inbox"""
        logger.info("Testing Gmail inbox message retrieval")
        
        # Get inbox messages from the API
        logger.info("Calling Gmail API to list inbox messages (max 5)")
        results = self.service.users().messages().list(
            userId='me', labelIds=['INBOX'], maxResults=5).execute()
        messages = results.get('messages', [])
        
        # Log the messages
        logger.info(f"Retrieved {len(messages)} inbox messages")
        
        # Verify the messages
        self.assertIsInstance(messages, list, "Messages should be a list")
        
        # If there are messages, check the first one
        if messages:
            logger.info(f"Getting details for first message (ID: {messages[0]['id']})")
            message = self.service.users().messages().get(
                userId='me', id=messages[0]['id']).execute()
            
            # Log message details
            headers = {h["name"]: h["value"] for h in message["payload"]["headers"]}
            logger.info(f"Message from: {headers.get('From', 'Unknown')}")
            logger.info(f"Message subject: {headers.get('Subject', 'No subject')}")
            
            # Verify message structure
            self.assertIn('id', message, "Message should have an ID")
            self.assertIn('threadId', message, "Message should have a thread ID")
            self.assertIn('payload', message, "Message should have a payload")
            logger.info("Message structure verified")
        else:
            logger.info("No messages in inbox to test")
        
        logger.info("Gmail inbox message retrieval test completed successfully")
    
    def test_search_emails(self):
        """Test searching for emails using Gmail search syntax"""
        logger.info("Testing Gmail email search")
        
        # Search for emails from the last 7 days
        query = "newer_than:7d"
        logger.info(f"Searching for emails with query: {query}")
        results = self.service.users().messages().list(
            userId='me', q=query, maxResults=5).execute()
        
        # Log the search results
        logger.info(f"Search returned: {results}")
        
        # Verify the results
        self.assertIsInstance(results, dict, "Results should be a dictionary")
        
        if 'messages' in results:
            messages = results['messages']
            logger.info(f"Found {len(messages)} messages matching the search")
            self.assertIsInstance(messages, list, "Messages should be a list")
            
            # If there are messages, check the first one
            if messages:
                logger.info(f"Getting details for first search result (ID: {messages[0]['id']})")
                message = self.service.users().messages().get(
                    userId='me', id=messages[0]['id']).execute()
                
                # Log message details
                headers = {h["name"]: h["value"] for h in message["payload"]["headers"]}
                logger.info(f"Message from: {headers.get('From', 'Unknown')}")
                logger.info(f"Message subject: {headers.get('Subject', 'No subject')}")
                
                # Verify message structure
                self.assertIn('id', message, "Message should have an ID")
                self.assertIn('threadId', message, "Message should have a thread ID")
                logger.info("Message structure verified")
        else:
            logger.info("No messages found matching the search query")
        
        logger.info("Gmail email search test completed successfully")
    
    def test_get_message_content(self):
        """Test extracting plain text content from a Gmail message"""
        logger.info("Testing message content extraction")
        
        # Skip if we don't have a test message
        if not self.test_message_id:
            logger.warning("No test message available, skipping test")
            self.skipTest("No test message available")
        
        # Get the message from the API
        logger.info(f"Getting message with ID: {self.test_message_id}")
        message = self.service.users().messages().get(
            userId='me', id=self.test_message_id).execute()
        
        # Extract the content
        logger.info("Extracting message content")
        content = get_message_content(message)
        
        # Log the content
        logger.info(f"Extracted content (first 100 chars): {content[:100]}")
        
        # Verify the content
        self.assertIsInstance(content, str, "Content should be a string")
        logger.info("Message content extraction test completed successfully")
    
    def test_add_and_remove_label(self):
        """Test adding and removing a label from a Gmail message"""
        logger.info("Testing label addition and removal")
        
        # Skip if we don't have a test message or label
        if not self.test_message_id or not self.test_label:
            logger.warning("No test message or label available, skipping test")
            self.skipTest("No test message or label available")
        
        # Add the label to the message
        logger.info(f"Adding label {self.test_label_name} to message {self.test_message_id}")
        self.service.users().messages().modify(
            userId='me',
            id=self.test_message_id,
            body={'addLabelIds': [self.test_label['id']]}
        ).execute()
        
        # Verify the label was added
        logger.info("Verifying label was added")
        message = self.service.users().messages().get(
            userId='me', id=self.test_message_id).execute()
        self.assertIn(self.test_label['id'], message.get('labelIds', []),
                     "Label should be added to the message")
        logger.info("Label was successfully added")
        
        # Remove the label
        logger.info(f"Removing label {self.test_label_name} from message {self.test_message_id}")
        self.service.users().messages().modify(
            userId='me',
            id=self.test_message_id,
            body={'removeLabelIds': [self.test_label['id']]}
        ).execute()
        
        # Verify the label was removed
        logger.info("Verifying label was removed")
        message = self.service.users().messages().get(
            userId='me', id=self.test_message_id).execute()
        self.assertNotIn(self.test_label['id'], message.get('labelIds', []),
                        "Label should be removed from the message")
        logger.info("Label was successfully removed")
        
        logger.info("Label addition and removal test completed successfully")
    
    def test_mark_as_read_unread(self):
        """Test marking a Gmail message as read and unread"""
        logger.info("Testing marking messages as read/unread")
        
        # Skip if we don't have a test message
        if not self.test_message_id:
            logger.warning("No test message available, skipping test")
            self.skipTest("No test message available")
        
        # Mark as read (remove UNREAD label)
        logger.info(f"Marking message {self.test_message_id} as read")
        self.service.users().messages().modify(
            userId='me',
            id=self.test_message_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        
        # Verify it's marked as read
        logger.info("Verifying message is marked as read")
        message = self.service.users().messages().get(
            userId='me', id=self.test_message_id).execute()
        self.assertNotIn('UNREAD', message.get('labelIds', []),
                        "UNREAD label should be removed")
        logger.info("Message successfully marked as read")
        
        # Mark as unread (add UNREAD label)
        logger.info(f"Marking message {self.test_message_id} as unread")
        self.service.users().messages().modify(
            userId='me',
            id=self.test_message_id,
            body={'addLabelIds': ['UNREAD']}
        ).execute()
        
        # Verify it's marked as unread
        logger.info("Verifying message is marked as unread")
        message = self.service.users().messages().get(
            userId='me', id=self.test_message_id).execute()
        self.assertIn('UNREAD', message.get('labelIds', []),
                     "UNREAD label should be added")
        logger.info("Message successfully marked as unread")
        
        logger.info("Mark as read/unread test completed successfully")

if __name__ == '__main__':
    unittest.main()