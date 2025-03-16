# server.py
import sys
import traceback
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from mcp.server.fastmcp import FastMCP

from .auth import GmailClient
from .mcp.resources import GmailResources
from .mcp.tools import GmailTools
from .mcp.prompts import GmailPrompts

# Global variable for backward compatibility
mcp = None
gmail_service = None

@asynccontextmanager
async def gmail_lifespan(server: FastMCP) -> AsyncIterator[dict]:
    """Initialize Gmail API client and manage its lifecycle."""
    global gmail_service
    gmail_client = GmailClient()
    try:
        gmail_client.authenticate()
        gmail_service = gmail_client.service  # For backward compatibility
        
        # Register resources, tools, and prompts
        GmailResources(server, gmail_client)
        GmailTools(server, gmail_client)
        GmailPrompts(server)
        
        # Yield a context dictionary with the Gmail client
        yield {"gmail_client": gmail_client}
    finally:
        gmail_service = None
        gmail_client.close()

def create_server():
    """Create and configure the Gmail MCP server."""
    global mcp
    # Create the MCP server with Gmail lifespan
    mcp = FastMCP("Gmail Server", lifespan=gmail_lifespan)
    
    # Add custom error handler
    def custom_error_handler(error):
        print(f"MCP ERROR DETAILS: {type(error).__name__}: {str(error)}", file=sys.stderr)
        if hasattr(error, '__context__') and error.__context__:
            print(f"CAUSED BY: {type(error.__context__).__name__}: {str(error.__context__)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
    
    mcp.onerror = custom_error_handler
    
    return mcp

def main():
    """Main entry point for the Gmail MCP server."""
    # Configure detailed logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.StreamHandler(sys.stderr)
        ]
    )
    
    # Enable debug logging for MCP and anyio
    logging.getLogger('mcp').setLevel(logging.DEBUG)
    logging.getLogger('anyio').setLevel(logging.DEBUG)
    
    print("Starting Gmail MCP Server with enhanced logging...", file=sys.stderr)
    
    try:
        # Create and run the server
        server = create_server()
        
        # Register components directly
        # The gmail_client will be available in server.state after the lifespan context manager is entered
        # We'll modify the gmail_lifespan function to register components
        server.run()
    except Exception as e:
        print(f"Error in Gmail MCP Server: {str(e)}", file=sys.stderr)
        print(f"Error type: {type(e).__name__}", file=sys.stderr)
        if hasattr(e, '__context__') and e.__context__:
            print(f"Caused by: {type(e.__context__).__name__}: {str(e.__context__)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()