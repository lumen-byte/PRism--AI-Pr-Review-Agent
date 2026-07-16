# Security & Authentication

- **Webhooks**: Validated using HMAC-SHA256 signatures to ensure payloads come directly from GitHub.
- **Dashboard**: Protected by JWT-based authentication.
- **API Keys**: Groq and GitHub tokens are passed via environment variables and never exposed to the frontend.
