# __init__.py
from .auth import GmailClient, SCOPES
from .server import create_server, gmail_lifespan
from .utils import format_email_metadata, get_message_content, normalize_message_id

# For backward compatibility
from .server import mcp
gmail_service = None  # This will be set by the lifespan context manager

# Re-export all resources, tools, and prompts
from .mcp.resources import GmailResources
from .mcp.tools import GmailTools
from .mcp.prompts import GmailPrompts