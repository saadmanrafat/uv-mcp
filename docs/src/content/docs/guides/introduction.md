---
title: Introduction
description: Overview of UV-MCP
---

# Introduction

**UV-MCP** is a Model Context Protocol (MCP) server designed to bridge the gap between AI assistants (like Gemini and Claude) and your Python development environment.

It leverages the speed and efficiency of **[uv](https://docs.astral.sh/uv/)**, the extremely fast Python package manager written in Rust.

## Why UV-MCP?

Managing Python environments can be complex. Dependency conflicts, broken virtual environments, and configuration mismatches are common headaches. UV-MCP allows your AI assistant to:

*   **Diagnose** issues automatically.
*   **Repair** broken environments without manual intervention.
*   **Manage** dependencies using natural language.

## Core Capabilities

*   **Environment Health Checks**: Validates `pyproject.toml`, virtualenvs, and lockfiles.
*   **Automated Repairs**: Can initialize projects, create venvs, and sync dependencies.
*   **Dependency Management**: Add or remove packages, including dev dependencies and optional groups.
