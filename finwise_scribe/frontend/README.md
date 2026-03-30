# Finwise Scribe Frontend

React + Vite trading terminal UI for Finwise Scribe.

## Run Locally

```bash
npm install
npm run dev
```

Default local URL: `http://localhost:3000`

## Current UX Features

- Responsive panel routing for `Sidebar`, `Market`, and `Scribe` chat views.
- Desktop split view with draggable resize handle between market and agent panels.
- Mobile bottom navigation with dedicated `MENU` access.
- Keyboard shortcuts:
	- `Ctrl/Cmd + P`: run forecast
	- `Ctrl/Cmd + /`: focus chat input
- Page switching from sidebar:
	- `TERM`: terminal market view
	- `SESS`: sessions archive
	- `CFG`: workspace settings

## Build

```bash
npm run build
```
