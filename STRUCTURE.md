# Application Structure

This document explains the modular structure of the Hellas Direct chatbot application after refactoring from a single large `app.py` file.

## File Structure

```
├── app.py                    # Main application entry point
├── config.py                 # Configuration and Flask app setup
├── schemas.py                # Pydantic schemas for data validation
├── agents.py                 # AI agents and system prompt setup
├── routes.py                 # Flask route handlers
├── utils.py                  # Helper functions and session management
├── test_decision_agent.py    # Test script for AC/RA decision agent
├── database.py               # Database operations (existing)
├── templates/                # HTML templates (existing)
├── static/                   # Static files (existing)
└── uploads/                  # File upload directory (existing)
```

## Module Descriptions

### `app.py` (Main Entry Point)
- **Purpose**: Application entry point that ties everything together
- **Contents**: 
  - Creates Flask app using `config.create_app()`
  - Registers routes using `routes.register_routes()`
  - Application runner (`if __name__ == "__main__"`)
- **Size**: ~10 lines (down from 673 lines)

### `config.py` (Configuration)
- **Purpose**: Handles Flask app configuration and API key management
- **Contents**:
  - `create_app()`: Creates and configures Flask application
  - `get_api_key()`: Retrieves OpenAI API key from environment or default
  - App configuration (secret key, upload settings, etc.)

### `schemas.py` (Data Models)
- **Purpose**: Contains all Pydantic schemas for data validation
- **Contents**:
  - `CustomOutputSchema`: Main chat agent response schema
  - `VehicleImageAnalysis`: Image analysis results
  - `ImageAnalysisInput/Output`: Image processing schemas
  - `CaseDecisionInputSchema/OutputSchema`: AC/RA decision agent schemas
- **Dependencies**: Pydantic, instructor, atomic_agents

### `agents.py` (AI Components)
- **Purpose**: OpenAI client setup and AI agent creation
- **Contents**:
  - `setup_openai_client()`: Creates instructor-wrapped OpenAI client
  - `create_chat_system_prompt()`: Chat agent system prompt
  - `create_image_analysis_prompt()`: Image analysis system prompt
  - `create_case_decision_system_prompt()`: AC/RA classification system prompt
  - `create_image_analyzer()`: Image analysis agent factory
  - `create_chat_agent()`: Chat agent factory with memory
  - `create_case_decision_agent()`: AC/RA decision agent factory
- **Dependencies**: instructor, openai, atomic_agents, schemas, config

### `routes.py` (Web Endpoints)
- **Purpose**: Contains all Flask route handlers
- **Contents**:
  - `register_routes(app)`: Registers all routes with Flask app
  - Route handlers: `/`, `/chat`, `/upload_images`, `/admin`, etc.
  - `/classify_case`: New endpoint to test the decision agent
  - Image upload and analysis logic
  - Session management integration
- **Dependencies**: Flask, utils, agents, schemas

### `utils.py` (Helper Functions)
- **Purpose**: Utility functions and session management
- **Contents**:
  - `get_or_create_session()`: Session management with memory
  - `update_case_from_ai_response()`: AI response to case data mapping
  - `classify_case_with_decision_agent()`: Uses decision agent for case classification
  - Database integration
- **Dependencies**: Flask sessions, atomic_agents, schemas, database

### `test_decision_agent.py` (Testing Script)
- **Purpose**: Test and demonstrate the AC/RA decision agent
- **Contents**:
  - Comprehensive test cases for AC, RA, and OTHER scenarios
  - Automated testing with accuracy reporting
  - Interactive testing mode for manual case testing
  - Rich console output with formatted tables and panels
- **Usage**: `python test_decision_agent.py` or `python test_decision_agent.py interactive`

## New Feature: AC/RA Decision Agent

### Overview
The decision agent automatically classifies customer cases into:
- **AC (Accident Care)**: Accidents, collisions, damage from external factors
- **RA (Road Assistance)**: Mechanical breakdowns, flat tires, fuel issues
- **OTHER**: Non-vehicle related inquiries

