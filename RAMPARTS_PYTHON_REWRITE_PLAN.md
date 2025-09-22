# RAMPARTS Python Rewrite Plan

**Date**: 2025-09-22
**Author**: Claude (AI Assistant)
**Status**: Comprehensive Technical Plan

## Executive Summary

This document outlines a complete rewrite of Ramparts from Rust to Python, replacing the broken rmcp library with FastMCP and utilizing yara-python for security scanning. The Python implementation will be more maintainable, easier to deploy, and immediately functional compared to the current blocked Rust implementation.

## 🎯 Strategic Advantages of Python Rewrite

### Why Python Over Rust

1. **Working MCP Library**: FastMCP is battle-tested and actively maintained, unlike rmcp which is fundamentally broken
2. **Rapid Development**: Python's development velocity is 3-5x faster than Rust for this use case
3. **Ecosystem Maturity**: Rich ecosystem of security tools, MCP libraries, and deployment options
4. **Community Support**: Larger contributor pool and easier onboarding for new developers
5. **Deployment Flexibility**: Simpler Docker images, native package managers (pip), and cloud deployment
6. **Testing Infrastructure**: Already have working FastMCP test harness in `test_harness/`

### Technical Benefits

- **No Compilation**: Immediate feedback loop during development
- **Dynamic Typing**: Faster prototyping of security rules and patterns
- **Native JSON**: Direct JSON manipulation without serde complexity
- **Async Support**: Modern Python async/await matches Rust tokio capabilities
- **Cross-Platform**: Python runs everywhere without complex cross-compilation

## 📦 Core Dependencies

### Primary Libraries

| Rust Library | Python Replacement | Purpose | Status |
|-------------|-------------------|---------|---------|
| rmcp v0.6.4 | fastmcp >= 2.0 | MCP client/server | ✅ Proven working |
| yara-x | yara-python >= 4.5.4 | YARA rule scanning | ✅ Mature library |
| reqwest | httpx/aiohttp | Async HTTP client | ✅ Production ready |
| tokio | asyncio | Async runtime | ✅ Built-in |
| clap | click/typer | CLI framework | ✅ Excellent |
| axum | fastapi/starlette | Web framework | ✅ Industry standard |
| serde_json | json (built-in) | JSON handling | ✅ Native |
| tracing | logging/structlog | Structured logging | ✅ Comprehensive |

### Additional Python Libraries

```toml
# pyproject.toml dependencies
[tool.poetry.dependencies]
python = "^3.10"
fastmcp = "^2.0"
yara-python = "^4.5.4"
httpx = "^0.27.0"
typer = "^0.12.0"
fastapi = "^0.115.0"
uvicorn = "^0.30.0"
pydantic = "^2.9.0"
rich = "^13.7.0"  # Beautiful CLI output
aiofiles = "^24.1.0"
pyyaml = "^6.0.1"
python-dotenv = "^1.0.0"
structlog = "^25.2.0"
jinja2 = "^3.1.0"  # Report templating
aiohttp-sse-client = "^0.3.0"  # SSE client
psutil = "^6.0.0"  # Process monitoring
```

## 🏗️ Architecture Design

### Project Structure

