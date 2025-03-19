# Gmail MCP Server

A Model Context Protocol (MCP) server that provides Gmail API integration for AI assistants and other MCP clients. This server enables AI systems to access and manage Gmail accounts through a standardized interface.

## Overview

The Gmail MCP Server exposes Gmail functionality through the Model Context Protocol, allowing AI assistants to:

- Read emails from your inbox
- Search for specific emails
- Send emails and create drafts
- Manage labels, threads, and message status
- Access full email content and metadata

## Prerequisites

- Python 3.6+
- Gmail API credentials (`credentials.json`)
- Required Python packages:
  - `google-auth`
  - `google-auth-oauthlib`
  - `google-api-python-client`
  - `mcp` (Model Context Protocol SDK)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/gmail-mcp.git
   cd gmail-mcp
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up Gmail API credentials:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Gmail API
   - Create OAuth 2.0 credentials (Desktop application type)
   - Download the credentials JSON file and save it as `credentials.json` in the project root directory

## Usage

### Running the MCP Server

To start the Gmail MCP server:

```bash
python -m gmail.server
```

or use the convenience script:

```bash
python gmail_server.py
```

The first time you run the server, it will open a browser window for authentication with your Google account. After successful authentication, a `token.json` file will be created to store your credentials for future use.

### Connecting to the Server

MCP clients can connect to the server through standard MCP protocols. The server exposes Gmail functionality through tools and resources that follow the MCP specification.

## MCP Tools

The Gmail MCP server provides the following tools:

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `get_labels_tool` | Get all Gmail labels and their IDs | None |
| `get_inbox_messages` | Get recent messages from the Gmail inbox | `max_results` (optional, default: 10) |
| `get_message_content_tool` | Get the full content of a specific email | `message_id` (required) |
| `send_email` | Send an email from your Gmail account | `to`, `subject`, `body` (all required) |
| `search_emails_tool` | Search for emails using Gmail search syntax | `query` (required), `max_results` (optional, default: 10) |
| `create_draft` | Create a draft email | `to`, `subject`, `body` (all required) |
| `add_label_to_message` | Add a label to a specific email message | `message_id`, `label_name` (both required) |
| `get_thread` | Get all messages in an email conversation thread | `thread_id` (required) |
| `mark_as_read` | Mark an email message as read | `message_id` (required) |
| `mark_as_unread` | Mark an email message as unread | `message_id` (required) |
| `archive_message` | Archive an email message | `message_id` (required) |
| `trash_message` | Move an email message to the Gmail trash | `message_id` (required) |

## MCP Resources

The server also provides the following resources:

| Resource URI | Description |
|--------------|-------------|
| `gmail://labels` | List of all Gmail labels |
| `gmail://inbox` | Recent messages from the inbox |
| `gmail://message/{message_id}` | Content of a specific email message |
| `gmail://search/{query}` | Results of a Gmail search query |

## Command Line Interface

In addition to the MCP server, this project includes a command-line interface for direct interaction with Gmail:

```bash
python gmail_cli.py [command] [options]
```

For detailed CLI usage instructions, see [gmail_cli_README.md](gmail_cli_README.md).

## Authentication and Security

The Gmail MCP server uses OAuth 2.0 for authentication with the Gmail API. The authentication flow:

1. On first run, the server initiates an OAuth flow that opens a browser window
2. The user logs in to their Google account and grants permission
3. Google provides an access token that is stored in `token.json`
4. Subsequent runs use the stored token, refreshing it when necessary

**Security Notes:**
- The `token.json` file contains sensitive authentication information and should be kept secure
- The server requests the following Gmail API scopes:
  - `https://www.googleapis.com/auth/gmail.readonly`
  - `https://www.googleapis.com/auth/gmail.send`
  - `https://www.googleapis.com/auth/gmail.compose`
  - `https://www.googleapis.com/auth/gmail.modify`
  - `https://www.googleapis.com/auth/gmail.labels`

## Examples

### Example 1: Using the MCP Server with an AI Assistant

When connected to an AI assistant through MCP, you can ask natural language questions like:

- "Show me my recent emails"
- "Search for emails from example@gmail.com"
- "Send an email to john@example.com with subject 'Meeting' and body 'Can we meet tomorrow?'"
- "What's in my latest email?"

The AI assistant will use the appropriate MCP tools to fulfill these requests.

### Example 2: Using the CLI to Search Emails

```bash
python gmail_cli.py search "from:example@gmail.com is:unread" --max 5
```

This will search for up to 5 unread emails from example@gmail.com.

## Testing

To run the test suite:

```bash
python run_tests.py
```

For more information about the tests, see [tests_README.md](tests_README.md).

## Project Structure

```
gmail-mcp/
├── gmail/                  # Main package
│   ├── __init__.py
│   ├── auth.py             # Authentication handling
│   ├── server.py           # MCP server implementation
│   ├── utils.py            # Utility functions
│   ├── api/                # Gmail API operations
│   │   ├── __init__.py
│   │   ├── drafts.py       # Draft email operations
│   │   ├── labels.py       # Label operations
│   │   ├── messages.py     # Message operations
│   │   └── threads.py      # Thread operations
│   └── mcp/                # MCP-specific implementations
│       ├── __init__.py
│       ├── prompts.py      # MCP prompts
│       ├── resources.py    # MCP resources
│       └── tools.py        # MCP tools
├── gmail_server.py         # Server entry point
├── gmail_cli.py            # Command-line interface
├── gmail_cli_README.md     # CLI documentation
├── tests_README.md         # Testing documentation
├── run_tests.py            # Test runner
├── test_gmail_mcp.py       # MCP tests
└── test_gmail_server.py    # Server tests
```

## Troubleshooting

### Authentication Issues

If you encounter authentication problems:
1. Delete the `token.json` file
2. Run the server again to trigger a new authentication flow
3. Ensure you have the correct permissions on your Google Cloud project

### API Quota Limits

The Gmail API has usage quotas. If you hit these limits:
1. Check your [Google Cloud Console](https://console.cloud.google.com/) for quota information
2. Consider implementing rate limiting in your application
3. Request higher quotas if needed for production use

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License:

```
MIT License

Copyright (c) 2025 Redazzo

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```