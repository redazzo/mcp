# auth.py
import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build

# Define the Gmail API scopes needed
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.labels'
]

class GmailClient:
    """Client for interacting with the Gmail API.
    
    This class handles authentication and provides access to the Gmail service.
    It can be used as a context manager to ensure proper cleanup.
    """
    
    def __init__(self):
        """Initialize the Gmail client."""
        self.service = None
    
    def authenticate(self):
        """Authenticate with the Gmail API and create a service instance."""
        creds = self.get_credentials()
        self.service = build('gmail', 'v1', credentials=creds)
        return self.service
    
    def _safe_refresh_token(self, creds, token_path, credentials_path):
        """Safely refresh the token, handling expired or revoked tokens.
        
        If token refresh fails, removes the token file and initiates a new OAuth flow.
        
        Args:
            creds: The credentials to refresh
            token_path: Path to the token.json file
            credentials_path: Path to the credentials.json file
            
        Returns:
            Refreshed or new credentials
        """
        try:
            creds.refresh(Request())
            return creds
        except RefreshError as e:
            print(f"Token refresh failed: {e}. Removing token and starting new auth flow.")
            # Delete the invalid token file
            if os.path.exists(token_path):
                os.remove(token_path)
            # Proceed with new OAuth flow
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            return flow.run_local_server(port=0)
    
    def get_credentials(self):
        """Get valid user credentials from storage or initiate OAuth2 flow.

        This function handles Gmail authentication by:
        1. Checking for existing credentials in token.json
        2. Refreshing expired credentials if possible
        3. Initiating a new OAuth2 flow if needed
        4. Saving valid credentials for future use

        Returns:
            Google OAuth2 credentials object for Gmail API access
        """
        creds = None
        script_dir = os.path.dirname(os.path.abspath(__file__))
        token_path = os.path.join(script_dir, '..', 'token.json')
        credentials_path = os.path.join(script_dir, '..', 'credentials.json')

        # Check if token.json exists (stored credentials)
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_info(
                json.loads(open(token_path).read()), SCOPES)

        # If no credentials or they're invalid, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds = self._safe_refresh_token(creds, token_path, credentials_path)
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open(token_path, 'w') as token:
                token.write(creds.to_json())

        return creds
    
    def close(self):
        """Close the Gmail service."""
        self.service = None
    
    def __enter__(self):
        """Enter the context manager."""
        self.authenticate()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        self.close()