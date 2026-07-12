"""Two MCP patterns, one client wiring:
  · mcp_tools   — OUR custom Location Analyzer server (FastMCP on Cloud Run/localhost)
  · star_tools  — Google's MANAGED BigQuery MCP (hosted; OAuth ADC auth) + a local FunctionTool
  · confirm_tools — the deterministic beacon gate (plain code)
"""
