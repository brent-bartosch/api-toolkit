#!/usr/bin/env python3
"""
sync.py — Propagate MCP server configs from manifest.json to each tool's native format.

Reads:  mcp-servers/manifest.json (canonical source of truth)
Writes:
  - ~/.hermes/config.yaml  (mcp_servers section — via `hermes mcp add/remove`)
  - ~/.claude/mcp.json     (global, mcpServers key)
  - ~/.codex/config.toml   ([mcp_servers.*] sections)

Usage:
  python sync.py                    # sync all servers to all tools
  python sync.py --tool hermes      # sync only to Hermes
  python sync.py --tool claude      # sync only to Claude Code
  python sync.py --tool codex       # sync only to Codex
  python sync.py --server playwright # sync only the playwright server
  python sync.py --dry-run          # show what would change without writing
"""

import json
import os
import sys
import argparse
from pathlib import Path

MANIFEST_PATH = Path(__file__).parent / "manifest.json"
HOME = Path.home()


def load_manifest():
    with open(MANIFEST_PATH) as f:
        return json.load(f)


def expand_path(p):
    """Expand ~ in paths."""
    if isinstance(p, str):
        return p.replace("~", str(HOME))
    if isinstance(p, list):
        return [expand_path(x) for x in p]
    return p


def sync_hermes(manifest, servers_to_sync, dry_run=False):
    """Sync to Hermes via `hermes mcp add` / `hermes mcp remove` CLI."""
    print("\n── Hermes (~/.hermes/config.yaml) ──")
    servers = manifest["servers"]

    # Get currently configured servers
    result = os.popen("hermes mcp list 2>/dev/null").read()
    existing = set()
    for line in result.split("\n"):
        line = line.strip()
        if line and not line.startswith("Name") and not line.startswith("─"):
            parts = line.split()
            if parts:
                existing.add(parts[0])

    for name in servers_to_sync:
        if name not in servers:
            print(f"  ⚠ {name}: not in manifest, skipping")
            continue

        srv = servers[name]
        cmd = srv["command"]
        args = expand_path(srv["args"])

        if name in existing:
            # Remove and re-add to ensure config matches manifest
            if not dry_run:
                os.system(f"hermes mcp remove {name} 2>/dev/null")
            print(f"  ♻ {name}: updating (remove + re-add)")

        # Build the hermes mcp add command
        args_str = " ".join(args)
        env_flags = ""
        for k, v in srv.get("env", {}).items():
            env_flags += f" --env {k}={v}"

        add_cmd = f"echo 'Y' | hermes mcp add {name} --command {cmd} --args {args_str}{env_flags}"

        if dry_run:
            print(f"  → [DRY RUN] {add_cmd}")
        else:
            result = os.system(add_cmd + " 2>&1")
            if result == 0:
                print(f"  ✓ {name}: synced")
            else:
                print(f"  ✗ {name}: sync failed (exit {result})")

    print()


def sync_claude(manifest, servers_to_sync, dry_run=False):
    """Sync to Claude Code global config at ~/.claude/mcp.json."""
    print("\n── Claude Code (~/.claude/mcp.json) ──")
    config_path = HOME / ".claude" / "mcp.json"

    # Load existing or create new
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
    else:
        config = {"mcpServers": {}}

    if "mcpServers" not in config:
        config["mcpServers"] = {}

    servers = manifest["servers"]
    changed = False

    for name in servers_to_sync:
        if name not in servers:
            print(f"  ⚠ {name}: not in manifest, skipping")
            continue

        srv = servers[name]
        entry = {
            "command": srv["command"],
            "args": expand_path(srv["args"]),
            "env": srv.get("env", {}),
        }
        if "timeout" in srv:
            entry["timeout"] = srv["timeout"]

        existing = config["mcpServers"].get(name)
        if existing != entry:
            config["mcpServers"][name] = entry
            changed = True
            action = "would update" if dry_run else "updated"
            print(f"  ✓ {name}: {action}")
        else:
            print(f"  = {name}: already in sync")

    if changed and not dry_run:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        print(f"  → Wrote {config_path}")
    elif dry_run and changed:
        print(f"  → [DRY RUN] Would write {config_path}")
    else:
        print("  → No changes needed")

    print()


