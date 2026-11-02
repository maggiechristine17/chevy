# Chevy

Chevy is a personal workspace for projects and pages. You can link them together, write notes in Markdown with `[[Title]]` links, and see how everything connects in a graph.

This repository holds the public website version, published by Netlify whenever `main` changes.

## How the website works

- `content.json` holds Maggie's published entries. Visitors see them read-only.
- Visitors can add their own entries as a sandbox. These are saved only in their own browser and never reach anyone else.
- `index.html` is built from the Claude version of Chevy with `tools/build_site.py`:

  ```
  python3 tools/build_site.py <claude-chevy.html> index.html
  ```

## Updating the site

1. Rebuild `index.html` if the Claude version's design or features changed.
2. Refresh `content.json` from the Claude version's saved projects, areas and resources (`pages`) with `tools/make_content.py`. Only entries with **Show on website** turned on are published.
3. Commit and push to `main`.
