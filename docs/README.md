# uv-mcp

This directory contains the documentation for UV-MCP, built with [Astro Starlight](https://starlight.astro.build/).

## Project Structure

```
docs/
├── src/
│   ├── content/
│   │   └── docs/    # Markdown/MDX content
│   └── assets/      # Images and static assets
├── astro.config.mjs # Astro configuration
└── package.json     # Dependencies and scripts
```

## Running Locally

To work on the documentation locally:

1.  **Install dependencies**:
    ```bash
    npm install
    ```

2.  **Start the development server**:
    ```bash
    npm run dev
    ```
    This will start a local server at `http://localhost:4321`.

3.  **Build for production**:
    ```bash
    npm run build
    ```
    The static site will be generated in the `dist/` directory.

## Contributing to Docs

-   Edit files in `src/content/docs/`.
-   Use MDX for advanced components.
-   Ensure you run `npm run dev` to preview your changes before submitting a PR.