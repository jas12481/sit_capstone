"""
DSL Change Management System for Dify workflow configurations.

Provides governed version control for Dify DSL YAMLs:
- Parse exported YAMLs to extract LLM/code/agent nodes
- Detect changes via SHA256 content hashing
- Generate human-readable diffs
- Route changes through a named-approval workflow (MCP API)
- Commit approved changes to GitHub with full attribution
"""
