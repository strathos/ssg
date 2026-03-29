import tempfile
import unittest
from pathlib import Path

from main import generate_page, generate_pages_recursive


class TestGeneratePage(unittest.TestCase):
    def test_generate_page(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            markdown_path = temp_path / "index.md"
            template_path = temp_path / "template.html"
            dest_path = temp_path / "docs" / "index.html"

            markdown_path.write_text(
                '# Hello World\n\nThis is a **test** page. [Home](/)',
                encoding="utf-8",
            )
            template_path.write_text(
                (
                    "<html><head><title>{{ Title }}</title></head>"
                    '<body><img src="/logo.png" />{{ Content }}</body></html>'
                ),
                encoding="utf-8",
            )

            generate_page(markdown_path, template_path, dest_path, "/repo/")

            self.assertEqual(
                dest_path.read_text(encoding="utf-8"),
                (
                    "<html><head><title>Hello World</title></head>"
                    '<body><img src="/repo/logo.png" /><div><h1>Hello World</h1>'
                    '<p>This is a <b>test</b> page. <a href="/repo/">Home</a>'
                    "</p></div></body></html>"
                ),
            )

    def test_generate_pages_recursive(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            content_dir = temp_path / "content"
            template_path = temp_path / "template.html"
            dest_dir = temp_path / "docs"

            (content_dir / "blog" / "post").mkdir(parents=True)
            (content_dir / "index.md").write_text("# Home\n\nHome page.", encoding="utf-8")
            (content_dir / "blog" / "post" / "index.md").write_text(
                "# Blog Post\n\nNested page.",
                encoding="utf-8",
            )
            template_path.write_text(
                (
                    "<html><head><title>{{ Title }}</title></head>"
                    "<body>{{ Content }}</body></html>"
                ),
                encoding="utf-8",
            )

            generate_pages_recursive(content_dir, template_path, dest_dir, "/")

            self.assertTrue((dest_dir / "index.html").exists())
            self.assertTrue((dest_dir / "blog" / "post" / "index.html").exists())


if __name__ == "__main__":
    unittest.main()
