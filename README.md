# PWKM: Personal Work and Knowledge Management

A sophisticated system for human-AI collaboration in complex, multi-project knowledge work.

## What is PWKM?

PWKM is an integrated architecture that combines:
- **Work management**: Projects, tasks, milestones, deliverables, deadlines
- **Knowledge management**: Research, ideas, themes, theory-building, cross-project synthesis

Built through iterative collaboration between a human knowledge worker and Claude (Anthropic's AI assistant), PWKM addresses the fundamental challenge of maintaining coherent context across multiple concurrent projects while leveraging AI assistance effectively.

## Why PWKM?

When working with AI assistants, knowledge workers face specific challenges:

- **Context Fragmentation**: Each conversation starts fresh
- **Knowledge Silos**: Insights that bridge projects get lost
- **Discontinuity**: No systematic way to ensure comprehensive context loading
- **Work-Knowledge Disconnect**: Traditional tools separate project management from knowledge management

PWKM solves these problems through a hub-and-spoke architecture with Notion as the single source of truth and Claude as an intelligent collaborator.

## Key Principles

1. **Single Source of Truth**: Notion is authoritative; chat history is secondary
2. **Hub-and-Spoke Architecture**: Central hub connects specialized components
3. **Tiered Protocol Loading**: Load only what's needed for each session type
4. **Integration Over Automation**: Structure for collaboration, not replacement of thought
5. **Work and Knowledge as Inseparable**: Projects generate knowledge; knowledge informs projects

## Prerequisites

- **Windows 11** with administrator access
- **Claude Desktop** application with MCP support
- **Python 3.10+**
- **Notion account** (free tier works)
- **Claude Pro or Team account**

### Required MCP Servers

- Notion MCP
- Filesystem MCP
- Windows MCP
- Google Calendar MCP

## Getting Started

1. Read [docs/pwkm-system-documentation.md](docs/pwkm-system-documentation.md) for the complete system overview
2. Follow [docs/setup-guide.md](docs/setup-guide.md) for installation
3. Import the Notion templates from the `notion/` directory
4. Configure Claude Desktop using examples in `claude-desktop/`
5. Start your first PWKM session!

## Repository Structure

```
pwkm/
├── docs/                    # Documentation
│   ├── pwkm-system-documentation.md  # Comprehensive guide
│   ├── setup-guide.md       # Installation instructions
│   ├── usage-guide.md       # Daily workflows
│   └── customization.md     # Adapting to your needs
├── scripts/                 # Python utilities
├── claude-desktop/          # Claude Desktop configuration
├── notion/                  # Notion templates (Markdown export)
├── protocols/               # Protocol documents for Claude
└── examples/                # Example sessions and workflows
```

## Related

This repository is the practical companion to the essay "Love Me, Love My AI" which argues *why* employers should embrace personal AI systems. This repo provides *how* to build one.

## License

- **Code and Scripts**: Custom license for personal and internal business use
- **Documentation and Templates**: CC BY-NC-ND 4.0

See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md) for details.

## Author

Keith Mann

For commercial licensing inquiries: keith@keithmann.com
