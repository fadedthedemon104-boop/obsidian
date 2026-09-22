# Architecture Overview

This project follows a lightweight client-first architecture with a secure sync layer and GitHub-backed persistence.

```mermaid
flowchart LR
    U[User] --> UI[Browser UI\nindex.html / dashboard.html]
    UI --> App[Client App Logic\nrenderApp / toggleHabit / mergeLogs]
    App --> LS[Local Storage\nBrowser cache / JSON data]
    App --> Sync[Sync Client\nbackup / merge requests]

    Sync --> Server[Sync Server\nExpress proxy]
    Server --> GitHub[GitHub Contents API]
    GitHub --> Remote[(Remote Backup\nGitHub repo / file)]

    subgraph ClientSide[Client-side layer]
        UI
        App
        LS
    end

    subgraph ServerSide[Server-side security layer]
        Sync
        Server
    end

    subgraph RemoteLayer[Remote persistence]
        GitHub
        Remote
    end

    App -->|reads/writes local data| LS
    App -->|secure backup + merge| Server
    Server -->|authenticated API calls| GitHub

    classDef user fill:#1f2937,stroke:#9ca3af,color:#fff;
    classDef client fill:#0f766e,stroke:#5eead4,color:#fff;
    classDef server fill:#1d4ed8,stroke:#93c5fd,color:#fff;
    classDef remote fill:#7c3aed,stroke:#c4b5fd,color:#fff;

    class U user;
    class UI,App,LS client;
    class Sync,Server server;
    class GitHub,Remote remote;
```

## Components

- Browser UI: renders habits, schedules, and activity state.
- Client App Logic: handles local state, rendering, toggling, and merge logic.
- Local Storage: stores the working data locally in the browser.
- Sync Server: acts as a trusted intermediary that avoids exposing credentials on the client.
- GitHub Contents API: stores backup snapshots and versioned updates remotely.
- Remote Backup: final persisted state for sync and recovery.

## Data flow

1. The user interacts with the browser UI.
2. Client logic updates local storage and refreshes the rendered view.
3. When a sync is triggered, the client sends a backup/merge request to the server.
4. The server performs GitHub API calls on behalf of the user using stored secrets.
5. The remote repository receives the updated backup state.

## Design intent

- Keep the frontend simple and fast.
- Avoid storing personal access tokens in the browser.
- Centralize GitHub access in a backend proxy for better security.
- Support sync, merge, and recovery with remote backups.
