# Web Chat UI

Frontend React (Vite + TypeScript) para conversar com personas sintéticas em uma UX estilo chat.

## Requisitos

- Backend FastAPI ativo em `http://127.0.0.1:8010`
- Node.js 20+

## Configuração

```bash
cp .env.example .env
```

Variável principal:

- `VITE_API_BASE_URL`: URL base da API (`/api`)

## Rodar local

```bash
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

URL local:

- `http://localhost:5173`

## Build

```bash
npm run build
```
