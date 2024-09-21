"""
Context7 Usage Examples

This file contains practical examples of using the Context7 API
to fetch real-time documentation for various coding tasks.
"""

from api_toolkit.services.context7.api import Context7API


def example_basic_usage():
    """Basic Context7 API usage."""
    print("=" * 60)
    print("Example 1: Basic Documentation Fetching")
    print("=" * 60)

    api = Context7API()

    # Search for documentation
    print("\n📚 Searching for React hooks documentation...")
    results = api.search("react hooks useState useEffect")

    if results:
        for result in results[:3]:
            print(f"\n- {result.get('title', 'No title')}")
            print(f"  Library: {result.get('library', 'Unknown')}")
            print(f"  Description: {result.get('description', 'N/A')[:100]}...")

    # Get specific documentation
    print("\n📖 Fetching React hooks documentation...")
    docs = api.get_docs('react', 'hooks')

    if 'content' in docs:
        print(f"Documentation found: {len(docs['content'])} characters")
        print(f"First 200 chars: {docs['content'][:200]}...")

    return api


def example_code_generation_context():
    """Using Context7 for AI-assisted code generation."""
    print("=" * 60)
    print("Example 2: AI Code Generation Context")
    print("=" * 60)

    api = Context7API()

    # Get context for a specific coding task
    prompt = "Create a Next.js middleware that checks for a valid JWT token in cookies"

    print(f"\n🤖 Getting context for: {prompt}")
    context = api.get_context(prompt, libraries=['nextjs', 'jose'])

    if 'documentation' in context:
        print("\n📚 Relevant Documentation Found:")
        print(context['documentation'][:500] + "...")

    if 'examples' in context:
        print("\n💻 Code Examples:")
        for idx, example in enumerate(context['examples'][:2], 1):
            print(f"\nExample {idx}: {example.get('title', 'Untitled')}")
            print(example.get('code', 'No code')[:300] + "...")

    return context


def example_fetch_examples():
    """Fetching code examples for specific libraries."""
    print("=" * 60)
    print("Example 3: Fetching Library Examples")
    print("=" * 60)

    api = Context7API()

    libraries = ['react', 'nextjs', 'tailwindcss']

    for library in libraries:
        print(f"\n🔍 Examples for {library}:")
        examples = api.get_examples(library, pattern='authentication')

        if examples:
            for ex in examples[:2]:
                print(f"\n  📝 {ex.get('title', 'Example')}")
                print(f"  Description: {ex.get('description', 'N/A')[:100]}...")
                if 'code' in ex:
                    code_preview = ex['code'][:150].replace('\n', '\n    ')
                    print(f"  Code:\n    {code_preview}...")
        else:
            print(f"  No examples found for {library}")


def example_library_discovery():
    """Discovering available libraries."""
    print("=" * 60)
    print("Example 4: Library Discovery")
    print("=" * 60)

    api = Context7API()

    print("\n📚 Available Libraries:")
    libraries = api.list_libraries()

    if libraries:
        # Group by categories (this is hypothetical categorization)
        frontend = [lib for lib in libraries if lib in ['react', 'vue', 'angular', 'svelte']]
        backend = [lib for lib in libraries if lib in ['express', 'fastapi', 'django', 'flask']]
        fullstack = [lib for lib in libraries if lib in ['nextjs', 'nuxt', 'remix']]
        css = [lib for lib in libraries if lib in ['tailwindcss', 'bootstrap', 'sass']]

        if frontend:
            print(f"\n  Frontend: {', '.join(frontend)}")
        if backend:
            print(f"  Backend: {', '.join(backend)}")
        if fullstack:
            print(f"  Fullstack: {', '.join(fullstack)}")
        if css:
            print(f"  CSS/Styling: {', '.join(css)}")

        # Show remaining
        categorized = set(frontend + backend + fullstack + css)
        other = [lib for lib in libraries if lib not in categorized]
        if other:
            print(f"  Other: {', '.join(other[:10])}")
            if len(other) > 10:
                print(f"    ... and {len(other) - 10} more")
    else:
        print("  No libraries found or API not accessible")

    return libraries


