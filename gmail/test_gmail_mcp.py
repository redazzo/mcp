import unittest
import os
import json
import time
import sys
import asyncio
import logging
from contextlib import contextmanager
from io import StringIO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('TestGmailMCP')

# User confirmation helper
def confirm_gmail_write(operation_description):
    """
    Ask for user confirmation before executing a Gmail write operation.
    
    Args:
        operation_description: Description of the operation about to be performed
        
    Returns:
        bool: True if user confirms, False if rejected
    """
    print("\n" + "="*80)
    print(f"GMAIL WRITE OPERATION: {operation_description}")
    print("="*80)
    
    response = input("Allow this operation? (y/n): ").strip().lower()
    
    if response == 'y' or response == 'yes':
        print("Operation ALLOWED. Proceeding...\n")
        return True
    else:
        print("Operation REJECTED. Skipping...\n")
        return False

# Import the modules from our new structure
from gmail.auth import GmailClient
from gmail.server import create_server, gmail_lifespan
from gmail.mcp.resources import GmailResources
from gmail.mcp.tools import GmailTools

# Import Google API libraries
from googleapiclient.discovery import build

class TestGmailMCP(unittest.TestCase):
    """Tests for the Gmail MCP Server functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up the Gmail service for all tests"""
        logger.info("Setting up TestGmailMCP test suite")
        
        # Get credentials and build the service
        logger.info("Getting Gmail API credentials")
        cls.client = GmailClient()
        cls.creds = cls.client.get_credentials()
        logger.info("Building Gmail service")
        cls.service = build('gmail', 'v1', credentials=cls.creds)
        
        # Create the MCP server
        logger.info("Creating MCP server")
        cls.mcp = create_server()
        
        # Create a unique identifier for test resources
        cls.test_id = f"test_{int(time.time())}"
        logger.info(f"Created unique test ID: {cls.test_id}")
        
        # Create a test label for testing
        cls.test_label_name = f"TestLabel_{cls.test_id}"
        logger.info(f"Creating test label: {cls.test_label_name}")
        
        if confirm_gmail_write(f"Create test label '{cls.test_label_name}' for testing"):
            try:
                cls.test_label = cls.service.users().labels().create(
                    userId='me',
                    body={'name': cls.test_label_name}
                ).execute()
                logger.info(f"Created test label with ID: {cls.test_label['id']}")
            except Exception as e:
                logger.warning(f"Could not create test label: {str(e)}")
                cls.test_label = None
        else:
            logger.warning("Test label creation was rejected by user")
            cls.test_label = None
        
        # Create a test draft for testing
        logger.info("Creating test draft email")
        test_email_content = f"This is a test email for MCP testing {cls.test_id}"
        message = {
            'raw': 'RnJvbTogdGVzdEBleGFtcGxlLmNvbQpUbzogdGVzdEBleGFtcGxlLmNvbQpTdWJqZWN0OiBUZXN0IEVtYWlsIGZvciBHbWFpbCBNQ1AgU2VydmVyIFRlc3RzCgpUaGlzIGlzIGEgdGVzdCBlbWFpbCBmb3IgdGVzdGluZyB0aGUgR21haWwgTUNQIFNlcnZlci4='
        }
        
        if confirm_gmail_write("Create a test draft email for testing"):
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
        else:
            logger.warning("Test draft creation was rejected by user")
            cls.test_draft = None
            cls.test_message_id = None
            
        # Create a thread with multiple messages for testing
        if cls.test_message_id:  # Only proceed if we have a test message
            logger.info("Creating test thread")
            # First, get your own email address
            user_email = cls.service.users().getProfile(userId='me').execute()['emailAddress']
            logger.info(f"User email: {user_email}")
            
            # Create a message in a new thread
            thread_message = {
                'raw': f'RnJvbToge3VzZXJfZW1haWx9ClRvOiB7dXNlcl9lbWFpbH0KU3ViamVjdDogVGVzdCBUaHJlYWQgZm9yIEdtYWlsIE1DUCBTZXJ2ZXIgVGVzdHMKCk1lc3NhZ2UgMSBpbiB0ZXN0IHRocmVhZCB7Y2xzLnRlc3RfaWR9Lg=='.replace('{user_email}', user_email).replace('{cls.test_id}', cls.test_id)
            }
            
            # Send the message
            logger.info("Sending test message to create thread")
            
            if confirm_gmail_write(f"Send a test message to {user_email} to create a thread for testing"):
                try:
                    sent_message = cls.service.users().messages().send(
                        userId='me',
                        body={'raw': thread_message}
                    ).execute()
                    
                    cls.test_thread_id = sent_message['threadId']
                    cls.test_thread_message_id = sent_message['id']
                    logger.info(f"Created test thread with ID: {cls.test_thread_id}")
                    logger.info(f"Created test thread message with ID: {cls.test_thread_message_id}")
                except Exception as e:
                    logger.warning(f"Could not create test thread: {str(e)}")
                    cls.test_thread_id = None
                    cls.test_thread_message_id = None
            else:
                logger.warning("Test thread creation was rejected by user")
                cls.test_thread_id = None
                cls.test_thread_message_id = None
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        logger.info("Cleaning up TestGmailMCP test suite")
        
        # Delete the test label if it was created
        if cls.test_label:
            logger.info(f"Deleting test label: {cls.test_label_name}")
            
            if confirm_gmail_write(f"Delete test label '{cls.test_label_name}'"):
                try:
                    cls.service.users().labels().delete(
                        userId='me',
                        id=cls.test_label['id']
                    ).execute()
                    logger.info("Test label deleted successfully")
                except Exception as e:
                    logger.warning(f"Could not delete test label: {str(e)}")
            else:
                logger.warning("Test label deletion was rejected by user")
        
        # Delete the test draft if it was created
        if cls.test_draft:
            logger.info(f"Deleting test draft")
            
            if confirm_gmail_write(f"Delete test draft with ID: {cls.test_draft['id']}"):
                try:
                    cls.service.users().drafts().delete(
                        userId='me',
                        id=cls.test_draft['id']
                    ).execute()
                    logger.info("Test draft deleted successfully")
                except Exception as e:
                    logger.warning(f"Could not delete test draft: {str(e)}")
            else:
                logger.warning("Test draft deletion was rejected by user")
        
        # Move test messages to trash
        if hasattr(cls, 'test_thread_message_id') and cls.test_thread_message_id:
            logger.info(f"Moving test thread message to trash: {cls.test_thread_message_id}")
            
            if confirm_gmail_write(f"Move test message with ID: {cls.test_thread_message_id} to trash"):
                try:
                    cls.service.users().messages().trash(
                        userId='me',
                        id=cls.test_thread_message_id
                    ).execute()
                    logger.info("Test thread message moved to trash successfully")
                except Exception as e:
                    logger.warning(f"Could not trash test message: {str(e)}")
            else:
                logger.warning("Test message trash operation was rejected by user")
        
        logger.info("TestGmailMCP cleanup completed")
    
    @contextmanager
    def capture_stdout(self):
        """Capture stdout for testing"""
        logger.info("Capturing stdout for testing")
        new_out = StringIO()
        old_out = sys.stdout
        try:
            sys.stdout = new_out
            yield new_out
        finally:
            sys.stdout = old_out
            logger.info("Restored original stdout")
    
    def test_mcp_resource_labels(self):
        """Test the gmail://labels resource to verify it returns all Gmail labels"""
        logger.info("Testing MCP resource: gmail://labels")
        
        # Initialize the Gmail service
        logger.info("Initializing Gmail service for test")
        client = GmailClient()
        client.service = self.service
        
        # Create resources
        logger.info("Creating GmailResources")
        resources = GmailResources(self.__class__.mcp, client)
        
        # Call the resource handler directly
        logger.info("Calling get_labels resource handler")
        result = resources.get_labels()
        
        # Log the result (truncated)
        result_preview = result[:200] + "..." if len(result) > 200 else result
        logger.info(f"Resource result preview: {result_preview}")
        
        # Check that the result contains our test label
        self.assertIsInstance(result, str, "Result should be a string")
        if self.test_label:
            logger.info(f"Checking if test label {self.test_label_name} is in the result")
            self.assertIn(self.test_label_name, result, "Test label should be in the result")
            logger.info("Test label found in the result")
        
        logger.info("MCP resource labels test completed successfully")
    
    def test_mcp_resource_inbox(self):
        """Test the gmail://inbox resource to verify it returns inbox messages"""
        logger.info("Testing MCP resource: gmail://inbox")
        
        # Initialize the Gmail service
        logger.info("Initializing Gmail service for test")
        client = GmailClient()
        client.service = self.service
        
        # Create resources
        logger.info("Creating GmailResources")
        resources = GmailResources(self.__class__.mcp, client)
        
        # Call the resource handler directly
        logger.info("Calling get_inbox resource handler")
        result = resources.get_inbox()
        
        # Log the result (truncated)
        result_preview = result[:200] + "..." if len(result) > 200 else result
        logger.info(f"Resource result preview: {result_preview}")
        
        # Check that the result is a string
        self.assertIsInstance(result, str, "Result should be a string")
        
        # The inbox might be empty, so we just check that the function returns
        # either "No messages found in inbox." or a non-empty string
        self.assertTrue(
            result == "No messages found in inbox." or len(result) > 0,
            "Result should either indicate no messages or contain message data"
        )
        
        logger.info("MCP resource inbox test completed successfully")
    
    def test_mcp_resource_message(self):
        """Test the gmail://message/{message_id} resource to verify it returns a specific message"""
        logger.info("Testing MCP resource: gmail://message/{message_id}")
        
        # Skip if we don't have a test message
        if not self.test_message_id:
            logger.warning("No test message available, skipping test")
            self.skipTest("No test message available")
        
        # Initialize the Gmail service
        logger.info("Initializing Gmail service for test")
        client = GmailClient()
        client.service = self.service
        
        # Create resources
        logger.info("Creating GmailResources")
        resources = GmailResources(self.__class__.mcp, client)
        
        # Call the resource handler directly
        logger.info(f"Calling get_message resource handler with ID: {self.test_message_id}")
        result = resources.get_message(self.test_message_id)
        
        # Log the result (truncated)
        result_preview = result[:200] + "..." if len(result) > 200 else result
        logger.info(f"Resource result preview: {result_preview}")
        
        # Check that the result is a string
        self.assertIsInstance(result, str, "Result should be a string")
        
        # Check that the result contains basic email fields
        logger.info("Checking for required email fields in the result")
        self.assertIn("From:", result, "Result should contain From field")
        self.assertIn("Subject:", result, "Result should contain Subject field")
        self.assertIn("Date:", result, "Result should contain Date field")
        
        logger.info("MCP resource message test completed successfully")
    
    def test_mcp_resource_search(self):
        """Test the gmail://search/{query} resource to verify it returns search results"""
        logger.info("Testing MCP resource: gmail://search/{query}")
        
        # Initialize the Gmail service
        logger.info("Initializing Gmail service for test")
        client = GmailClient()
        client.service = self.service
        
        # Create resources
        logger.info("Creating GmailResources")
        resources = GmailResources(self.__class__.mcp, client)
        
        # Call the resource handler directly with a query that should match our test message
        search_query = "subject:Test"
        logger.info(f"Calling search_emails resource handler with query: {search_query}")
        result = resources.search_emails(search_query)
        
        # Log the result (truncated)
        result_preview = result[:200] + "..." if len(result) > 200 else result
        logger.info(f"Resource result preview: {result_preview}")
        
        # Check that the result is a string
        self.assertIsInstance(result, str, "Result should be a string")
        
        logger.info("MCP resource search test completed successfully")
    
    def test_mcp_tool_send_email(self):
        """Test the send_email MCP tool to verify it can send emails"""
        logger.info("Testing MCP tool: send_email")
        
        # Skip this test in normal runs to avoid sending actual emails
        logger.warning("Skipping send_email test to avoid sending actual emails")
        self.skipTest("Skipping send_email test to avoid sending actual emails")
        
        # Initialize the Gmail service
        logger.info("Initializing Gmail service for test")
        client = GmailClient()
        client.service = self.service
        
        # Create tools
        logger.info("Creating GmailTools")
        tools = GmailTools(self.__class__.mcp, client)
        
        # Get the user's email address
        logger.info("Getting user's email address")
        user_email = self.service.users().getProfile(userId='me').execute()['emailAddress']
        logger.info(f"User email: {user_email}")
        
        # Call the tool handler directly
        logger.info("Calling send_email tool handler")
        subject = f"Test Email from MCP Test {self.test_id}"
        body = "This is a test email sent by the Gmail MCP Server test suite."
        logger.info(f"Email details - To: {user_email}, Subject: {subject}")
        
        if confirm_gmail_write(f"Send test email to {user_email} with subject '{subject}'"):
            result = tools.send_email(
                to=user_email,
                subject=subject,
                body=body
            )
            
            # Log the result
            logger.info(f"Tool result: {result}")
            
            # Check that the result indicates success
            self.assertIn("Email sent successfully", result, "Result should indicate success")
            self.assertIn(user_email, result, "Result should contain recipient email")
        else:
            logger.warning("Test email sending was rejected by user")
            self.skipTest("Email sending rejected by user")
            return
        
        logger.info("MCP tool send_email test completed successfully")
    
    def test_mcp_tool_search_emails(self):
        """Test the search_emails_tool MCP tool to verify it can search emails"""
        logger.info("Testing MCP tool: search_emails_tool")
        
        # Initialize the Gmail service
        logger.info("Initializing Gmail service for test")
        client = GmailClient()
        client.service = self.service
        
        # Create tools
        logger.info("Creating GmailTools")
        tools = GmailTools(self.__class__.mcp, client)
        
        # Call the tool handler directly
        search_query = "subject:Test"
        max_results = 5
        logger.info(f"Calling search_emails_tool with query: {search_query}, max_results: {max_results}")
        
        result = tools.search_emails_tool(
            query=search_query,
            max_results=max_results
        )
        
        # Log the result (truncated)
        result_preview = result[:200] + "..." if len(result) > 200 else result
        logger.info(f"Tool result preview: {result_preview}")
        
        # Check that the result is a string
        self.assertIsInstance(result, str, "Result should be a string")
        
        logger.info("MCP tool search_emails_tool test completed successfully")
    
    def test_mcp_tool_create_draft(self):
        """Test the create_draft MCP tool to verify it can create email drafts"""
        logger.info("Testing MCP tool: create_draft")
        
        # Initialize the Gmail service
        logger.info("Initializing Gmail service for test")
        client = GmailClient()
        client.service = self.service
        
        # Create tools
        logger.info("Creating GmailTools")
        tools = GmailTools(self.__class__.mcp, client)
        
        # Get the user's email address
        logger.info("Getting user's email address")
        user_email = self.service.users().getProfile(userId='me').execute()['emailAddress']
        logger.info(f"User email: {user_email}")
        
        # Call the tool handler directly
        logger.info("Calling create_draft tool handler")
        subject = f"Test Draft from MCP Test {self.test_id}"
        body = "This is a test draft created by the Gmail MCP Server test suite."
        logger.info(f"Draft details - To: {user_email}, Subject: {subject}")
        
        if confirm_gmail_write(f"Create test draft email to {user_email} with subject '{subject}'"):
            result = tools.create_draft(
                to=user_email,
                subject=subject,
                body=body
            )
            
            # Log the result
            logger.info(f"Tool result: {result}")
            
            # Check that the result indicates success
            self.assertIn("Draft created successfully", result, "Result should indicate success")
            
            # Extract the draft ID from the result
            draft_id = result.split("Draft ID: ")[1]
            logger.info(f"Created draft ID: {draft_id}")
            
            # Clean up by deleting the draft
            logger.info(f"Cleaning up by deleting draft: {draft_id}")
            
            if confirm_gmail_write(f"Delete test draft with ID: {draft_id}"):
                try:
                    self.service.users().drafts().delete(
                        userId='me',
                        id=draft_id
                    ).execute()
                    logger.info("Draft deleted successfully")
                except Exception as e:
                    logger.warning(f"Could not delete test draft: {str(e)}")
            else:
                logger.warning("Test draft deletion was rejected by user")
        else:
            logger.warning("Test draft creation was rejected by user")
            self.skipTest("Draft creation rejected by user")
        
        logger.info("MCP tool create_draft test completed successfully")
    
    def test_mcp_tool_add_label(self):
        """Test the add_label_to_message MCP tool to verify it can add labels to messages"""
        logger.info("Testing MCP tool: add_label_to_message")
        
        # Skip if we don't have a test message
        if not self.test_message_id:
            logger.warning("No test message available, skipping test")
            self.skipTest("No test message available")
        
        # Initialize the Gmail service
        logger.info("Initializing Gmail service for test")
        client = GmailClient()
        client.service = self.service
        
        # Create tools
        logger.info("Creating GmailTools")
        tools = GmailTools(self.__class__.mcp, client)
        
        # Call the tool handler directly
        logger.info(f"Calling add_label_to_message with message ID: {self.test_message_id}, label: {self.test_label_name}")
        
        if confirm_gmail_write(f"Add label '{self.test_label_name}' to message with ID: {self.test_message_id}"):
            result = tools.add_label_to_message(
                message_id=self.test_message_id,
                label_name=self.test_label_name
            )
            
            # Log the result
            logger.info(f"Tool result: {result}")
            
            # Check that the result indicates success
            self.assertIn(f"Label '{self.test_label_name}' added to message", result,
                         "Result should indicate label was added")
            
            # Verify the label was added
            logger.info("Verifying label was added to the message")
            message = self.service.users().messages().get(
                userId='me', id=self.test_message_id).execute()
            self.assertIn(self.test_label['id'], message.get('labelIds', []),
                         "Label should be added to the message")
        else:
            logger.warning("Adding label to message was rejected by user")
            self.skipTest("Adding label to message rejected by user")
            return
        
        logger.info("MCP tool add_label_to_message test completed successfully")
    
    def test_mcp_tool_get_thread(self):
        """Test the get_thread MCP tool to verify it can retrieve email threads"""
        logger.info("Testing MCP tool: get_thread")
        
        # Skip if we don't have a test thread
        if not self.test_thread_id:
            logger.warning("No test thread available, skipping test")
            self.skipTest("No test thread available")
        
        # Initialize the Gmail service
        logger.info("Initializing Gmail service for test")
        client = GmailClient()
        client.service = self.service
        
        # Create tools
        logger.info("Creating GmailTools")
        tools = GmailTools(self.__class__.mcp, client)
        
        # Call the tool handler directly
        logger.info(f"Calling get_thread with thread ID: {self.test_thread_id}")
        result = tools.get_thread(self.test_thread_id)
        
        # Log the result (truncated)
        result_preview = result[:200] + "..." if len(result) > 200 else result
        logger.info(f"Tool result preview: {result_preview}")
        
        # Check that the result is a string
        self.assertIsInstance(result, str, "Result should be a string")
        
        # Check that the result contains the thread ID
        self.assertIn(f"Thread {self.test_thread_id}", result,
                     "Result should contain the thread ID")
        
        logger.info("MCP tool get_thread test completed successfully")
    
    def test_mcp_tool_mark_as_read_unread(self):
        """Test the mark_as_read and mark_as_unread MCP tools to verify they can change message read status"""
        logger.info("Testing MCP tools: mark_as_read and mark_as_unread")
        
        # Skip if we don't have a test message
        if not self.test_message_id:
            logger.warning("No test message available, skipping test")
            self.skipTest("No test message available")
        
        # Initialize the Gmail service
        logger.info("Initializing Gmail service for test")
        client = GmailClient()
        client.service = self.service
        
        # Create tools
        logger.info("Creating GmailTools")
        tools = GmailTools(self.__class__.mcp, client)
        
        # Call the mark_as_read tool handler directly
        logger.info(f"Calling mark_as_read with message ID: {self.test_message_id}")
        
        if confirm_gmail_write(f"Mark message with ID: {self.test_message_id} as read"):
            result_read = tools.mark_as_read(self.test_message_id)
            
            # Log the result
            logger.info(f"mark_as_read result: {result_read}")
            
            # Check that the result indicates success
            self.assertIn(f"Message {self.test_message_id} marked as read", result_read,
                         "Result should indicate message was marked as read")
            
            # Verify it's marked as read
            logger.info("Verifying message is marked as read")
            message = self.service.users().messages().get(
                userId='me', id=self.test_message_id).execute()
            self.assertNotIn('UNREAD', message.get('labelIds', []),
                            "UNREAD label should be removed")
            
            # Call the mark_as_unread tool handler directly
            logger.info(f"Calling mark_as_unread with message ID: {self.test_message_id}")
            
            if confirm_gmail_write(f"Mark message with ID: {self.test_message_id} as unread"):
                result_unread = tools.mark_as_unread(self.test_message_id)
                
                # Log the result
                logger.info(f"mark_as_unread result: {result_unread}")
                
                # Check that the result indicates success
                self.assertIn(f"Message {self.test_message_id} marked as unread", result_unread,
                             "Result should indicate message was marked as unread")
                
                # Verify it's marked as unread
                logger.info("Verifying message is marked as unread")
                message = self.service.users().messages().get(
                    userId='me', id=self.test_message_id).execute()
                self.assertIn('UNREAD', message.get('labelIds', []),
                             "UNREAD label should be added")
            else:
                logger.warning("Marking message as unread was rejected by user")
                self.skipTest("Marking message as unread rejected by user")
        else:
            logger.warning("Marking message as read was rejected by user")
            self.skipTest("Marking message as read rejected by user")
        
        logger.info("MCP tools mark_as_read and mark_as_unread tests completed successfully")
    
    def test_mcp_tool_archive_message(self):
        """Test the archive_message MCP tool to verify it can archive messages"""
        logger.info("Testing MCP tool: archive_message")
        
        # Skip if we don't have a test thread message
        if not self.test_thread_message_id:
            logger.warning("No test thread message available, skipping test")
            self.skipTest("No test thread message available")
        
        # Initialize the Gmail service
        logger.info("Initializing Gmail service for test")
        client = GmailClient()
        client.service = self.service
        
        # Create tools
        logger.info("Creating GmailTools")
        tools = GmailTools(self.__class__.mcp, client)
        
        # First, make sure the message has the INBOX label
        logger.info(f"Ensuring message {self.test_thread_message_id} has INBOX label")
        
        if confirm_gmail_write(f"Add INBOX label to message with ID: {self.test_thread_message_id}"):
            self.service.users().messages().modify(
                userId='me',
                id=self.test_thread_message_id,
                body={'addLabelIds': ['INBOX']}
            ).execute()
            
            # Verify it has the INBOX label
            message = self.service.users().messages().get(
                userId='me', id=self.test_thread_message_id).execute()
            if 'INBOX' in message.get('labelIds', []):
                logger.info("Message has INBOX label")
            else:
                logger.warning("Could not add INBOX label to message")
                self.skipTest("Could not add INBOX label to message")
                return
                
            # Call the archive_message tool handler directly
            logger.info(f"Calling archive_message with message ID: {self.test_thread_message_id}")
            
            if confirm_gmail_write(f"Archive message with ID: {self.test_thread_message_id}"):
                result = tools.archive_message(self.test_thread_message_id)
                
                # Log the result
                logger.info(f"Tool result: {result}")
                
                # Check that the result indicates success
                self.assertIn(f"Message {self.test_thread_message_id} archived", result,
                             "Result should indicate message was archived")
                
                # Verify the message is archived (no INBOX label)
                logger.info("Verifying message is archived (no INBOX label)")
                message = self.service.users().messages().get(
                    userId='me', id=self.test_thread_message_id).execute()
                self.assertNotIn('INBOX', message.get('labelIds', []),
                                "INBOX label should be removed")
            else:
                logger.warning("Archiving message was rejected by user")
                self.skipTest("Archiving message rejected by user")
        else:
            logger.warning("Adding INBOX label to message was rejected by user")
            self.skipTest("Adding INBOX label rejected by user")
        
        logger.info("MCP tool archive_message test completed successfully")
    
    def test_mcp_tool_trash_message(self):
        """Test the trash_message MCP tool to verify it can move messages to trash"""
        logger.info("Testing MCP tool: trash_message")
        
        # Skip this test to avoid trashing the test message we need for other tests
        logger.warning("Skipping trash_message test to preserve test messages")
        self.skipTest("Skipping trash_message test to preserve test messages")
        
        # Initialize the Gmail service
        logger.info("Initializing Gmail service for test")
        client = GmailClient()
        client.service = self.service
        
        # Create tools
        logger.info("Creating GmailTools")
        tools = GmailTools(self.__class__.mcp, client)
        
        # Call the trash_message tool handler directly
        logger.info(f"Calling trash_message with message ID: {self.test_thread_message_id}")
        
        if confirm_gmail_write(f"Move message with ID: {self.test_thread_message_id} to trash"):
            result = tools.trash_message(self.test_thread_message_id)
            
            # Log the result
            logger.info(f"Tool result: {result}")
            
            # Check that the result indicates success
            self.assertIn(f"Message {self.test_thread_message_id} moved to trash", result,
                         "Result should indicate message was moved to trash")
            
            # Verify the message is in trash
            logger.info("Verifying message is in trash")
            message = self.service.users().messages().get(
                userId='me', id=self.test_thread_message_id).execute()
            self.assertIn('TRASH', message.get('labelIds', []),
                         "TRASH label should be added")
        else:
            logger.warning("Moving message to trash was rejected by user")
            self.skipTest("Moving message to trash rejected by user")
        
        logger.info("MCP tool trash_message test completed successfully")

if __name__ == '__main__':
    unittest.main()