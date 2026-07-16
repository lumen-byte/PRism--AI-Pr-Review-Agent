# GitHub Webhooks Setup

1. Navigate to your repository settings -> Webhooks.
2. Payload URL: `https://your-domain.com/api/v1/webhook/github`
3. Content type: `application/json`
4. Secret: The value of your `GITHUB_WEBHOOK_SECRET` in `.env`.
5. Events: Select "Pull requests" only.
