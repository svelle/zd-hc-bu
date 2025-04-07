# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment Setup
- Python script requiring environment variables (`ZENDESK_API_TOKEN`)
- Use virtual environment: `python -m venv venv && source venv/bin/activate`
- Install dependencies: `pip install requests`

## Code Style Guidelines
- Follow PEP 8 conventions
- Imports: standard library first, then third-party packages
- Use meaningful variable names and snake_case
- Include docstrings for functions
- Error handling: use try/except blocks with specific error types
- Add descriptive print statements for debugging and status updates

## Error Handling
- Always catch exceptions when making API requests
- Provide detailed error messages with status codes and response text
- Use fallback values when appropriate

## API Usage
- Authenticate with HTTPBasicAuth using token-based authentication
- Respect API pagination for listing resources
- Handle 404 responses with fallback creation logic