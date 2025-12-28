import os
import re
import sys
import pathlib

# Configuration
DOCS_ROOT = pathlib.Path("docs/src/content/docs")
BASE_PATH = "/uv-mcp"
ALLOWED_EXTENSIONS = {".md", ".mdx"}

# Emoji regex (broad range for emojis and symbols, excluding basic ASCII and common Latin supplements)
# Adjusted to exclude Box Drawing (2500-257F) and Block Elements (2580-259F)
EMOJI_PATTERN = re.compile(
    r"["
    r"\U0001F600-\U0001F64F"  # Emoticons
    r"\U0001F300-\U0001F5FF"  # Misc Symbols and Pictographs
    r"\U0001F680-\U0001F6FF"  # Transport and Map
    r"\U0001F1E0-\U0001F1FF"  # Flags (iOS)
    r"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    r"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
    r"\U00002600-\U000026FF"  # Misc Symbols (Warning: includes some math/gender symbols, but mostly emoji-like)
    r"\U00002700-\U000027BF"  # Dingbats
    r"]+", flags=re.UNICODE
)

def find_files(root):
    for path in root.rglob("*"):
        if path.suffix in ALLOWED_EXTENSIONS:
            yield path

def check_emojis(content, file_path):
    issues = []
    for line_num, line in enumerate(content.splitlines(), 1):
        if EMOJI_PATTERN.search(line):
            issues.append(f"Line {line_num}: Emoji detected")
    return issues

def resolve_link(link, current_file):
    # Strip anchor
    url = link.split("#")[0]
    if not url:
        return True # Just an anchor

    # External link
    if url.startswith("http") or url.startswith("mailto:"):
        return True

    # Absolute link (site root)
    if url.startswith(BASE_PATH):
        # /uv-mcp/guides/intro/ -> docs/src/content/docs/guides/intro.md
        rel_path = url[len(BASE_PATH):].strip("/")
    elif url.startswith("/"):
        # Treat as relative to site root if it starts with / but not base path?
        # Starlight usually expects base path if configured.
        # But let's assume it maps to DOCS_ROOT
        rel_path = url.strip("/")
    else:
        # Relative link
        # current_file is .../docs/guides/usage.md
        # link is ../reference/tools
        # resolved is .../docs/reference/tools
        current_dir = current_file.parent
        # resolve_path needs to handle potential navigation up
        # We need to be careful with pathlib resolution of ".." if it goes out of scope?
        # But for checking existence it's fine.
        try:
             resolved_path = (current_dir / url).resolve()
        except Exception:
             return False
        
        try:
            rel_path_from_docs = resolved_path.relative_to(DOCS_ROOT.resolve())
            rel_path = str(rel_path_from_docs)
        except ValueError:
            # Pointing outside docs root?
            return False

    # Check existence
    # Try extensions
    possible_paths = [
        DOCS_ROOT / rel_path,
        DOCS_ROOT / (rel_path + ".md"),
        DOCS_ROOT / (rel_path + ".mdx"),
        DOCS_ROOT / rel_path / "index.md",
        DOCS_ROOT / rel_path / "index.mdx",
    ]
    
    return any(p.exists() for p in possible_paths)

def check_links(content, file_path):
    issues = []
    # Markdown links [text](url)
    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    
    for line_num, line in enumerate(content.splitlines(), 1):
        matches = link_pattern.findall(line)
        for text, link in matches:
            if not resolve_link(link, file_path):
                issues.append(f"Line {line_num}: Broken link '{link}'")
    return issues

def main():
    print(f"Checking documentation in {DOCS_ROOT}...")
    all_passed = True
    
    for file_path in find_files(DOCS_ROOT):
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            all_passed = False
            continue

        emoji_issues = check_emojis(content, file_path)
        link_issues = check_links(content, file_path)
        
        if emoji_issues or link_issues:
            print(f"\nIssues in {file_path}:")
            for issue in emoji_issues:
                print(f"  [Emoji] {issue}")
            for issue in link_issues:
                print(f"  [Link]  {issue}")
            all_passed = False
            
    if all_passed:
        print("\n All checks passed!")
        sys.exit(0)
    else:
        print("\n Checks failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