### Key Features
- **Greek Language Support**: System prompts and responses in Greek
- **Confidence Levels**: HIGH, MEDIUM, LOW based on clarity of indicators
- **Key Indicator Extraction**: Lists specific words/phrases that led to the decision
- **Follow-up Questions**: Suggests clarifying questions for ambiguous cases
- **Fallback Logic**: Basic keyword matching if AI agent fails

### Integration Points
1. **New API Endpoint**: `/classify_case` for standalone testing
2. **Enhanced Chat Route**: Optional decision agent integration via `use_decision_agent` parameter
3. **Utility Function**: `classify_case_with_decision_agent()` for reusable classification
4. **Comprehensive Testing**: Automated and interactive testing capabilities

## Benefits of This Structure

### 1. **Modularity**
- Each file has a single, clear responsibility
- Easy to locate and modify specific functionality
- Reduced cognitive load when working on specific features
- New decision agent cleanly separated from existing code

### 2. **Maintainability**
- Changes to AI prompts only affect `agents.py`
- Route modifications only affect `routes.py`
- Schema changes only affect `schemas.py`
- Decision logic isolated in dedicated functions

### 3. **Testability**
- Each module can be tested independently
- Dedicated test script for decision agent validation
- Mock dependencies easily in unit tests
- Isolated functionality reduces test complexity

### 4. **Reusability**
- Decision agent can be used across different routes
- Agents can be reused across different contexts
- Schemas can be imported by other modules
- Configuration centralized and reusable

### 5. **Scalability**
- Easy to add new classification types (beyond AC/RA)
- New AI agents can be added to `agents.py`
- New decision criteria can be added to schemas
- Decision logic can be enhanced without affecting other components

## Usage Examples

### Testing the Decision Agent
```bash
# Run automated tests
python test_decision_agent.py

# Run interactive testing
python test_decision_agent.py interactive
```

### Using the API Endpoint
```bash
# Test case classification
curl -X POST http://localhost:8080/classify_case \
  -H "Content-Type: application/json" \
  -d '{"message": "Τράκαρα με άλλο αυτοκίνητο", "context": ""}'
```

### Enhanced Chat with Decision Agent
```bash
# Chat with decision agent enabled
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Έσκασε το λάστιχό μου", "use_decision_agent": true}'
```

## Import Dependencies

```python
# agents.py depends on:
from schemas import ImageAnalysisInput, ImageAnalysisOutput, CustomOutputSchema, CaseDecisionInputSchema, CaseDecisionOutputSchema
from config import get_api_key

# routes.py depends on:
from utils import get_or_create_session, update_case_from_ai_response, db, classify_case_with_decision_agent
from agents import setup_openai_client, create_image_analyzer, create_chat_agent
from schemas import ImageAnalysisInput

# utils.py depends on:
from schemas import CustomOutputSchema, CaseDecisionInputSchema
from database import ChatDatabase

# test_decision_agent.py depends on:
from utils import classify_case_with_decision_agent
from rich.console import Console, Table, Panel

# app.py depends on:
from config import create_app
from routes import register_routes
```

## Running the Application

The application is run the same way as before:

```bash
python app.py
```

The modular structure is transparent to the end user - all functionality remains the same, but the code is now much more organized and maintainable, with the addition of intelligent case classification.

## Development Workflow

1. **Adding new routes**: Add to `routes.py` in the `register_routes()` function
2. **Modifying AI behavior**: Update system prompts in `agents.py`
3. **Adding new data fields**: Update schemas in `schemas.py`
4. **Configuration changes**: Modify `config.py`
5. **New helper functions**: Add to `utils.py`
6. **Testing decision logic**: Use `test_decision_agent.py` for validation
7. **New classification types**: Extend decision agent schemas and prompts

This structure follows Flask best practices and makes the application much more professional and maintainable, with the added capability of intelligent case classification for improved customer service automation. 