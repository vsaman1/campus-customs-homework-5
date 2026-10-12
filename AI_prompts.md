# AI Prompt Log

## Problem 2 — Campus Customs Database Study

### Original Prompt

> now we are on problem 2 study the Campus Customs database and look through all the fields and tables. copy the original file to data/campus_customs_new.db - later problems update that working copy.  ssttudy the three open tickest so you can see hwo they link to other tables. start output/harness.md. for eahc table list the fields and one short line on why the table matters for the agent in a way that is comprehensible to humans and concise. you will keep growing this harness file later in teh problem

### Follow-up Prompts

None.

## Problem 8 — Agent Dashboard

### Original Prompt

> now we are on problem 8 agent dashboard
>
> build the frontend dashboard in frontend/ with react + vite + typescript. the page should call the routes you built in problem 7.. at minimum the board should
>
> list all three tickets
> let you pick one ticket and start the agent team on it
> show each agent and what they are saying / doing while the tickets ruN
> mark a ticket resolved when the run finishes
> show a short summary of waht each agent did on that ticket
> let a human approve a pay or purchase when asked
> show the check balance (it should drop after an approved pay)
>
> make the dashbaord look good. be creative with the layout and feel - this is a real desk people would want to sit at, so put thoughts into how it looks
>
> tell the front end to talk to your backend at [http://localhost:8000](http://localhost:8000/) on the backend allow the vite page origint (usually [http://localhost:5173](http://localhost:5173/) so teh browser is allwoed to call those routes. start the board with
>
> npm run dev
>
> this opens the react desk in your browser so you can pick tickets and watch agnets. write output/design.md with what you choose for the dashboard looks (layout, how agents read differently, how resolved tickets and cahs show up) and why - including the creative choices that maek it feel special and something humans would actually enjoy using

### Follow-up Prompts

None.

## Problem 7 — Backend Routes

### Original Prompt

> now we are on problem 7 backend routes
>
> your react frontend dashbaord (the next problem) needs a abckend it can call. in backend/main.py use FastAPI and add routes that do the following
>
> return the three tickets and whter each is open or resolved
> take a ticket id and run your agent team on that ticket
> return recent agent events - what each agent said and which toosl they used so the board can refresh
> approve a payment or purchase after a human clicks approve (agents only prepare the pay; thsi routes is what actually changes cash)
> return the current checkign balance from cash_accounts
> reset the database to the origincal vlaues when you want to try a fresh run
>
> from the backend/ folder  strat the server with
>
>  uvicorn main:app --reload --port 8000
>
> this turns on your backend at [http://localhost:8000](http://localhost:8000/) so the front end dashbaord cna call these routes. in output/harness.md lsit each route in one line (what url/what it does)

### Follow-up Prompts

None.

## Problem 5 — Campus Customs Agent Team

### Original Prompt

> we are now on problem 5 buidl the agent team and grow the mcp tools
>
> build teh agentic team for campus customs using pydanticAI: Boss, Inventory, Accounting Facilities, and Customer Service. include prompts, models, and agent loops so they cna delegate work to each other with full connectivity. put the agent prompts in backend/prompts/ - one file per agent. put data types in backend/models.py and the agent files under backend/ (your layout can vary as long as the five roles are clear). use the portkey_api_key and only gpt-6-luna for every agent. write each prompt in your own words with the shop rules that agent needs. more detailed prompts that cover all aspects fo an agent's work and scope score higher than a short generic prompt
>
> add any tools the agents need to the mcp server so they cna work on the open tickets shop facts come from teh mcp server over data/campus_customs_new.db - do nto invent a second shop-tools layer that bypass MCP. wire the agent so they append to output/audit_trail.json as tehy run for each agent-loop step, record enough to audit later. append to this file - do not wipe it each run.
>
> in output/harness.md list each agent and each mcp tool (including ones you add in this problem) along with which tables the tools uses. also add a short safety section: the guardrails a real business would want when agents touch real customers and real money plus limits that keep token use in check. update mcp_server/readme.md so the tools  list matches what you have now

A follow-up prompt was necessary because the PydanticAI installation timed out and required an explicit installation and import verification before the team could be implemented.

### Follow-up Prompts

> PydanticAI installation timed out. please continue from the current state and do not redo completed work.
>
> first, install `pydantic-ai` into the existing Homework 5 `.venv` and verify that `import pydantic_ai` works.
>
> once it is installed, continue problem 5 exactly from where you left off and build the five-agent PydanticAI team using only `gpt-6-luna` through Portkey.
>
> keep all shop facts and database access going through the MCP server over `data/campus_customs_new.db`.
>
> if the install is still blocking, stop and tell me exactly what command failed and the error instead of repeatedly waiting or redoing the project.

## Problem 6 — Ticket Plans

### Original Prompt

> now we are on problem 6 plan the three tickets
>
> build output/desk_tickets.html, a page you can double click with one tab per ticekt (101,102,103). also add empty cash and reflection tabs for later problems (leave them blank)
>
> on each ticket tab fill an expected section only (leave room for an actula section that we will fill out later). for each ticket's expected session write the below. do not run the agents yet
>
> Ticket 101
> Boss should call Inventory first because the customer needs a specific shirt and size so first we need to see if we have it.
>
> Expected delegations: Inventory should call Accounting because size S is out of stock and Bulldog Print Co has an overdue $840 invoice that needs to be dealt with before they can ship more. Customer Service can then draft a response for the customer.
>
> Expected MCP tools: inventory lookup, invoice lookup, cash balance lookup, vendor lead time lookup, and payment prep if needed.
>
> Ticket 102
> Boss should call Facilities first because this is a rent/lease issue.
>
> Expected delegations: Facilities should call Accounting to make sure we have enough cash for the $2,400 rent and prepare the payment for human approval. The checking account has $3,400 so we should be able to pay it without going negative.
>
> Expected MCP tools: lease lookup, date lookup, cash balance lookup, and payment prep.
>
> Ticket 103
> Boss should call Inventory first because the customer wants 20 medium hoodies and we need to see if we have enough stock.
>
> Expected delegations: Inventory should call Accounting because we only have 8 in stock so we are short 12. Accounting should check the $22 cost and $58 price to see how much discount we can give while still making money. They may also need to deal with the overdue Bulldog Print Co invoice before more hoodies can ship. Customer Service can draft the final response.
>
> Expected MCP tools: inventory lookup, pricing lookup, vendor lead time lookup, invoice lookup, cash balance lookup, and payment prep if needed.

### Follow-up Prompts

None.

## Problem 3 — Campus Customs MCP Server

### Original Prompt

> now we are on problem 3 build the mcp server. write an mcp server in mcp_server/ using fastmcp. it iwll talk to data/campus_customs_new.db. you do nto need to connect or run ti in htis problem. every agent  in this homework uses the tools in this mcp server. you will add mroe tools to it later; for now write three tools you know you will need for the tickets in the database. they direclty help adn resolve the three open tickets. keep the names clear. never invent any data only use information in the database. in output/harness.md list each of yoru three mcp tools for every tool including which table it reads which ticket it helps unlock (101,102,103) adn one sentence on why that tool is the right one for that ticket. vague lines like reads inventory score low - tie the tool to the ticket. also add a short mcp_server/README.md file that explains what the mcp server is for, which database file it uses, and the three tools it has

A follow-up prompt was necessary because FastMCP installation had not yet completed and its availability needed to be verified before implementing the server.

### Follow-up Prompts

> Please continue from the current state. If the FastMCP installation is blocking, verify whether it actually installed successfully. If not, install only the required package in the existing Homework 5 virtual environment, then continue Problem 3 without redoing completed work.

## Problem 4 — MCP Connection and Tool Smoke Tests

### Original Prompt

> now we are on problem 4 add the mcp server to this project so the vibe coder can call the tools. save the connection json text in .mcp.json at the project root. with this connected, test all three  of the mcp tools saee the evidence for eahc test in output/mcp_smoke.json for every test save
>
> the prompt you asked
> the tool name
> the tool output
>
> the output must match data/campus_customs_new.db
>
> make sure .mcp.json contains the actula connection config needed ot launch/connect your mcp server

### Follow-up Prompts

None.