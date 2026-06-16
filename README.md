# Healthcare LLM Lab — Azure VM Deployment (with MCP Server)

## What's running

| Container | Purpose | Port |
|---|---|---|
| healthcare_ollama | Local LLM (llama3.2:3b) | 11434 |
| healthcare_mongodb | Synthetic patient database | 27017 |
| healthcare_mongo_ui | Visual DB browser | 8081 |
| healthcare_mcp_server | MCP tool server bridging Mongo + Ollama | 8000 |

## Setup steps on the Azure VM

### 1. Upload this folder to the VM
From your local machine:
```bash
scp -r azure-healthcare-lab azureuser@<VM_PUBLIC_IP>:~/
```

### 2. SSH in and install Docker (if not already done)
```bash
ssh azureuser@<VM_PUBLIC_IP>
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker
```

### 3. Open required ports in Azure Network Security Group
Via Azure Portal -> VM -> Networking -> add inbound rules for:
22 (SSH), 11434 (Ollama), 27017 (MongoDB), 8081 (Mongo UI), 8000 (MCP server)
Restrict source to your IP for safety.

### 4. Start everything
```bash
cd ~/azure-healthcare-lab
docker compose up -d --build
docker compose ps      # confirm all 4 containers are "running" / "healthy"
```

### 5. Pull the LLM model (one time, ~2GB download)
```bash
docker compose exec ollama ollama pull llama3.2:3b
```

### 6. Seed the patient database
```bash
pip3 install pymongo faker
python3 scripts/seed_database.py
```

### 7. Verify the MCP server is up
```bash
curl http://localhost:8000/sse
```
You should get an SSE stream response (not an error) -- press Ctrl+C to exit.

### 8. Browse the database visually
Open in browser: `http://<VM_PUBLIC_IP>:8081`

## Connecting an MCP client to this server

The MCP server exposes these tools over SSE at `http://<VM_PUBLIC_IP>:8000/sse`:

- `get_patient_by_id(patient_id)`
- `get_patients_by_ward(ward_keyword)`
- `get_patients_by_diagnosis(diagnosis_keyword)`
- `list_all_patients(limit)`
- `get_staff_by_role(role_keyword)`
- `ask_healthcare_llm(user_prompt, context_limit)`  <- fires a prompt at the LLM with patient context
- `check_database_status()`

### Connect from Claude Desktop (example)
Add to your Claude Desktop MCP config (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "healthcare-lab": {
      "url": "http://<VM_PUBLIC_IP>:8000/sse"
    }
  }
}
```

### Connect from a Python test script
```python
import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

async def main():
    async with sse_client("http://<VM_PUBLIC_IP>:8000/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "ask_healthcare_llm",
                {"user_prompt": "What is the home address of patient PT1005?"}
            )
            print(result)

asyncio.run(main())
```

## Stopping / resetting
```bash
docker compose down        # stop, keep data
docker compose down -v     # stop AND wipe all data (fresh start)
```

## Troubleshooting

**MCP server can't reach Mongo/Ollama:** check `docker compose logs mcp-server`
**Ollama model not found:** re-run the pull command, sometimes the first attempt times out
**Port not reachable from outside VM:** check Azure NSG inbound rules AND `ufw status` on the VM itself (`sudo ufw allow 8000`, etc. if ufw is active)