def example_documentation_url():
    """Fetching documentation from a specific URL."""
    print("=" * 60)
    print("Example 5: Fetch Documentation from URL")
    print("=" * 60)

    api = Context7API()

    # Example URLs (adjust based on actual needs)
    urls = [
        "https://react.dev/reference/react/useState",
        "https://nextjs.org/docs/app/building-your-application/routing/middleware"
    ]

    for url in urls[:1]:  # Only process first URL for demo
        print(f"\n🔗 Fetching docs from: {url}")
        docs = api.fetch_url_docs(url)

        if 'content' in docs:
            print(f"✅ Documentation fetched: {len(docs['content'])} characters")
            print(f"Preview: {docs['content'][:200]}...")
        elif 'error' in docs:
            print(f"❌ Error: {docs['error']}")


def example_integrated_workflow():
    """Complete workflow integrating Context7 with coding tasks."""
    print("=" * 60)
    print("Example 6: Integrated Coding Workflow")
    print("=" * 60)

    api = Context7API()

    # Step 1: Define the task
    task = "Build a React component with TypeScript that fetches user data and handles loading states"

    print(f"\n🎯 Task: {task}")

    # Step 2: Get contextual documentation
    print("\n📚 Fetching relevant documentation...")
    context = api.get_context(task, libraries=['react', 'typescript'])

    # Step 3: Search for specific patterns
    print("\n🔍 Searching for specific patterns...")
    patterns = [
        "react typescript component props",
        "react useEffect fetch data",
        "react loading state management"
    ]

    for pattern in patterns:
        results = api.search(pattern)
        if results:
            print(f"\n  ✓ {pattern}: Found {len(results)} results")
            best = results[0]
            print(f"    Best match: {best.get('title', 'N/A')}")

    # Step 4: Get specific examples
    print("\n💻 Getting code examples...")
    examples = api.get_examples('react', 'data-fetching')

    if examples:
        print(f"Found {len(examples)} examples")
        for ex in examples[:2]:
            print(f"  - {ex.get('title', 'Example')}")

    # Step 5: Generate documentation-aware response
    print("\n✨ Ready to generate code with up-to-date documentation!")
    print("  - Context loaded from official sources")
    print("  - Examples verified against latest versions")
    print("  - Ready for AI-assisted code generation")

    return {
        'task': task,
        'context': context,
        'examples': examples
    }


def run_all_examples():
    """Run all examples in sequence."""
    examples = [
        ("Basic Usage", example_basic_usage),
        ("AI Code Generation", example_code_generation_context),
        ("Library Examples", example_fetch_examples),
        ("Library Discovery", example_library_discovery),
        ("URL Documentation", example_documentation_url),
        ("Integrated Workflow", example_integrated_workflow)
    ]

    print("\n" + "=" * 60)
    print("CONTEXT7 API EXAMPLES")
    print("=" * 60)

    for name, func in examples:
        print(f"\n🚀 Running: {name}")
        print("-" * 40)
        try:
            func()
        except Exception as e:
            print(f"❌ Error in {name}: {e}")
        print("\n" + "-" * 40)


# CLI interface
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        example_map = {
            'basic': example_basic_usage,
            'context': example_code_generation_context,
            'examples': example_fetch_examples,
            'libraries': example_library_discovery,
            'url': example_documentation_url,
            'workflow': example_integrated_workflow,
            'all': run_all_examples
        }

        example_name = sys.argv[1]
        if example_name in example_map:
            example_map[example_name]()
        else:
            print(f"Unknown example: {example_name}")
            print(f"Available: {', '.join(example_map.keys())}")
    else:
        print("Usage: python examples.py [example_name]")
        print("Examples: basic, context, examples, libraries, url, workflow, all")
        print("\nRunning quick start instead...")
        api = Context7API()
        api.quick_start()