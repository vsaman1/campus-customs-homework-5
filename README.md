# Campus Customs Homework 5

## Project Layout

```text
Homework 5/
|-- backend/                 FastAPI application, team orchestration, and agent prompts
|-- data/
|   |-- campus_customs.db    Original database (preserved)
|   `-- campus_customs_new.db Working database used by the app
|-- frontend/                React/Vite ticket board
|-- mcp_server/              FastMCP server and documentation
|-- output/                  Audit trail, resolved-ticket artifacts, and visual evidence
|-- .mcp.json                MCP server configuration
`-- requirements.txt         Python dependencies
```

## Setup

Use a project-local Python environment and install the backend dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

From the Homework 5 project root, copy the provided template to a local `.env` file. It must not be committed:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and enter your own Portkey key:

```text
PORTKEY_API_KEY=your_key_here
PORTKEY_MODEL=gpt-6-luna
```

Install the React dependencies:

```powershell
Set-Location frontend
npm install
Set-Location ..
```

## Clean Run Reset

Keep `data/campus_customs.db` unchanged. Before a clean run or a complete three-ticket demonstration, reset the working copy:

```powershell
Copy-Item data\campus_customs.db data\campus_customs_new.db -Force
```

This reset is required before starting the full Ticket 101, Ticket 102, and Ticket 103 run so the payment and ticket states begin from the original data.

## Run the Application

Open separate terminals in this project folder.

1. Start the MCP server:

   ```powershell
   .\.venv\Scripts\python.exe mcp_server\server.py
   ```

2. Start the FastAPI backend:

   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
   ```

3. Start the React ticket board:

   ```powershell
   Set-Location frontend
   npm run dev
   ```

Open the local URL printed by Vite (normally `http://localhost:5173`). The board communicates with the FastAPI API through its configured development proxy.

## Submission Notes

Both database files under `data/` are intentionally tracked so graders can inspect the preserved original and the completed working copy. The repository ignores real environment files, virtual environments, dependency folders, and caches.