import unittest

from textnode import (
    block_to_block_type,
    extract_title,
    markdown_to_html_node,
    markdown_to_blocks,
    BlockType,
    TextNode,
    TextType,
    extract_markdown_images,
    extract_markdown_links,
    split_nodes_image,
    split_nodes_link,
    split_nodes_delimiter,
    text_to_textnodes,
    text_node_to_html_node,
)


class TestTextNode(unittest.TestCase):
    def test_eq(self):
        node = TextNode("This is a text node", TextType.BOLD)
        node2 = TextNode("This is a text node", TextType.BOLD)
        self.assertEqual(node, node2)

    def test_eq_with_none_url(self):
        node = TextNode("A plain node", TextType.PLAIN, None)
        node2 = TextNode("A plain node", TextType.PLAIN, None)
        self.assertEqual(node, node2)

    def test_not_eq_different_text_type(self):
        node = TextNode("Same text", TextType.PLAIN)
        node2 = TextNode("Same text", TextType.BOLD)
        self.assertNotEqual(node, node2)

    def test_not_eq_different_url(self):
        node = TextNode("A link", TextType.LINK, "https://example.com")
        node2 = TextNode("A link", TextType.LINK, None)
        self.assertNotEqual(node, node2)

    def test_not_eq_different_text(self):
        node = TextNode("First text", TextType.ITALIC)
        node2 = TextNode("Second text", TextType.ITALIC)
        self.assertNotEqual(node, node2)


class TestTextNodeToHTMLNode(unittest.TestCase):
    def test_text(self):
        node = TextNode("This is a text node", TextType.TEXT)
        html_node = text_node_to_html_node(node)
        self.assertEqual(html_node.tag, None)
        self.assertEqual(html_node.value, "This is a text node")

    def test_bold(self):
        node = TextNode("Bold text", TextType.BOLD)
        html_node = text_node_to_html_node(node)
        self.assertEqual(html_node.tag, "b")
        self.assertEqual(html_node.value, "Bold text")
        self.assertEqual(html_node.props, None)

    def test_italic(self):
        node = TextNode("Italic text", TextType.ITALIC)
        html_node = text_node_to_html_node(node)
        self.assertEqual(html_node.tag, "i")
        self.assertEqual(html_node.value, "Italic text")
        self.assertEqual(html_node.props, None)

    def test_code(self):
        node = TextNode("print('hi')", TextType.CODE)
        html_node = text_node_to_html_node(node)
        self.assertEqual(html_node.tag, "code")
        self.assertEqual(html_node.value, "print('hi')")
        self.assertEqual(html_node.props, None)

    def test_link(self):
        node = TextNode("Boot.dev", TextType.LINK, "https://www.boot.dev")
        html_node = text_node_to_html_node(node)
        self.assertEqual(html_node.tag, "a")
        self.assertEqual(html_node.value, "Boot.dev")
        self.assertEqual(html_node.props, {"href": "https://www.boot.dev"})

    def test_image(self):
        node = TextNode("Alt text", TextType.IMAGE, "https://www.boot.dev/img.png")
        html_node = text_node_to_html_node(node)
        self.assertEqual(html_node.tag, "img")
        self.assertEqual(html_node.value, "")
        self.assertEqual(
            html_node.props,
            {
                "src": "https://www.boot.dev/img.png",
                "alt": "Alt text",
            },
        )

    def test_invalid_text_type_raises(self):
        node = TextNode("text", TextType.TEXT)
        node.text_type = "not-a-text-type"
        with self.assertRaisesRegex(ValueError, "invalid TextType"):
            text_node_to_html_node(node)


