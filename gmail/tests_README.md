# Gmail MCP Server Tests

This directory contains tests for the Gmail MCP Server. The tests are designed to verify the functionality of the server and its components.

## Test Files

- `test_gmail_server.py`: Tests the basic functionality and helper functions of the Gmail server.
- `test_gmail_mcp.py`: Tests the MCP-specific functionality, including resources and tools.
- `run_tests.py`: A test runner script that runs both test files and provides a summary of the results.

## Running the Tests

You can run the tests using the `run_tests.py` script:

```bash
python run_tests.py
```

This will run all the tests and provide a summary of the results.

Alternatively, you can run individual test files:

```bash
python -m unittest test_gmail_server.py
python -m unittest test_gmail_mcp.py
```

## Important Notes

1. **Real Gmail Account**: These tests use your actual Gmail account through the credentials in `token.json` and `credentials.json`. Be careful when running tests that modify your Gmail data.

2. **Skipped Tests**: Some tests that could potentially modify your Gmail data (like sending emails or trashing messages) are skipped by default. You can enable these tests by removing the `self.skipTest()` lines in the test methods.

3. **Test Data**: The tests create temporary test data (labels, drafts, messages) and clean up after themselves. However, if a test fails or is interrupted, some test data might remain in your Gmail account.

## Test Coverage

The tests cover the following functionality:

### Basic Functionality (test_gmail_server.py)
- Getting credentials
- Formatting email metadata
- Getting message content
- Getting labels
- Getting inbox messages
- Searching emails
- Adding and removing labels
- Marking messages as read/unread

### MCP Functionality (test_gmail_mcp.py)
- MCP Resources:
  - gmail://labels
  - gmail://inbox
  - gmail://message/{message_id}
  - gmail://search/{query}
- MCP Tools:
  - send_email
  - search_emails_tool
  - create_draft
  - add_label_to_message
  - get_thread
  - mark_as_read
  - mark_as_unread
  - archive_message
  - trash_message

## Customizing Tests

You can customize the tests by modifying the test files. For example, you can:

- Enable skipped tests by removing the `self.skipTest()` lines
- Add more test cases for specific functionality
- Modify the test data creation and cleanup

## Troubleshooting

If you encounter issues with the tests:

1. Check that your `credentials.json` and `token.json` files are valid and have the necessary permissions.
2. Make sure the Gmail API is enabled for your Google Cloud project.
3. Check the error messages in the test output for specific issues.
4. If tests are failing due to rate limiting, wait a few minutes and try again.