```
ramparts-python/
├── pyproject.toml                 # Poetry configuration
├── README.md
├── LICENSE
├── Makefile                        # Build/test automation
├── Dockerfile                      # Multi-stage Docker build
├── docker-compose.yml
├── .env.example
│
├── ramparts/                       # Main package
│   ├── __init__.py
│   ├── __main__.py                # Entry point
│   ├── cli.py                     # CLI interface (typer)
│   ├── config.py                  # Configuration management
│   ├── constants.py               # Constants and enums
│   ├── version.py                 # Version info
│   │
│   ├── scanner/                   # Core scanning module
│   │   ├── __init__.py
│   │   ├── core.py                # MCPScannerCore port
│   │   ├── client.py              # MCP client implementation
│   │   ├── transports.py          # Transport handlers
│   │   ├── discovery.py           # IDE config discovery
│   │   └── cache.py               # Result caching
│   │
│   ├── security/                  # Security analysis
│   │   ├── __init__.py
│   │   ├── yara_scanner.py        # YARA rule engine
│   │   ├── llm_assessor.py        # LLM security assessment
│   │   ├── cross_origin.py        # Cross-origin analysis
│   │   ├── vulnerability.py       # Vulnerability detection
│   │   └── risk_scoring.py        # Risk assessment
│   │
│   ├── mcp_server/                # MCP server implementation
│   │   ├── __init__.py
│   │   ├── server.py              # FastMCP server
│   │   ├── tools.py               # Tool implementations
│   │   ├── resources.py           # Resource handlers
│   │   └── prompts.py             # Prompt definitions
│   │
│   ├── web_server/                # HTTP microservice
│   │   ├── __init__.py
│   │   ├── app.py                 # FastAPI application
│   │   ├── routes.py              # API endpoints
│   │   ├── models.py              # Pydantic models
│   │   └── websockets.py          # Real-time updates
│   │
│   ├── reporting/                 # Report generation
│   │   ├── __init__.py
│   │   ├── markdown.py            # Markdown reports
│   │   ├── json_output.py        # JSON formatting
│   │   ├── table.py               # Table formatting
│   │   └── templates/             # Jinja2 templates
│   │
│   └── utils/                     # Utilities
│       ├── __init__.py
│       ├── logging.py             # Logging setup
│       ├── banner.py              # ASCII banner
│       ├── colors.py              # Terminal colors
│       └── validators.py          # Input validation
│
├── rules/                          # YARA rules (unchanged)
│   └── pre/
│       ├── sql_injection.yar
│       ├── command_injection.yar
│       ├── path_traversal.yar
│       ├── secrets_leakage.yar
│       ├── cross_origin_escalation.yar
│       └── mcp_config_risk.yar
│
├── tests/                          # Test suite
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures
│   ├── test_scanner.py
│   ├── test_security.py
│   ├── test_mcp_server.py
│   ├── test_web_server.py
│   ├── integration/
│   │   └── test_end_to_end.py
│   └── fixtures/                  # Test data
│
└── scripts/                        # Utility scripts
    ├── migrate_config.py          # Migrate Rust config
    ├── validate_rules.py          # Validate YARA rules
    └── build_docker.sh            # Docker build script
```

## 🔄 Migration Strategy

### Phase 1: Core Scanner (Week 1)
**Goal**: Replicate basic scanning functionality

1. **Set up project structure**
   - Initialize Poetry project
   - Configure development environment
   - Set up testing framework
   - Create Docker development container

2. **Implement scanner core**
   ```python
   # ramparts/scanner/core.py
   class MCPScannerCore:
       """Core scanning engine using FastMCP client"""

       def __init__(self, config: ScannerConfig):
           self.config = config
           self.cache = ScanCache()
           self.yara_engine = YaraEngine()

       async def scan(self, url: str, options: ScanOptions) -> ScanResult:
           """Scan an MCP server"""
           async with Client(url) as client:
               # Initialize connection
               server_info = await client.initialize()

               # Discover capabilities
               tools = await client.list_tools()
               resources = await client.list_resources()
               prompts = await client.list_prompts()

               # Run security analysis
               vulnerabilities = await self.analyze_security(
                   tools, resources, prompts
               )

               return ScanResult(
                   server_info=server_info,
                   tools=tools,
                   resources=resources,
                   prompts=prompts,
                   vulnerabilities=vulnerabilities
               )
   ```

3. **Port transport handlers**
   - HTTP/HTTPS support
   - SSE client implementation
   - stdio subprocess handling
   - Transport auto-detection

### Phase 2: Security Analysis (Week 1-2)
**Goal**: Implement YARA scanning and vulnerability detection