class TestSplitNodesDelimiter(unittest.TestCase):
    def test_split_code_delimiter(self):
        node = TextNode("This is text with a `code block` word", TextType.TEXT)
        self.assertEqual(
            split_nodes_delimiter([node], "`", TextType.CODE),
            [
                TextNode("This is text with a ", TextType.TEXT),
                TextNode("code block", TextType.CODE),
                TextNode(" word", TextType.TEXT),
            ],
        )

    def test_split_bold_delimiter(self):
        node = TextNode(
            "This is text with a **bolded phrase** in the middle",
            TextType.TEXT,
        )
        self.assertEqual(
            split_nodes_delimiter([node], "**", TextType.BOLD),
            [
                TextNode("This is text with a ", TextType.TEXT),
                TextNode("bolded phrase", TextType.BOLD),
                TextNode(" in the middle", TextType.TEXT),
            ],
        )

    def test_split_italic_delimiter(self):
        node = TextNode("This is _italic_ text", TextType.TEXT)
        self.assertEqual(
            split_nodes_delimiter([node], "_", TextType.ITALIC),
            [
                TextNode("This is ", TextType.TEXT),
                TextNode("italic", TextType.ITALIC),
                TextNode(" text", TextType.TEXT),
            ],
        )

    def test_split_multiple_delimited_sections(self):
        node = TextNode("Start `code` middle `more code` end", TextType.TEXT)
        self.assertEqual(
            split_nodes_delimiter([node], "`", TextType.CODE),
            [
                TextNode("Start ", TextType.TEXT),
                TextNode("code", TextType.CODE),
                TextNode(" middle ", TextType.TEXT),
                TextNode("more code", TextType.CODE),
                TextNode(" end", TextType.TEXT),
            ],
        )

    def test_split_preserves_non_text_nodes(self):
        nodes = [
            TextNode("prefix ", TextType.TEXT),
            TextNode("already bold", TextType.BOLD),
        ]
        self.assertEqual(
            split_nodes_delimiter(nodes, "**", TextType.BOLD),
            [
                TextNode("prefix ", TextType.TEXT),
                TextNode("already bold", TextType.BOLD),
            ],
        )

    def test_split_multiple_input_nodes(self):
        nodes = [
            TextNode("Alpha **beta**", TextType.TEXT),
            TextNode("gamma", TextType.CODE),
            TextNode(" delta **epsilon** zeta", TextType.TEXT),
        ]
        self.assertEqual(
            split_nodes_delimiter(nodes, "**", TextType.BOLD),
            [
                TextNode("Alpha ", TextType.TEXT),
                TextNode("beta", TextType.BOLD),
                TextNode("gamma", TextType.CODE),
                TextNode(" delta ", TextType.TEXT),
                TextNode("epsilon", TextType.BOLD),
                TextNode(" zeta", TextType.TEXT),
            ],
        )

    def test_split_allows_text_that_is_only_delimited_content(self):
        node = TextNode("`code`", TextType.TEXT)
        self.assertEqual(
            split_nodes_delimiter([node], "`", TextType.CODE),
            [TextNode("code", TextType.CODE)],
        )

    def test_split_raises_when_closing_delimiter_is_missing(self):
        node = TextNode("This is `broken markdown", TextType.TEXT)
        with self.assertRaisesRegex(ValueError, "missing closing delimiter: `"):
            split_nodes_delimiter([node], "`", TextType.CODE)


class TestExtractMarkdown(unittest.TestCase):
    def test_extract_markdown_images(self):
        matches = extract_markdown_images(
            "This is text with an ![image](https://i.imgur.com/zjjcJKZ.png)"
        )
        self.assertListEqual(
            [("image", "https://i.imgur.com/zjjcJKZ.png")],
            matches,
        )

    def test_extract_markdown_images_multiple(self):
        matches = extract_markdown_images(
            "Text ![rick roll](https://i.imgur.com/aKaOqIh.gif) "
            "and ![obi wan](https://i.imgur.com/fJRm4Vk.jpeg)"
        )
        self.assertListEqual(
            [
                ("rick roll", "https://i.imgur.com/aKaOqIh.gif"),
                ("obi wan", "https://i.imgur.com/fJRm4Vk.jpeg"),
            ],
            matches,
        )

    def test_extract_markdown_links(self):
        matches = extract_markdown_links(
            "This is text with a link [to boot dev](https://www.boot.dev)"
        )
        self.assertListEqual(
            [("to boot dev", "https://www.boot.dev")],
            matches,
        )

    def test_extract_markdown_links_multiple(self):
        matches = extract_markdown_links(
            "Links [to boot dev](https://www.boot.dev) and "
            "[to youtube](https://www.youtube.com/@bootdotdev)"
        )
        self.assertListEqual(
            [
                ("to boot dev", "https://www.boot.dev"),
                ("to youtube", "https://www.youtube.com/@bootdotdev"),
            ],
            matches,
        )

    def test_extract_markdown_links_ignores_images(self):
        matches = extract_markdown_links(
            "An image ![alt](https://example.com/image.png) and "
            "a [link](https://example.com)"
        )
        self.assertListEqual(
            [("link", "https://example.com")],
            matches,
        )

    def test_extract_markdown_images_returns_empty_list_when_missing(self):
        matches = extract_markdown_images("This text has no markdown images.")
        self.assertListEqual([], matches)


