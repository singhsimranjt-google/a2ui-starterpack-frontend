# {{PROJECT_TITLE}} (Angular A2UI Application)

This project is a standalone **Angular** client configured to render streaming **Material A2UI v0.9.1** component surfaces from Google ADK agents.

## Features
- **Material UI Catalog v0.9.1**: Renders `MaterialCard`, `MaterialColumn`, `MaterialRow`, `MaterialText`, `MaterialIcon`, and `MaterialButton`.
- **Signal Reactivity**: Uses Angular `signal()` and `computed()` for responsive, low-latency UI updates.
- **Interactive Action Loop**: Dispatches button click events with context prompts back to the Google ADK agent.
- **Pre-Built Flow**: Conversational flow supporting greetings and "What are your capabilities?" Material Card generation.

## Getting Started

### 1. Install Dependencies
```bash
npm install
```

### 2. Start Development Server
```bash
npm start
```
Navigate to `http://localhost:4200/` in your browser.
