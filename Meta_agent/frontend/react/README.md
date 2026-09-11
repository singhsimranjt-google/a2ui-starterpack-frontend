# A2UI React Starter Framework

This project was bootstrapped with `goog-adk-a2ui-starter`. It is a modern, enterprise-ready React application built with Vite and TypeScript, designed to seamlessly render dynamic UI payloads (A2UI) from a Google ADK Python backend.

## 📁 Folder Structure

```text
my-react-app/
├── src/
│   ├── components/
│   │   └── A2UIRenderer.tsx       # 🎨 Core Drawing Engine (A2UI Component)
│   ├── App.tsx                    # 🧠 The Main Application Host
│   ├── index.css                  # 💅 Global Styling & Theming
│   └── main.tsx                   # 🚀 React DOM Bootstrapper
├── index.html                     # HTML Entry Point
├── package.json                   # Project Dependencies & Scripts
├── tsconfig.json                  # TypeScript Configuration
└── vite.config.ts                 # Vite Build Configuration
```

## 🧩 Important Components

### 1. `App.tsx` (The Brain)
This is the root application file. Its primary responsibilities are:
- **State Management:** Maintains the user's `appState` (form inputs) and `history` (the timeline of the chat).
- **Network Routing:** Uses the `fetch` API and Server-Sent Events (SSE) to stream chunks of JSON from your Python backend.
- **Action Dispatching:** Catches `onAction` events bubbling up from the renderer and forwards them back to the LLM agent.

### 2. `A2UIRenderer.tsx` (The Drawing Engine)
This is a pure, schema-driven React component. 
- **Decoupled:** It has absolutely zero network logic. It only knows how to turn JSON into HTML.
- **Recursive:** It recursively traverses the A2UI JSON payload (e.g., `Card` -> `Column` -> `Button`).
- **Data Binding:** It securely resolves paths like `{"path": "name"}` against the global `appState` so your form inputs are instantly synced.

## 🚀 Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```
2. Start the Vite development server:
   ```bash
   npm run dev
   ```
3. Ensure your Python Google ADK backend is running on `http://localhost:8080`.
