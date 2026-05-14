import os
import pytest
from navidoc.parsers.markdown import MarkdownParser

def test_markdown_parser():
    # Create a dummy markdown file in storage
    storage_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../storage'))
    test_dir = os.path.join(storage_dir, 'test_data')
    os.makedirs(test_dir, exist_ok=True)
    
    p = os.path.join(test_dir, "test.md")
    with open(p, 'w', encoding='utf-8') as f:
        f.write("# Header 1\nContent 1\n## Header 2\nContent 2")

    parser = MarkdownParser()
    tree = parser.parse(p)

    assert tree["title"] == "Root"
    assert len(tree["children"]) == 1
    assert tree["children"][0]["title"] == "Header 1"
    assert len(tree["children"][0]["children"]) == 1
    assert tree["children"][0]["children"][0]["title"] == "Header 2"
