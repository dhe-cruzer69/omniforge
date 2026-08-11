# ARIEX Control Contract

## Role
Free/local AI workbench orchestrator with persistent skill memory and feedback loops.

## Observed baseline
- Ollama local inference
- Chroma vector skill store
- Brand Voice Vault and goal templates
- Plan → Execute → Capture → Learn loop

## Advanced upgrade track
1. Add deterministic evaluation cases for skill reuse quality.
2. Add async/parallel tool execution with bounded concurrency.
3. Add run tracing, latency and model resource metrics.
4. Add skill versioning and rollback.
5. Add local health checks and reproducible environment validation.
6. Export evidence to the ARIEX fleet dashboard.

## Definition of done
A skill improvement is validated only when evaluation evidence shows the new version is at least as reliable as the previous version.