def sync_codex(manifest, servers_to_sync, dry_run=False):
    """Sync to Codex config at ~/.codex/config.toml."""
    print("\n── Codex (~/.codex/config.toml) ──")
    config_path = HOME / ".codex" / "config.toml"

    if not config_path.exists():
        print(f"  ✗ {config_path} not found — Codex not installed?")
        return

    # Read existing config
    with open(config_path) as f:
        content = f.read()

    servers = manifest["servers"]

    for name in servers_to_sync:
        if name not in servers:
            print(f"  ⚠ {name}: not in manifest, skipping")
            continue

        srv = servers[name]
        cmd = srv["command"]
        args = expand_path(srv["args"])
        env = srv.get("env", {})

        # Check if already exists in TOML
        section = f"[mcp_servers.{name}]"
        if section in content:
            # Remove existing section and re-add
            lines = content.split("\n")
            new_lines = []
            skip = False
            for line in lines:
                if line.strip() == section:
                    skip = True
                    continue
                if skip and line.strip().startswith("[") and not line.strip() == section:
                    skip = False
                if not skip:
                    new_lines.append(line)
            content = "\n".join(new_lines).rstrip() + "\n"

        # Build TOML section
        toml_section = f"\n[mcp_servers.{name}]\n"
        toml_section += f'command = "{cmd}"\n'
        if args:
            toml_args = ", ".join(f'"{a}"' for a in args)
            toml_section += f"args = [{toml_args}]\n"
        else:
            toml_section += "args = []\n"

        if env:
            toml_section += "\n[mcp_servers.%s.env]\n" % name
            for k, v in env.items():
                toml_section += f'{k} = "{v}"\n'

        action = "would add" if dry_run else "added"
        print(f"  ✓ {name}: {action}")

        if not dry_run:
            content = content.rstrip() + "\n" + toml_section

    if not dry_run:
        with open(config_path, "w") as f:
            f.write(content)
        print(f"  → Wrote {config_path}")
    else:
        print(f"  → [DRY RUN] Would write {config_path}")

    print()


def main():
    parser = argparse.ArgumentParser(description="Sync MCP server configs from manifest.json to all agent tools")
    parser.add_argument("--tool", choices=["hermes", "claude", "codex"], help="Sync only to specific tool")
    parser.add_argument("--server", help="Sync only specific server(s), comma-separated")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    args = parser.parse_args()

    manifest = load_manifest()
    all_servers = list(manifest["servers"].keys())

    if args.server:
        servers_to_sync = [s.strip() for s in args.server.split(",")]
    else:
        servers_to_sync = all_servers

    print(f"Manifest: {MANIFEST_PATH}")
    print(f"Servers to sync: {', '.join(servers_to_sync)}")
    if args.dry_run:
        print("Mode: DRY RUN (no changes written)")

    tools = [args.tool] if args.tool else ["hermes", "claude", "codex"]

    for tool in tools:
        if tool == "hermes":
            sync_hermes(manifest, servers_to_sync, args.dry_run)
        elif tool == "claude":
            sync_claude(manifest, servers_to_sync, args.dry_run)
        elif tool == "codex":
            sync_codex(manifest, servers_to_sync, args.dry_run)

    print("── Done ──")
    print("\nNext steps:")
    print("  • Hermes:    /reset or relaunch to load new MCP tools")
    print("  • Claude:    Restart Claude Code to load ~/.claude/mcp.json")
    print("  • Codex:     Restart Codex to reload config.toml")
    print("  • Log in to browser-only destinations once — session persists in ~/.hermes/browser-profiles/playwright")


if __name__ == "__main__":
    main()