1. **YARA integration**
   ```python
   # ramparts/security/yara_scanner.py
   import yara
   from pathlib import Path

   class YaraEngine:
       """YARA-based security scanner"""

       def __init__(self, rules_dir: Path = Path("rules/pre")):
           self.rules = self._compile_rules(rules_dir)

       def _compile_rules(self, rules_dir: Path) -> dict:
           """Compile all YARA rules"""
           compiled = {}
           for rule_file in rules_dir.glob("*.yar"):
               namespace = rule_file.stem
               compiled[namespace] = yara.compile(filepath=str(rule_file))
           return compiled

       def scan_content(self, content: str) -> list[YaraMatch]:
           """Scan content against all rules"""
           matches = []
           for namespace, rules in self.rules.items():
               for match in rules.match(data=content):
                   matches.append(YaraMatch(
                       rule=match.rule,
                       namespace=namespace,
                       severity=self._get_severity(match),
                       strings=match.strings
                   ))
           return matches
   ```

2. **LLM assessment integration**
   - Port prompt templates
   - Implement batched assessment
   - Add fallback for API failures

3. **Risk scoring system**
   - CRITICAL/HIGH/MEDIUM/LOW classification
   - Aggregate scoring algorithm
   - Configurable thresholds

### Phase 3: MCP Server Mode (Week 2)
**Goal**: Ramparts as a working MCP server

1. **FastMCP server implementation**
   ```python
   # ramparts/mcp_server/server.py
   from fastmcp import FastMCP

   mcp = FastMCP(
       name="Ramparts Security Scanner",
       version="1.0.0"
   )

   @mcp.tool(
       name="scan",
       description="Scan an MCP server for security vulnerabilities"
   )
   async def scan_tool(url: str, detailed: bool = False) -> dict:
       """Scan MCP server tool"""
       scanner = MCPScannerCore()
       result = await scanner.scan(url, ScanOptions(detailed=detailed))
       return result.to_dict()

   @mcp.tool(
       name="scan_config",
       description="Scan MCP servers from IDE configurations"
   )
   async def scan_config_tool(ide: str = "all") -> dict:
       """Scan IDE configurations"""
       configs = await discover_ide_configs(ide)
       results = {}
       for name, config in configs.items():
           results[name] = await scan_tool(config.url)
       return results

   def run_stdio():
       """Run as stdio MCP server"""
       mcp.run(transport="stdio")

   def run_sse(host: str = "0.0.0.0", port: int = 8000):
       """Run as SSE server"""
       mcp.run(transport="sse", host=host, port=port)
   ```

2. **Tool registration**
   - health check
   - scan
   - scan_config
   - refresh_tools
   - increment_counter (for testing)

3. **Resource exposure**
   - Scan results cache
   - YARA rule definitions
   - Configuration status

### Phase 4: Web Microservice (Week 2-3)
**Goal**: HTTP API for continuous monitoring

1. **FastAPI implementation**
   ```python
   # ramparts/web_server/app.py
   from fastapi import FastAPI, WebSocket
   from fastapi.middleware.cors import CORSMiddleware

   app = FastAPI(title="Ramparts Security Scanner")

   @app.post("/api/scan")
   async def scan_endpoint(request: ScanRequest) -> ScanResponse:
       """Scan an MCP server"""
       scanner = get_scanner()
       result = await scanner.scan(request.url, request.options)
       return ScanResponse(result=result)

   @app.websocket("/ws/scan/{scan_id}")
   async def scan_websocket(websocket: WebSocket, scan_id: str):
       """Real-time scan updates via WebSocket"""
       await websocket.accept()
       async for update in scan_progress(scan_id):
           await websocket.send_json(update)
   ```

2. **API endpoints**
   - POST /api/scan - Single scan
   - GET /api/scan/{id} - Get scan result
   - POST /api/batch - Batch scanning
   - GET /api/health - Health check
   - WebSocket /ws/scan - Real-time updates

3. **Background tasks**
   - Scheduled scanning
   - Result persistence
   - Alert notifications

