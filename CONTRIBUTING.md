# Contributing to PRism

First off, thank you for considering contributing to PRism! It's people like you that make PRism such a great tool.

## 1. Where do I go from here?

If you've noticed a bug or have a feature request, make sure to check our [Issues](https://github.com/yourusername/prism-ai/issues) page to see if someone else has already created a ticket. If not, go ahead and make one!

## 2. Fork & create a branch

If this is something you think you can fix, then fork PRism and create a branch with a descriptive name.

A good branch name would be (where issue #325 is the ticket you're working on):

```sh
git checkout -b 325-add-linear-integration
```

## 3. Local Development Setup

To run PRism locally, you will need Docker and Docker Compose.

1. Copy the example environment file:
   ```sh
   cp .env.example .env
   ```
2. Add your Groq API key and GitHub Fine-Grained token to `.env`.
3. Start the application:
   ```sh
   docker-compose up --build
   ```
4. Access the dashboard at `http://localhost:8000/dashboard`.

## 4. Code Standards

- **Python**: We use `ruff` and `black` for formatting. Ensure your code passes standard linting before submitting.
- **Frontend**: Keep the frontend Vanilla JS to maintain zero-dependencies. Ensure `style.css` changes use existing CSS variables.
- **Testing**: Ensure any new agents or API endpoints have corresponding test coverage (if applicable).

## 5. Submitting a Pull Request

When you're ready to submit a Pull Request, please ensure you:
- Reference the related issue (e.g., "Fixes #325").
- Provide a clear summary of what your PR accomplishes.
- Wait for the CI pipeline to pass before requesting a review.

Thank you for contributing!
