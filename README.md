# NexusAI Agent — v1.0

An AI-powered personal assistant built with **Google Gemini, LangGraph, LangChain, FastAPI, and PostgreSQL**. NexusAI combines LLM-based reasoning with tool calling, semantic document retrieval, persistent conversation state, email integration, and automated report generation.

> **Version:** 1.0.0  
> **Project Type:** Generative AI Learning Project  
> **Status:** Experimental

## Table of Contents

- [Overview](#overview)
- [Project Demo](#project-demo)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Tech Stack](#tech-stack)
- [RAG Implementation](#rag-implementation)
- [AI Agent and LangGraph](#ai-agent-and-langgraph)
- [Available Tools](#available-tools)
- [Authentication and User Management](#authentication-and-user-management)
- [File Uploads and Report Generation](#file-uploads-and-report-generation)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
- [Current Limitations](#current-limitations)
- [Future Improvements](#future-improvements)
- [Disclaimer](#disclaimer)

## Overview

NexusAI is a personal AI assistant designed to explore how modern Generative AI components can work together in a single application.

Instead of relying only on an LLM to generate responses, the system allows the model to select and execute tools when appropriate. LangGraph coordinates the execution flow, while PostgreSQL supports user data, vector retrieval, and persistent conversation state.

The project explores practical applications of:

- Large Language Models (LLMs)
- AI agents and tool calling
- Retrieval-Augmented Generation (RAG)
- Vector similarity search
- Persistent conversation state
- REST API development
- Authentication and password hashing
- Multimodal input and document processing

## Project Demo

Watch the NexusAI Agent v1.0 demo on YouTube to see the project in action.

[![NexusAI Agent v1.0 — YouTube Demo](https://img.youtube.com/vi/bdR5vadUPx8/maxresdefault.jpg)](https://www.youtube.com/watch?v=bdR5vadUPx8&t=61s)

▶️ **[Watch the full demo on YouTube](https://www.youtube.com/watch?v=bdR5vadUPx8&t=61s)**

## Key Features

### AI Agent

- Google Gemini integration through LangChain.
- Model-driven tool selection using tool calling.
- Graph-based execution and conditional routing with LangGraph.
- Repeated interaction between the LLM and tools until a final response is generated.

### Retrieval-Augmented Generation (RAG)

- Local document retrieval using PGVector.
- Sentence embeddings using `sentence-transformers/all-MiniLM-L6-v2`.
- Semantic similarity search over stored document chunks.
- Retrieval of the five most similar chunks for a query.

### Persistent Conversation State

- LangGraph checkpointing with PostgreSQL.
- Conversation threads identified using a `thread_id`.
- Previous messages can be restored when the same thread is used again.

### Productivity Tools

- Web search with Tavily.
- Email reading and sending through Gmail.
- Mathematical calculations.
- Automated report generation in PDF, Excel, and text formats.

### Backend and Security

- FastAPI endpoints.
- User registration and login.
- Password hashing using Argon2.
- JWT-based authentication.
- Authenticated report downloads.
- PDF and TXT file uploads, plus image input support.

## System Architecture

The application consists of several cooperating components:

1. **Client:** Sends chat messages and optional files or images.
2. **FastAPI:** Handles requests, authentication, and responses.
3. **LangGraph:** Manages the LLM and tool execution workflow.
4. **Google Gemini:** Processes messages and decides when to call tools.
5. **Tool Layer:** Executes search, email, calculation, document retrieval, and report-generation operations.
6. **PostgreSQL:** Stores user records, supports vector retrieval through PGVector, and persists LangGraph checkpoints.

### Agent Execution Flow

```mermaid
flowchart TD
    A[User Request] --> B[FastAPI]
    B --> C[Authentication]
    C --> D[LangGraph]
    D --> E[Gemini LLM]
    E --> F{Tool Calls?}
    F -- Yes --> G[ToolNode]
    G --> H[Execute Selected Tools]
    H --> E
    F -- No --> I[Final Response]
    I --> J[FastAPI Response]
```

The model can call a tool, receive its result, and continue reasoning before returning a final answer.

## Tech Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| LLM | Google Gemini |
| LLM Integration | LangChain |
| Agent Orchestration | LangGraph |
| Backend API | FastAPI |
| Relational Database | PostgreSQL |
| Vector Search | PGVector |
| Embeddings | Hugging Face Sentence Transformers |
| Authentication | JWT |
| Password Hashing | Argon2 |
| Web Search | Tavily |
| PDF Processing | pypdf, ReportLab |
| Excel Generation | openpyxl |
| Configuration | python-dotenv |

## RAG Implementation

NexusAI includes a local semantic search tool built with **LangChain PGVector** and Hugging Face embeddings.

The purpose of this component is to retrieve relevant information from a local document collection rather than relying exclusively on the LLM's general knowledge.

### 1. Embedding Model

The project uses:

`sentence-transformers/all-MiniLM-L6-v2`

The embedding model converts text into numerical vectors that represent semantic information. These vectors enable similarity-based retrieval.

The configured model runs on CUDA and uses normalized embeddings. CPU configuration may be used if GPU execution is unavailable.

```python
from langchain_huggingface import HuggingFaceEmbeddings

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cuda"},
    encode_kwargs={"normalize_embeddings": True}
)
```

**Note:** This configuration expects a working CUDA-compatible environment. Change the device to `"cpu"` if GPU execution is unavailable.

### 2. Vector Store with PGVector

The project uses PostgreSQL with the PGVector extension to store and retrieve document embeddings.

```python
from langchain_postgres import PGVector

vector_store = PGVector(
    embeddings=embedding_model,
    collection_name="my_documents",
    connection=CONNECTION,
)
```

The vector store connects the embedding model to a PostgreSQL-backed collection named `my_documents`.

### 3. Semantic Similarity Search

The `local_search` tool retrieves the five most similar document chunks for a user query.

```python
@tool
def local_search(query: str):
    results = vector_store.similarity_search(
        query,
        k=5
    )

    return "\n".join(
        document.page_content
        for document in results
    )
```

At a high level, retrieval works as follows:

1. The user asks a question.
2. The query is embedded into a vector.
3. PGVector searches the stored document vectors for similar content.
4. The top five matching chunks are returned.
5. The agent receives the retrieved text and can use it to formulate a response.

### 4. RAG Workflow

```mermaid
flowchart TD
    A[User Question] --> B[Embedding Model]
    B --> C[Query Vector]
    C --> D[PGVector Similarity Search]
    D --> E[Top 5 Document Chunks]
    E --> F[Agent Receives Retrieved Context]
    F --> G[LLM Generates Response]
```

### Important RAG Scope

The code included in this version implements **retrieval from an existing vector collection**. A complete ingestion pipeline would additionally load source documents, split them into chunks, generate embeddings for those chunks, and insert them into PGVector.

That ingestion workflow is not included in the code shown here.

The current retrieval function also returns document text without explicitly formatting metadata or providing source citations to the user. Retrieval quality and answer grounding should be evaluated as the project evolves.

## AI Agent and LangGraph

The agent workflow is implemented using LangGraph's `StateGraph` and `MessagesState`.

### Graph Components

**LLM Node**

Invokes the Gemini model with the conversation messages and the available tool definitions.

**Tool Node**

Uses LangGraph's `ToolNode` to execute the tools requested by the model.

**Conditional Routing**

Checks whether the latest assistant message contains tool calls.

- If tool calls exist, control moves to the tool node.
- Otherwise, the graph ends and returns the final response.

### Graph Workflow

```python
graph = StateGraph(MessagesState)

graph.add_node("llm", llm_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "llm")
graph.add_edge("tools", "llm")

graph.add_conditional_edges(
    "llm",
    route,
    {
        "tools": "tools",
        "end": END,
    },
)
```

This creates a tool-calling loop:

**LLM → Tools → LLM → Final Response**

The model can use the results of a tool call to determine its next action.

### Persistent State with PostgreSQL

The project uses LangGraph's `PostgresSaver` checkpointer.

```python
checkpointer = cm.__enter__()
checkpointer.setup()

app = graph.compile(
    checkpointer=checkpointer
)
```

Each conversation is associated with a configurable `thread_id`. The application uses the authenticated user's ID as that identifier, allowing conversation state to be restored for subsequent requests using the same ID.

The checkpointer preserves graph state; it is not a separate semantic long-term memory or a user-profile memory system.

**Implementation note:** The checkpointer's context manager must be managed throughout the application's lifecycle. In a production implementation, initialize and close resources through FastAPI lifespan handling.

## Available Tools

The agent has access to six tools.

| Tool | Purpose |
|---|---|
| `web_search` | Searches the web using Tavily. |
| `local_search` | Retrieves relevant text from the PGVector collection. |
| `send_mail` | Sends emails through Gmail SMTP. |
| `read_emails` | Searches and reads emails from a Gmail inbox through IMAP. |
| `calculator` | Evaluates supported mathematical expressions. |
| `create_report` | Generates PDF, Excel, or text reports. |

The LLM selects tools through its tool-calling interface, while LangGraph controls their execution and the return of tool results to the model.

## Authentication and User Management

The backend provides registration and login functionality.

### Registration

- Accepts first name, last name, age, email, and password.
- Hashes passwords using Argon2 before storage.
- Stores user records in PostgreSQL.
- Handles duplicate email addresses with an HTTP `409 Conflict` response.

### Login

- Looks up the account by email.
- Verifies the submitted password against the stored hash.
- Issues a signed JWT access token when authentication succeeds.

### JWT Authentication

Protected endpoints use a bearer token dependency to identify the authenticated user.

The configured token expiration is 30 minutes.

Passwords are stored as hashes rather than plaintext. Application secrets and database credentials must be supplied through environment variables and must never be committed to the repository.

## File Uploads and Report Generation

### Supported Chat Inputs

The chat endpoint accepts:

- Text messages.
- PDF files, with text extracted using `pypdf`.
- TXT files, decoded as UTF-8.
- Images, encoded as Base64 and passed to the model as image input.

The extracted text is added to the chat request. In the current implementation, uploaded PDF and TXT content is not automatically split, embedded, and indexed in PGVector.

### Report Generation

The `create_report` tool supports three output types:

- **PDF:** Generated using ReportLab.
- **Excel:** Generated using openpyxl.
- **Text:** Generated as a UTF-8 text file.

When report generation succeeds, the application returns the generated filename and a download URL.

The download endpoint checks the requested filename, verifies that the file is inside the configured reports directory, and requires authentication.

Authentication alone does not establish ownership of a report. Per-user report ownership and authorization should be added before using the application with multiple users.

## Project Structure

The following is a logical structure based on the supplied code. Adjust filenames to match the actual repository.

```text
NexusAI-Agent-v1/
├── main.py          # FastAPI endpoints and file uploads
├── model.py         # Gemini, LangGraph, tools, and checkpointing
├── tools.py         # RAG, web search, email, calculator, reports
├── auth.py          # User registration and login
├── sec.py           # Password hashing and JWT authentication
├── schame.py        # Pydantic request schemas
├── .env             # Local secrets; never commit
├── .gitignore
├── requirements.txt
└── README.md
```

## Installation

### Prerequisites

- Python 3.10 or a compatible version supported by your dependencies.
- PostgreSQL.
- The PGVector PostgreSQL extension.
- A Google Gemini API key.
- A Tavily API key.
- Gmail credentials configured for SMTP and IMAP.
- A compatible CUDA environment if using the configured GPU embedding setup.

### 1. Clone the Repository

```bash
git clone https://github.com/Yousef-salah-Ma/NexusAI-Agent-v1.git
cd NexusAI-Agent-v1
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

After preparing the project's `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 4. Configure PostgreSQL

Create the application database:

```sql
CREATE DATABASE mydatabase;
```

Connect to the database, then enable the PGVector extension:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Ensure the database connection used by the application has permission to create and access the required tables and vector-store structures.

Run the user-table initialization script if your repository includes one.

## Environment Variables

Create a local `.env` file and configure the required values.

```dotenv
# PostgreSQL - Vector Store / RAG
CONNECTION=postgresql+psycopg://postgres:YOUR_DB_PASSWORD@localhost:5432/mydb

# PostgreSQL - Users and Checkpoint Storage
CONNECTION_store=postgresql://postgres:YOUR_DB_PASSWORD@localhost:5432/store_users

# Google Gemini API
google_api_key=YOUR_GOOGLE_API_KEY

# Tavily Web Search API
tavily_api_key=YOUR_TAVILY_API_KEY

# JWT Authentication
SECRET_KEY=REPLACE_WITH_A_LONG_RANDOM_SECRET
ALGORITHM=HS256

# Email Configuration
FROM_EMAIL=your_email@gmail.com
PASSWORD_EMAIL=YOUR_EMAIL_APP_PASSWORD
```

**Configuration notes:**

- The supplied code currently reads `SECRET_KEY` as the PostgreSQL password in `auth.py` and in the user-table initialization function. Change those database connection calls to use the dedicated `DB_PASSWORD` variable before relying on this example configuration.
- The `CONNECTION_store` and `CONNECTION` variables may point to the same database, but their connection formats and purposes differ.
- Use URL-safe encoding for special characters in database connection strings where required by the URL format.
- Never commit `.env` or real API keys, tokens, passwords, or email app passwords.
- Add `.env` to `.gitignore`.
- The variable names in the `.env` file must match those expected by your Python code.

## Running the Application

After configuring the environment and installing dependencies, start the FastAPI development server:

```bash
uvicorn main:app --reload
```

Open the interactive API documentation at:

http://127.0.0.1:8000/docs

The configured CORS origin in the current code is `http://127.0.0.1:5500`. Update it if your frontend runs on a different origin.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/Register` | Registers a new user. |
| `POST` | `/login` | Authenticates a user and returns a JWT. |
| `POST` | `/chat` | Sends a message and optional file or image to the AI assistant. |
| `GET` | `/download/{filename}` | Downloads a generated report with authentication. |

### Chat Request

The `/chat` endpoint accepts `multipart/form-data`.

- `message`: Required text message.
- `image`: Optional image upload.
- `file`: Optional PDF or TXT upload.
- `Authorization`: Bearer token.

The response includes the assistant's answer and, when a report was generated successfully, a download URL.

## Current Limitations

This version is experimental and is primarily intended for learning and technical exploration.

Areas that require further work include:

- Automated tests and systematic evaluation of agent behavior.
- RAG ingestion, retrieval evaluation, source attribution, and improved ranking.
- Structured error handling, retries, and execution limits.
- File-size limits and stronger upload validation.
- Per-user report ownership and access control.
- Human confirmation for sensitive actions such as sending emails.
- Safer handling of instructions contained in retrieved documents, emails, and web content.
- Production-grade configuration, logging, monitoring, and deployment.
- Robust handling of concurrent requests and database/checkpointer lifecycle.

## Future Improvements

Planned areas for future versions include:

- Advanced RAG strategies and retrieval evaluation.
- Reranking and better document chunking.
- LLM and tool-call evaluation.
- Observability and tracing.
- Streaming responses.
- Automated tests.
- Docker-based deployment.
- More robust authorization and human-in-the-loop workflows.

## Disclaimer

NexusAI Agent v1.0 is a personal learning project built to explore Generative AI engineering concepts and integrate them into a practical application.

It is not presented as a production-ready system. Review security, privacy, authorization, and reliability requirements before using it with sensitive data or real users.

---

**Built as part of a hands-on journey into Generative AI Engineering.**