### Phase 5: CLI Interface (Week 3)
**Goal**: Feature-complete CLI

1. **Typer CLI implementation**
   ```python
   # ramparts/cli.py
   import typer
   from rich.console import Console
   from rich.table import Table

   app = typer.Typer(
       name="ramparts",
       help="Security scanner for MCP servers"
   )

   @app.command()
   def scan(
       url: str,
       auth_headers: list[str] = typer.Option(None),
       format: str = typer.Option("table"),
       report: bool = typer.Option(False),
       verbose: bool = typer.Option(False)
   ):
       """Scan a single MCP server"""
       if verbose:
           setup_verbose_logging()

       scanner = MCPScannerCore()
       with console.status(f"Scanning {url}..."):
           result = asyncio.run(scanner.scan(url))

       # Output formatting
       if format == "json":
           console.print_json(result.to_json())
       elif format == "table":
           display_table(result)

       if report:
           generate_report(result)

   @app.command()
   def server(
       port: int = typer.Option(3000),
       host: str = typer.Option("0.0.0.0")
   ):
       """Start HTTP microservice"""
       uvicorn.run(app, host=host, port=port)

   @app.command()
   def mcp_stdio():
       """Run as MCP server over stdio"""
       from ramparts.mcp_server import run_stdio
       run_stdio()
   ```

2. **Rich terminal output**
   - Colored severity levels
   - Progress bars
   - Interactive tables
   - ASCII banner

### Phase 6: Testing & Documentation (Week 3-4)
**Goal**: Comprehensive testing and documentation

1. **Test suite**
   - Unit tests (pytest)
   - Integration tests
   - FastMCP mock servers
   - YARA rule validation
   - End-to-end scenarios

2. **Documentation**
   - API documentation (auto-generated)
   - User guide
   - Security researcher guide
   - Docker deployment guide
   - Migration from Rust guide

## 🐳 Docker Strategy

### Multi-stage Dockerfile

```dockerfile
# Stage 1: Build environment
FROM python:3.11-slim as builder

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

# Stage 2: Runtime
FROM python:3.11-slim

# Install YARA
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libssl3 libmagic1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application
COPY ramparts/ ./ramparts/
COPY rules/ ./rules/

# Create non-root user
RUN useradd -m -u 1001 ramparts && \
    chown -R ramparts:ramparts /app

USER ramparts

# Default: stdio MCP server
ENTRYPOINT ["python", "-m", "ramparts"]
CMD ["mcp-stdio"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  ramparts-mcp:
    build: .
    image: ramparts-python:latest
    command: mcp-stdio
    stdin_open: true
    tty: true

  ramparts-web:
    build: .
    image: ramparts-python:latest
    command: server --port 8080
    ports:
      - "8080:8080"
    environment:
      - RAMPARTS_CONFIG=/app/config.yaml
    volumes:
      - ./config.yaml:/app/config.yaml:ro

  ramparts-sse:
    build: .
    image: ramparts-python:latest
    command: mcp-sse --port 8000
    ports:
      - "8000:8000"
```

## 🚀 Performance Optimizations

### Python-Specific Optimizations

1. **Async Everything**
   - Use aiohttp/httpx for concurrent requests
   - Batch YARA scanning with asyncio
   - Stream processing for large responses

2. **Caching Strategy**
   - LRU cache for compiled YARA rules
   - Redis/in-memory result caching
   - Connection pooling

3. **Process Management**
   - Use multiprocessing for CPU-bound YARA scanning
   - Thread pool for I/O operations
   - Uvloop for faster async

4. **Memory Management**
   - Generator-based streaming
   - Lazy loading of YARA rules
   - Structured logging with minimal overhead

## 📊 Comparison Matrix

| Feature | Rust (Current) | Python (Proposed) | Advantage |
|---------|---------------|-------------------|-----------|
| MCP Server | ❌ Broken | ✅ Working | Python |
| Development Speed | Slow | Fast | Python |
| Deployment | Complex | Simple | Python |
| Testing | Difficult | Easy | Python |
| Community | Small | Large | Python |
| Performance | Fast* | Good | Rust* |
| Memory Usage | Low* | Higher | Rust* |
| Type Safety | Strong | Runtime | Rust |

