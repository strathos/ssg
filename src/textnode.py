import re
from enum import Enum

from htmlnode import LeafNode, ParentNode

class TextType(Enum):
    TEXT = "text"
    PLAIN = "text"
    BOLD = "bold"
    ITALIC = "italic"
    CODE = "code"
    LINK = "link"
    IMAGE = "image"


class BlockType(Enum):
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    CODE = "code"
    QUOTE = "quote"
    UNORDERED_LIST = "unordered_list"
    ORDERED_LIST = "ordered_list"


class TextNode:
    def __init__(self, text, text_type, url=None):
        if not isinstance(text_type, TextType):
            raise TypeError("text_type must be a TextType enum")

        self.text = text
        self.text_type = text_type
        self.url = url

    def __eq__(self, other):
        if not isinstance(other, TextNode):
            return False

        return (
            self.text == other.text and
            self.text_type == other.text_type and
            self.url == other.url
        )

    def __repr__(self):
        return f"TextNode({self.text}, {self.text_type.value}, {self.url})"


def text_node_to_html_node(text_node):
    if text_node.text_type == TextType.TEXT:
        return LeafNode(None, text_node.text)

    if text_node.text_type == TextType.BOLD:
        return LeafNode("b", text_node.text)

    if text_node.text_type == TextType.ITALIC:
        return LeafNode("i", text_node.text)

    if text_node.text_type == TextType.CODE:
        return LeafNode("code", text_node.text)

    if text_node.text_type == TextType.LINK:
        return LeafNode("a", text_node.text, {"href": text_node.url})

    if text_node.text_type == TextType.IMAGE:
        return LeafNode(
            "img",
            "",
            {"src": text_node.url, "alt": text_node.text},
        )

    raise ValueError("invalid TextType")


def split_nodes_delimiter(old_nodes, delimiter, text_type):
    new_nodes = []

    for old_node in old_nodes:
        if old_node.text_type != TextType.TEXT:
            new_nodes.append(old_node)
            continue

        split_text = old_node.text.split(delimiter)
        if len(split_text) % 2 == 0:
            raise ValueError(f"missing closing delimiter: {delimiter}")

        for index, text in enumerate(split_text):
            if text == "":
                continue

            if index % 2 == 0:
                new_nodes.append(TextNode(text, TextType.TEXT))
            else:
                new_nodes.append(TextNode(text, text_type))

    return new_nodes


def extract_markdown_images(text):
    return re.findall(r"!\[([^\[\]]*)\]\(([^\(\)]*)\)", text)


def extract_markdown_links(text):
    return re.findall(r"(?<!!)\[([^\[\]]*)\]\(([^\(\)]*)\)", text)


def split_nodes_image(old_nodes):
    return split_nodes_markdown(old_nodes, extract_markdown_images, TextType.IMAGE)


def split_nodes_link(old_nodes):
    return split_nodes_markdown(old_nodes, extract_markdown_links, TextType.LINK)


def split_nodes_markdown(old_nodes, extract_function, text_type):
    new_nodes = []

    for old_node in old_nodes:
        if old_node.text_type != TextType.TEXT:
            new_nodes.append(old_node)
            continue

        original_text = old_node.text
        matches = extract_function(original_text)

        if not matches:
            new_nodes.append(old_node)
            continue

        remaining_text = original_text
        for alt_or_text, url in matches:
            if text_type == TextType.IMAGE:
                markdown_text = f"![{alt_or_text}]({url})"
            else:
                markdown_text = f"[{alt_or_text}]({url})"

            sections = remaining_text.split(markdown_text, 1)
            if len(sections) != 2:
                raise ValueError(f"invalid markdown: {markdown_text}")

            if sections[0]:
                new_nodes.append(TextNode(sections[0], TextType.TEXT))

            new_nodes.append(TextNode(alt_or_text, text_type, url))
            remaining_text = sections[1]

        if remaining_text:
            new_nodes.append(TextNode(remaining_text, TextType.TEXT))

    return new_nodes


def text_to_textnodes(text):
    nodes = [TextNode(text, TextType.TEXT)]
    nodes = split_nodes_image(nodes)
    nodes = split_nodes_link(nodes)
    nodes = split_nodes_delimiter(nodes, "**", TextType.BOLD)
    nodes = split_nodes_delimiter(nodes, "_", TextType.ITALIC)
    nodes = split_nodes_delimiter(nodes, "`", TextType.CODE)
    return nodes


def markdown_to_blocks(markdown):
    blocks = markdown.split("\n\n")
    return [block.strip() for block in blocks if block.strip() != ""]


def block_to_block_type(block):
    if re.match(r"^#{1,6} .+", block):
        return BlockType.HEADING

    if block.startswith("```\n") and block.endswith("\n```"):
        return BlockType.CODE

    lines = block.split("\n")

    if all(line.startswith(">") for line in lines):
        return BlockType.QUOTE

    if all(line.startswith("- ") for line in lines):
        return BlockType.UNORDERED_LIST

    if is_ordered_list(lines):
        return BlockType.ORDERED_LIST

    return BlockType.PARAGRAPH


def is_ordered_list(lines):
    for index, line in enumerate(lines, start=1):
        if not line.startswith(f"{index}. "):
            return False
    return True


def text_to_children(text):
    return [text_node_to_html_node(node) for node in text_to_textnodes(text)]


def markdown_to_html_node(markdown):
    blocks = markdown_to_blocks(markdown)
    children = []

    for block in blocks:
        children.append(block_to_html_node(block))

    return ParentNode("div", children)


def block_to_html_node(block):
    block_type = block_to_block_type(block)

    if block_type == BlockType.PARAGRAPH:
        return ParentNode("p", text_to_children(block.replace("\n", " ")))

    if block_type == BlockType.HEADING:
        heading_level = heading_level_from_block(block)
        heading_text = block[heading_level + 1:]
        return ParentNode(f"h{heading_level}", text_to_children(heading_text))

    if block_type == BlockType.CODE:
        code_text = block[4:-3]
        code_node = text_node_to_html_node(TextNode(code_text, TextType.TEXT))
        return ParentNode("pre", [ParentNode("code", [code_node])])

    if block_type == BlockType.QUOTE:
        quote_text = "\n".join(strip_quote_prefix(line) for line in block.split("\n"))
        return ParentNode("blockquote", text_to_children(quote_text))

    if block_type == BlockType.UNORDERED_LIST:
        return ParentNode("ul", list_items_to_html_nodes(block, "- "))

    if block_type == BlockType.ORDERED_LIST:
        return ParentNode("ol", list_items_to_html_nodes(block, r"\d+\. ", True))

    raise ValueError("invalid block type")


def heading_level_from_block(block):
    return len(block.split(" ", 1)[0])


def strip_quote_prefix(line):
    if line.startswith("> "):
        return line[2:]
    return line[1:]


def list_items_to_html_nodes(block, marker, use_regex=False):
    items = []

    for line in block.split("\n"):
        if use_regex:
            item_text = re.sub(f"^{marker}", "", line)
        else:
            item_text = line[len(marker):]
        items.append(ParentNode("li", text_to_children(item_text)))

    return items


def extract_title(markdown):
    for block in markdown_to_blocks(markdown):
        if re.match(r"^# .+", block):
            return block[2:].strip()
    raise ValueError("markdown must contain an h1 header")
