# Langfuse Integration Idea

*Saved from brainstorming session - 2026-01-29*

## Context

Adding an AI observability/error analysis service to the API toolkit using Langfuse.

## The Workflow (from idea.md)

1. **Collect traces** - Gather 100+ diverse traces from production or synthetic usage
2. **Annotate traces** ("open coding") - Review each trace, write brief notes on problems (hallucinated fact, misread user's name, failed tool call)
3. **Group and categorize** - Cluster similar notes (tone violation, failed tool call) - LLM can help
4. **Prioritize** - Count frequency of each category to inform priority
5. **Learn** - Keep looking at data until "theoretical saturation" (not learning anything new)

## Why Langfuse

- Open-source, self-hostable
- LLM-specific tracing with good Claude/OpenAI support
- Solid API for pulling traces programmatically
- Supports annotations/scores

## Implementation Direction

Would live in `services/langfuse/api.py` following the existing service pattern.

Goal: Make observability "default" for new projects - each project imports and configures when needed (like Supabase today).

## Next Steps

- [ ] Evaluate Langfuse API capabilities
- [ ] Design LangfuseAPI service class
- [ ] Create instrumentation helpers for common patterns
- [ ] Build analysis tools for the annotate → group → prioritize workflow