*Theoretical - Rust version doesn't actually work

## 🎯 Success Metrics

### Week 1 Deliverables
- [ ] Basic scanning working with FastMCP
- [ ] YARA rules integrated
- [ ] CLI with scan command
- [ ] Docker image builds

### Week 2 Deliverables
- [ ] MCP server mode working (stdio/SSE)
- [ ] All 5 tools exposed
- [ ] Web API operational
- [ ] Integration tests passing

### Week 3 Deliverables
- [ ] Feature parity with Rust design
- [ ] Performance optimization
- [ ] Documentation complete
- [ ] Production Docker images

### Week 4 Deliverables
- [ ] Full test coverage (>80%)
- [ ] Performance benchmarks
- [ ] Security audit
- [ ] Release v1.0.0

## 🔥 Risk Mitigation

### Technical Risks

1. **YARA Performance**
   - Mitigation: Pre-compile rules, use multiprocessing
   - Fallback: Optional YARA with graceful degradation

2. **Async Complexity**
   - Mitigation: Use battle-tested patterns from FastMCP
   - Fallback: Sync fallbacks for critical paths

3. **Memory Usage**
   - Mitigation: Streaming, generators, bounded queues
   - Fallback: Configurable limits and warnings

### Migration Risks

1. **Feature Gaps**
   - Mitigation: Incremental migration, feature flags
   - Fallback: Keep Rust code as reference

2. **User Disruption**
   - Mitigation: Docker images for both versions
   - Fallback: Parallel maintenance period

## 💡 Key Advantages Over Rust

1. **Immediate Functionality**: FastMCP works today, rmcp is permanently broken
2. **Developer Velocity**: 10x faster iteration cycles
3. **Ecosystem**: Thousands of security libraries available
4. **Deployment**: pip install ramparts vs complex Rust builds
5. **Maintenance**: Python easier to maintain and extend
6. **Testing**: Existing FastMCP test harness ready to use
7. **Documentation**: Auto-generated from docstrings
8. **Cloud Native**: Easy Lambda/Functions deployment

## 📅 Implementation Timeline

### Week 1 (Days 1-7)
- Days 1-2: Project setup, dependencies, structure
- Days 3-4: Core scanner, MCP client implementation
- Days 5-6: YARA integration, basic CLI
- Day 7: Testing, Docker setup

### Week 2 (Days 8-14)
- Days 8-9: MCP server mode (FastMCP)
- Days 10-11: Security analysis, LLM integration
- Days 12-13: Web microservice (FastAPI)
- Day 14: Integration testing

### Week 3 (Days 15-21)
- Days 15-16: CLI completion (all commands)
- Days 17-18: Reporting system
- Days 19-20: Performance optimization
- Day 21: Documentation

### Week 4 (Days 22-28)
- Days 22-23: Comprehensive testing
- Days 24-25: Security audit, hardening
- Days 26-27: Deployment preparation
- Day 28: Release v1.0.0

## 🎉 Conclusion

The Python rewrite of Ramparts is not just a workaround for the broken rmcp library - it's a strategic improvement that will result in a more maintainable, deployable, and extensible security scanner. With FastMCP's proven functionality and Python's rich ecosystem, we can deliver a working product in weeks rather than being indefinitely blocked.

The existing test infrastructure in `test_harness/` already uses FastMCP, proving the approach works. This rewrite turns a critical blocker into an opportunity for a better implementation.

**Recommendation**: Begin immediate implementation focusing on Phase 1 (Core Scanner) to demonstrate early value and validate the approach.

---

*Note: This plan represents approximately 4 weeks of focused development by a single developer familiar with both Python and the MCP protocol. With additional resources or parallel development, this timeline could be significantly reduced.*