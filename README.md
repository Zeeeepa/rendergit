# rendergit

> Just show me the code.

Tired of clicking around complex file hierarchies of GitHub repos? Do you just want to see all of the code on a single page? Enter `rendergit`. Flatten any GitHub repository into a single, searchable HTML page with syntax highlighting, markdown rendering, and a clean sidebar navigation. Perfect for code review, exploration, and an instant Ctrl+F experience.

## Basic usage

Git clone / pip install this repo somewhere:

```bash
git clone https://github.com/karpathy/rendergit
pip install -e .
```

Now you can just `rendergit` any GitHub url e.g.:

```bash
rendergit https://github.com/karpathy/nanoGPT
```

The code will:
1. Clone the repo to a temporary directory
2. Render its source code into a single static temporary HTML file
3. Automatically open the file in your browser

Once open, you can toggle between two views:
- **👤 Human View**: Browse with syntax highlighting, sidebar navigation, visual goodies
- **🤖 LLM View**: Copy the entire codebase as CXML text to paste into Claude, ChatGPT, etc.

There's a few other smaller options, see the code.

### Web Server Mode (for WSL2 and headless environments)

If you're using WSL2 or a headless environment where browser auto-opening doesn't work, you can run rendergit in server mode:

```bash
# Install with Flask dependency
pip install "rendergit[server]"

# Start the server (accessible from Windows via localhost:8000)
rendergit-serve --host 0.0.0.0 --port 8000
```

Then open http://localhost:8000 in your browser. This mode provides:
1. A simple web UI to enter GitHub repository URLs
2. Quick structure analysis (directory tree, file counts)
3. Full HTML generation on demand

This is especially useful for WSL2 users who encounter browser-related errors with the standard command.

## Features

- **Dual view modes** - toggle between Human and LLM views
  - **👤 Human View**: Pretty interface with syntax highlighting and navigation
  - **🤖 LLM View**: Raw CXML text format - perfect for copying to Claude/ChatGPT for code analysis
- **Web server mode** - run as a web server accessible from any browser
- **Syntax highlighting** for code files via Pygments
- **Markdown rendering** for README files and docs
- **Smart filtering** - skips binaries and oversized files
- **Directory tree** overview at the top
- **Sidebar navigation** with file links and sizes
- **Responsive design** that works on mobile
- **Search-friendly** - use Ctrl+F to find anything across all files

## Contributing

I vibe coded this utility a few months ago but I keep using it very often so I figured I'd just share it. I don't super intend to maintain or support it though.

## License

Apache 2.0 go nuts
