# Gmail Command Line Interface

A simple Python script that allows you to interact with Gmail server functions via the command line.

## Prerequisites

- Python 3.6+
- Gmail API credentials (`credentials.json` and `token.json`)
- Required Python packages (from the `gmail_server.py` implementation)

## Usage

```bash
python gmail_cli.py [command] [options]
```

## Available Commands

### List Labels

List all Gmail labels:

```bash
python gmail_cli.py labels
```

### View Inbox

View recent messages from your inbox:

```bash
python gmail_cli.py inbox [--max NUMBER]
```

Options:
- `--max NUMBER`: Maximum number of messages to retrieve (default: 10)

### Get Message

Get a specific message by ID:

```bash
python gmail_cli.py message MESSAGE_ID
```

### Search Emails

Search for emails using Gmail search syntax:

```bash
python gmail_cli.py search "QUERY" [--max NUMBER]
```

Options:
- `--max NUMBER`: Maximum number of results to return (default: 10)

Examples of search queries:
- `from:example@gmail.com`: Emails from a specific sender
- `subject:meeting`: Emails with "meeting" in the subject
- `is:unread`: Unread emails
- `after:2025/03/01`: Emails after March 1, 2025

### Send Email

Send an email:

```bash
python gmail_cli.py send --to RECIPIENT --subject "SUBJECT" --body "BODY"
```

### Create Draft

Create a draft email:

```bash
python gmail_cli.py draft --to RECIPIENT --subject "SUBJECT" --body "BODY"
```

### Add Label to Message

Add a label to a specific message:

```bash
python gmail_cli.py add-label MESSAGE_ID LABEL_NAME
```

If the label doesn't exist, it will be created automatically.

### Get Thread

Get all messages in a thread:

```bash
python gmail_cli.py thread THREAD_ID
```

### Mark as Read/Unread

Mark a message as read:

```bash
python gmail_cli.py mark-read MESSAGE_ID
```

Mark a message as unread:

```bash
python gmail_cli.py mark-unread MESSAGE_ID
```

### Archive Message

Archive a message (remove from inbox):

```bash
python gmail_cli.py archive MESSAGE_ID
```

### Trash Message

Move a message to trash:

```bash
python gmail_cli.py trash MESSAGE_ID
```

## Examples

1. List the 5 most recent inbox messages:
   ```bash
   python gmail_cli.py inbox --max 5
   ```

2. Search for unread emails from a specific sender:
   ```bash
   python gmail_cli.py search "from:example@gmail.com is:unread" --max 10
   ```

3. Send a simple email:
   ```bash
   python gmail_cli.py send --to "recipient@example.com" --subject "Hello" --body "This is a test email."
   ```

4. Get a specific message and then add a label to it:
   ```bash
   python gmail_cli.py message MESSAGE_ID
   python gmail_cli.py add-label MESSAGE_ID "Important"
   ```

## Notes

- The script uses the Gmail API and requires proper authentication.
- The first time you run the script, it may open a browser window for authentication.
- Message IDs and Thread IDs can be obtained from the inbox or search commands.