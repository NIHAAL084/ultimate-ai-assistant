# Sub-Agents Guide

This guide covers the specialized AI agents that integrate with external services through MCP (Model Context Protocol) servers.

## Available Sub-Agents

### Calendar Agent

**Purpose**: Google Calendar management and scheduling  
**MCP Server**: `@cocal/google-calendar-mcp`

**Key Capabilities**:

- Multi-calendar support (personal, work, shared calendars)
- Create, update, delete, and search calendar events
- Free/busy availability checking across calendars
- Smart scheduling with natural language understanding
- Recurring event management with advanced modifications
- Event import from images, PDFs, and web links
- Cross-calendar availability analysis
- Event color customization and organization

### Task Management Agent

**Purpose**: Todoist task and project management  
**MCP Server**: `@abhiz123/todoist-mcp-server`

**Key Capabilities**:

- Create tasks with natural language descriptions
- Set due dates using flexible formats (tomorrow, next week, specific dates)
- Assign priority levels (1-4) and add detailed descriptions
- Search and filter tasks by due date, priority, or project
- Update existing tasks using partial name matching
- Mark tasks as complete or delete them
- Natural language task management with smart search

## Setup Requirements

### Prerequisites

1. **Node.js and npm** installed for MCP servers
2. **API credentials** for the services you want to use
3. **User-specific environment** configuration

### MCP Server Installation

#### Calendar Agent

```bash
npm install -g @cocal/google-calendar-mcp
```

#### Task Management Agent

```bash
npm install -g @abhiz123/todoist-mcp-server
```

### Environment Configuration

See the [User Environment Guide](user-environment.md) for detailed setup instructions.

**Required Environment Variables**:

- `GOOGLE_OAUTH_CREDENTIALS`: Path to Google OAuth JSON file
- `TODOIST_API_TOKEN`: Your Todoist API token
- `GOOGLE_CALENDAR_MCP_TOKEN_PATH`: Custom token storage (optional)

## Usage Examples

### Calendar Agent

**Creating Events**:

- "Schedule a meeting with John tomorrow at 2 PM"
- "Block my calendar for vacation from June 1-7"
- "Create a recurring weekly team standup every Monday at 9 AM"

**Availability Checking**:

- "Am I free tomorrow afternoon?"
- "When is my next available 2-hour block this week?"
- "Show me my schedule for today"

**Event Management**:

- "Move my 3 PM meeting to 4 PM"
- "Cancel all meetings with 'project review' in the title"
- "Add John to the marketing meeting on Friday"

### Task Management Agent

**Creating Tasks**:

- "Add 'Buy groceries' to my todo list for tomorrow"
- "Create a high-priority task to finish the report by Friday"
- "Add a recurring task to review weekly metrics every Monday"

**Task Management**:

- "Mark 'finish presentation' as complete"
- "Show me all high-priority tasks due this week"
- "Update the grocery shopping task to include milk and bread"

**Organization**:

- "Move the marketing tasks to the Q2 project"
- "Set all overdue tasks to high priority"
- "Archive completed tasks from last month"

## Architecture

### Integration Method

Sub-agents are integrated into the main assistant using the **Agent-as-a-Tool** pattern:

1. **Tool Registration**: Each sub-agent is registered as a tool in the main assistant
2. **Dynamic Context**: Agents receive current time and user context
3. **MCP Communication**: External services accessed via MCP protocol
4. **User-Specific Config**: Each user can have their own API credentials

### Agent Lifecycle

1. **Initialization**: Agents created with current time context
2. **Tool Invocation**: Main assistant calls sub-agent tools based on user intent
3. **MCP Server Communication**: Sub-agents communicate with external services
4. **Response Integration**: Results are integrated back into the main conversation

## Troubleshooting

### Common Issues

**MCP Server Not Found**:

- Ensure Node.js packages are installed globally
- Check that MCP servers are in your PATH

**Authentication Errors**:

- Verify API tokens in user environment file
- For Google Calendar, ensure OAuth credentials are correctly configured
- Check token permissions and scopes

**Connection Issues**:

- Verify internet connectivity
- Check if external services (Google Calendar, Todoist) are accessible
- Review MCP server logs for detailed error messages

### Debug Commands

```bash
# Test MCP server installation
npx @cocal/google-calendar-mcp --version
npx @abhiz123/todoist-mcp-server --version

# Validate user environment
python manage_users.py validate

# Check agent imports
python -c "from app.assistant.sub_agents.calendar_agent.agent import create_calendar_agent; print('Calendar agent OK')"
```

## Extending Sub-Agents

### Adding New Sub-Agents

1. **Create Agent Directory**: Follow the pattern in `app/assistant/sub_agents/`
2. **Implement Agent Factory**: Create a function that returns an Agent instance
3. **Configure MCP Server**: Set up the external service integration
4. **Register as Tool**: Add to main assistant's tool collection
5. **Update Documentation**: Add agent details to this guide

### Best Practices

- **Environment Isolation**: Use user-specific environment variables
- **Error Handling**: Gracefully handle MCP server failures
- **Context Awareness**: Include current time in agent prompts
- **Clear Naming**: Use descriptive agent and tool names
- **Documentation**: Maintain clear capability descriptions