class TestSplitNodesImage(unittest.TestCase):
    def test_split_images(self):
        node = TextNode(
            "This is text with an ![image](https://i.imgur.com/zjjcJKZ.png) "
            "and another ![second image](https://i.imgur.com/3elNhQu.png)",
            TextType.TEXT,
        )
        new_nodes = split_nodes_image([node])
        self.assertListEqual(
            [
                TextNode("This is text with an ", TextType.TEXT),
                TextNode("image", TextType.IMAGE, "https://i.imgur.com/zjjcJKZ.png"),
                TextNode(" and another ", TextType.TEXT),
                TextNode(
                    "second image",
                    TextType.IMAGE,
                    "https://i.imgur.com/3elNhQu.png",
                ),
            ],
            new_nodes,
        )

    def test_split_image_only_node(self):
        node = TextNode(
            "![image](https://i.imgur.com/zjjcJKZ.png)",
            TextType.TEXT,
        )
        self.assertListEqual(
            [TextNode("image", TextType.IMAGE, "https://i.imgur.com/zjjcJKZ.png")],
            split_nodes_image([node]),
        )

    def test_split_images_preserves_non_text_nodes(self):
        nodes = [
            TextNode("prefix ![image](https://example.com/image.png)", TextType.TEXT),
            TextNode("already bold", TextType.BOLD),
        ]
        self.assertListEqual(
            [
                TextNode("prefix ", TextType.TEXT),
                TextNode("image", TextType.IMAGE, "https://example.com/image.png"),
                TextNode("already bold", TextType.BOLD),
            ],
            split_nodes_image(nodes),
        )

    def test_split_images_returns_original_text_node_when_no_images(self):
        nodes = [TextNode("This has no images", TextType.TEXT)]
        self.assertListEqual(nodes, split_nodes_image(nodes))

    def test_split_images_multiple_input_nodes(self):
        nodes = [
            TextNode("![first](https://example.com/1.png)", TextType.TEXT),
            TextNode("separator", TextType.CODE),
            TextNode("before ![second](https://example.com/2.png) after", TextType.TEXT),
        ]
        self.assertListEqual(
            [
                TextNode("first", TextType.IMAGE, "https://example.com/1.png"),
                TextNode("separator", TextType.CODE),
                TextNode("before ", TextType.TEXT),
                TextNode("second", TextType.IMAGE, "https://example.com/2.png"),
                TextNode(" after", TextType.TEXT),
            ],
            split_nodes_image(nodes),
        )


