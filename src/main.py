import os
import shutil
import sys

from textnode import extract_title, markdown_to_html_node


def copy_static_to_docs(source, destination):
    if os.path.exists(destination):
        shutil.rmtree(destination)

    os.mkdir(destination)
    copy_directory_contents(source, destination)


def copy_directory_contents(source, destination):
    for entry in os.listdir(source):
        source_path = os.path.join(source, entry)
        destination_path = os.path.join(destination, entry)

        if os.path.isfile(source_path):
            shutil.copy(source_path, destination_path)
            print(f"Copied file: {source_path} -> {destination_path}")
        else:
            os.mkdir(destination_path)
            copy_directory_contents(source_path, destination_path)


def generate_page(from_path, template_path, dest_path, basepath):
    print(
        f"Generating page from {from_path} to {dest_path} using {template_path}"
    )

    with open(from_path, encoding="utf-8") as markdown_file:
        markdown = markdown_file.read()

    with open(template_path, encoding="utf-8") as template_file:
        template = template_file.read()

    content_html = markdown_to_html_node(markdown).to_html()
    title = extract_title(markdown)
    page_html = template.replace("{{ Title }}", title).replace(
        "{{ Content }}", content_html
    )
    page_html = page_html.replace('href="/', f'href="{basepath}')
    page_html = page_html.replace('src="/', f'src="{basepath}')

    destination_dir = os.path.dirname(dest_path)
    if destination_dir:
        os.makedirs(destination_dir, exist_ok=True)

    with open(dest_path, "w", encoding="utf-8") as dest_file:
        dest_file.write(page_html)


def generate_pages_recursive(content_dir, template_path, dest_dir, basepath):
    for entry in os.listdir(content_dir):
        source_path = os.path.join(content_dir, entry)

        if os.path.isfile(source_path):
            if not entry.endswith(".md"):
                continue

            relative_path = os.path.relpath(source_path, content_dir)
            destination_path = os.path.join(
                dest_dir,
                os.path.splitext(relative_path)[0] + ".html",
            )
            generate_page(source_path, template_path, destination_path, basepath)
        else:
            relative_dir = os.path.relpath(source_path, content_dir)
            destination_subdir = os.path.join(dest_dir, relative_dir)
            generate_pages_recursive(
                source_path,
                template_path,
                destination_subdir,
                basepath,
            )


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    basepath = sys.argv[1] if len(sys.argv) > 1 else "/"
    source_dir = os.path.join(base_dir, "static")
    destination_dir = os.path.join(base_dir, "docs")
    content_dir = os.path.join(base_dir, "content")
    template_path = os.path.join(base_dir, "template.html")

    copy_static_to_docs(source_dir, destination_dir)
    generate_pages_recursive(content_dir, template_path, destination_dir, basepath)


if __name__ == "__main__":
    main()
