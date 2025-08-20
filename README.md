# rendergit

> Just show me the code.

Tired of clicking around complex file hierarchies of GitHub repos? Do you just want to see all of the code on a single page? Enter `rendergit`. Flatten any GitHub repository into a single, searchable HTML page with syntax highlighting, markdown rendering, and a clean sidebar navigation. Perfect for code review, exploration, and an instant Ctrl+F experience.

## Features

- **Dual view modes** - toggle between Human and LLM views
- **👤 Human View**: Pretty interface with syntax highlighting and navigation
- **🤖 LLM View**: Raw CXML text format - perfect for copying to Claude/ChatGPT for code analysis
- **Syntax highlighting** for code files via Pygments
- **Markdown rendering** for README files and docs
- **Smart filtering** - skips binaries and oversized files
- **Directory tree** overview at the top
- **Sidebar navigation** with file links and sizes
- **Responsive design** that works on mobile
- **Search-friendly** - use Ctrl+F to find anything across all files
- **Web server mode** - run as a web server accessible from any browser

## Installation

Install from source:

```bash
git clone https://github.com/Zeeeepa/rendergit
cd rendergit
pip install -e .
```

For web server functionality, install with the server extras:

```bash
pip install -e ".[server]"
```

## Usage

### CLI Mode

Use rendergit from the command line to generate a static HTML file:

```bash
# Basic usage
rendergit https://github.com/username/repo

# Specify output file
rendergit https://github.com/username/repo -o output.html

# Set maximum file size to render (default: 50 KiB)
rendergit https://github.com/username/repo --max-bytes 100000

# Don't open browser automatically
rendergit https://github.com/username/repo --no-open
```

### Web Server Mode

Run rendergit as a web server with a user-friendly interface:

```bash
# Start the web server using the CLI
rendergit https://github.com/username/repo --server --port 8000

# Or use the dedicated server script
rendergit-server --port 8000
```

Then open your browser and navigate to:
```
http://localhost:8000
```

### WSL2 Usage

When running on WSL2, the web server mode is particularly useful as it allows you to view the rendered repositories in your Windows browser:

1. Install rendergit with server extras in WSL2:
   ```bash
   pip install -e ".[server]"
   ```

2. Start the server (it will bind to all interfaces by default):
   ```bash
   rendergit-server
   ```

3. Open your Windows browser and navigate to:
   ```
   http://localhost:8000
   ```

## How It Works

The code will:

1. Clone the repo to a temporary directory
2. Render its source code into a single HTML file
3. In CLI mode: Save the file and open it in your browser
4. In web server mode: Serve the HTML directly through the web interface

Once open, you can toggle between two views:
- **👤 Human View**: Browse with syntax highlighting, sidebar navigation, visual goodies
- **🤖 LLM View**: Copy the entire codebase as CXML text to paste into Claude, ChatGPT, etc.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## License

Apache 2.0

