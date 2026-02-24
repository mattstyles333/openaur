# OpenAur Dashboard

A SvelteKit-based dashboard for monitoring and managing OpenAur.

## Features

- **Overview Dashboard** - System status at a glance
- **Memory Browser** - Search and explore stored memories
- **Agent Monitor** - Real-time agent status and control
- **Session Manager** - Tmux session overview
- **Heart Status** - Health and emotional state

## Development

```bash
cd apps/dashboard
npm install
npm run dev
```

## Build

```bash
npm run build
```

## Docker

```bash
docker build -t openaur-dashboard .
docker run -p 8001:3000 -e VITE_API_URL=http://openaura:8000 openaur-dashboard
```

## Environment Variables

- `VITE_API_URL` - OpenAur API URL (default: http://localhost:8000)