class TestSplitNodesLink(unittest.TestCase):
    def test_split_links(self):
        node = TextNode(
            "This is text with a link [to boot dev](https://www.boot.dev) "
            "and [to youtube](https://www.youtube.com/@bootdotdev)",
            TextType.TEXT,
        )
        new_nodes = split_nodes_link([node])
        self.assertListEqual(
            [
                TextNode("This is text with a link ", TextType.TEXT),
                TextNode("to boot dev", TextType.LINK, "https://www.boot.dev"),
                TextNode(" and ", TextType.TEXT),
                TextNode(
                    "to youtube",
                    TextType.LINK,
                    "https://www.youtube.com/@bootdotdev",
                ),
            ],
            new_nodes,
        )

    def test_split_link_only_node(self):
        node = TextNode("[boot dev](https://www.boot.dev)", TextType.TEXT)
        self.assertListEqual(
            [TextNode("boot dev", TextType.LINK, "https://www.boot.dev")],
            split_nodes_link([node]),
        )

    def test_split_links_ignores_images(self):
        node = TextNode(
            "![image](https://example.com/image.png) and [link](https://example.com)",
            TextType.TEXT,
        )
        self.assertListEqual(
            [
                TextNode(
                    "![image](https://example.com/image.png) and ",
                    TextType.TEXT,
                ),
                TextNode("link", TextType.LINK, "https://example.com"),
            ],
            split_nodes_link([node]),
        )

    def test_split_links_preserves_non_text_nodes(self):
        nodes = [
            TextNode("[boot dev](https://www.boot.dev)", TextType.TEXT),
            TextNode("raw code", TextType.CODE),
        ]
        self.assertListEqual(
            [
                TextNode("boot dev", TextType.LINK, "https://www.boot.dev"),
                TextNode("raw code", TextType.CODE),
            ],
            split_nodes_link(nodes),
        )

    def test_split_links_returns_original_text_node_when_no_links(self):
        nodes = [TextNode("This has no links", TextType.TEXT)]
        self.assertListEqual(nodes, split_nodes_link(nodes))


class TestTextToTextNodes(unittest.TestCase):
    def test_text_to_textnodes_with_all_supported_markdown(self):
        text = (
            "This is **text** with an _italic_ word and a `code block` and an "
            "![obi wan image](https://i.imgur.com/fJRm4Vk.jpeg) and a "
            "[link](https://boot.dev)"
        )
        self.assertListEqual(
            [
                TextNode("This is ", TextType.TEXT),
                TextNode("text", TextType.BOLD),
                TextNode(" with an ", TextType.TEXT),
                TextNode("italic", TextType.ITALIC),
                TextNode(" word and a ", TextType.TEXT),
                TextNode("code block", TextType.CODE),
                TextNode(" and an ", TextType.TEXT),
                TextNode(
                    "obi wan image",
                    TextType.IMAGE,
                    "https://i.imgur.com/fJRm4Vk.jpeg",
                ),
                TextNode(" and a ", TextType.TEXT),
                TextNode("link", TextType.LINK, "https://boot.dev"),
            ],
            text_to_textnodes(text),
        )


class TestMarkdownToBlocks(unittest.TestCase):
    def test_markdown_to_blocks(self):
        md = """
This is **bolded** paragraph

This is another paragraph with _italic_ text and `code` here
This is the same paragraph on a new line

- This is a list
- with items
"""
        blocks = markdown_to_blocks(md)
        self.assertEqual(
            blocks,
            [
                "This is **bolded** paragraph",
                "This is another paragraph with _italic_ text and `code` here\n"
                "This is the same paragraph on a new line",
                "- This is a list\n- with items",
            ],
        )

    def test_markdown_to_blocks_strips_whitespace_from_each_block(self):
        md = """
  # Heading  

  Paragraph text here.  
"""
        self.assertEqual(
            markdown_to_blocks(md),
            ["# Heading", "Paragraph text here."],
        )

    def test_markdown_to_blocks_removes_empty_blocks(self):
        md = """
First block



Second block


Third block
"""
        self.assertEqual(
            markdown_to_blocks(md),
            ["First block", "Second block", "Third block"],
        )


class TestBlockToBlockType(unittest.TestCase):
    def test_heading_block(self):
        self.assertEqual(
            block_to_block_type("### Heading text"),
            BlockType.HEADING,
        )

    def test_code_block(self):
        self.assertEqual(
            block_to_block_type("```\nprint('hello')\n```"),
            BlockType.CODE,
        )

    def test_quote_block(self):
        self.assertEqual(
            block_to_block_type(">first line\n> second line"),
            BlockType.QUOTE,
        )

    def test_unordered_list_block(self):
        self.assertEqual(
            block_to_block_type("- first item\n- second item\n- third item"),
            BlockType.UNORDERED_LIST,
        )

    def test_ordered_list_block(self):
        self.assertEqual(
            block_to_block_type("1. first item\n2. second item\n3. third item"),
            BlockType.ORDERED_LIST,
        )

    def test_paragraph_block(self):
        self.assertEqual(
            block_to_block_type("This is a normal paragraph."),
            BlockType.PARAGRAPH,
        )

    def test_invalid_heading_without_space_is_paragraph(self):
        self.assertEqual(
            block_to_block_type("##Heading"),
            BlockType.PARAGRAPH,
        )

    def test_invalid_ordered_list_is_paragraph(self):
        self.assertEqual(
            block_to_block_type("1. first item\n3. second item"),
            BlockType.PARAGRAPH,
        )

    def test_mixed_unordered_list_is_paragraph(self):
        self.assertEqual(
            block_to_block_type("- first item\nsecond item"),
            BlockType.PARAGRAPH,
        )

    def test_text_to_textnodes_with_plain_text(self):
        self.assertListEqual(
            [TextNode("just plain text", TextType.TEXT)],
            text_to_textnodes("just plain text"),
        )

    def test_text_to_textnodes_with_images_and_links(self):
        text = (
            "Start ![alt](https://example.com/image.png) middle "
            "[site](https://example.com) end"
        )
        self.assertListEqual(
            [
                TextNode("Start ", TextType.TEXT),
                TextNode("alt", TextType.IMAGE, "https://example.com/image.png"),
                TextNode(" middle ", TextType.TEXT),
                TextNode("site", TextType.LINK, "https://example.com"),
                TextNode(" end", TextType.TEXT),
            ],
            text_to_textnodes(text),
        )


class TestMarkdownToHTMLNode(unittest.TestCase):
    def test_paragraphs(self):
        md = """
This is **bolded** paragraph
text in a p
tag here

This is another paragraph with _italic_ text and `code` here

"""

        node = markdown_to_html_node(md)
        html = node.to_html()
        self.assertEqual(
            html,
            "<div><p>This is <b>bolded</b> paragraph text in a p tag here</p>"
            "<p>This is another paragraph with <i>italic</i> text and "
            "<code>code</code> here</p></div>",
        )

    def test_codeblock(self):
        md = """
```
This is text that _should_ remain
the **same** even with inline stuff
```
"""

        node = markdown_to_html_node(md)
        html = node.to_html()
        self.assertEqual(
            html,
            "<div><pre><code>This is text that _should_ remain\n"
            "the **same** even with inline stuff\n</code></pre></div>",
        )

    def test_heading(self):
        md = "# Heading with **bold** text"
        self.assertEqual(
            markdown_to_html_node(md).to_html(),
            "<div><h1>Heading with <b>bold</b> text</h1></div>",
        )

    def test_quote_block(self):
        md = ">first line\n>second line"
        self.assertEqual(
            markdown_to_html_node(md).to_html(),
            "<div><blockquote>first line\nsecond line</blockquote></div>",
        )

    def test_unordered_list(self):
        md = "- first item\n- second item"
        self.assertEqual(
            markdown_to_html_node(md).to_html(),
            "<div><ul><li>first item</li><li>second item</li></ul></div>",
        )

    def test_ordered_list(self):
        md = "1. first item\n2. second item"
        self.assertEqual(
            markdown_to_html_node(md).to_html(),
            "<div><ol><li>first item</li><li>second item</li></ol></div>",
        )


class TestExtractTitle(unittest.TestCase):
    def test_extract_title(self):
        markdown = "# Hello"
        self.assertEqual(extract_title(markdown), "Hello")

    def test_extract_title_strips_whitespace(self):
        markdown = "#   Tolkien Fan Club   "
        self.assertEqual(extract_title(markdown), "Tolkien Fan Club")

    def test_extract_title_raises_without_h1(self):
        markdown = "## Not the title\n\nParagraph text"
        with self.assertRaisesRegex(ValueError, "markdown must contain an h1 header"):
            extract_title(markdown)


if __name__ == "__main__":
    unittest.main()
