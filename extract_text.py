import os
from ebooklib import epub
from ebooklib import ITEM_DOCUMENT, ITEM_NAVIGATION
from bs4 import BeautifulSoup
from pathlib import Path

def sanitize_filename(title, max_length=100):
    """
    Sanitizes the title to create a safe filename and limits its length.
    
    Args:
        title (str): The original title.
        max_length (int): Maximum allowed length for the filename.
    
    Returns:
        str: A sanitized and truncated filename.
    """
    # Replace non-alphanumeric characters with underscores
    safe_title = "".join([c if c.isalnum() else "_" for c in title])
    
    # Truncate the title to the maximum allowed length
    if len(safe_title) > max_length:
        safe_title = safe_title[:max_length]
        # Optionally, remove trailing underscores
        safe_title = safe_title.rstrip("_")
    
    return safe_title

def extract_text_from_epub(epub_path, output_base_folder):
    book = epub.read_epub(epub_path)
    # Get the book title from the metadata, default to 'Unknown_Book' if not available
    book_title = book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else 'Unknown_Book'

    # Sanitize the book title for use in folder names
    safe_book_title = sanitize_filename(book_title, max_length=100)
    output_folder = output_base_folder / safe_book_title
    output_folder.mkdir(parents=True, exist_ok=True)

    file_counter = 1
    non_chapter_content = ""
    min_content_length = 100  # Minimum length to consider as a chapter

    # Extract potential titles from the navigation (Table of Contents)
    nav_titles = extract_titles_from_nav(book)

    # Process only the items in the spine
    for item_id, _ in book.spine[1:]:  # Skip the first item if it's 'nav'
        epub_item = book.get_item_with_id(item_id)

        if epub_item and epub_item.get_type() == ITEM_DOCUMENT:
            # Use get_body_content to get the body part only
            body_content = epub_item.get_body_content().decode() if epub_item.get_body_content() else epub_item.get_content().decode()
            title = epub_item.title or "Untitled"

            if body_content:
                soup = BeautifulSoup(body_content, 'html.parser')

                # Attempt to find chapter titles in various elements
                chapter_title = soup.find(['h1', 'h2', 'h3', 'h4'])
                if not chapter_title:
                    # Check for titles in custom or less common elements
                    chapter_title = soup.find('p', {'class': 'title'}) or \
                                    soup.find('div', {'class': 'chapter-title'}) or \
                                    soup.find('span', {'class': 'chapter-title'})

                # If no common title tags are found, check <em> tags with additional conditions
                if not chapter_title:
                    em_tags = soup.find_all('em')  
                    for em in em_tags:
                        # Assuming titles are often the first <em> tags and are isolated
                        if is_likely_title(em):
                            chapter_title = em
                            break

                # Use title from navigation if possible
                if not chapter_title and nav_titles:
                    # Extract the filename part from content_src (e.g., "chapter1.xhtml#section")
                    content_src = epub_item.get_name().split('/')[-1].split('#')[0]
                    title = nav_titles.get(content_src, title)

                if chapter_title:
                    title = chapter_title.get_text(strip=True)

                content = soup.get_text(separator=' ').strip()

                # Filter and save chapters or large content
                if len(content) > min_content_length:
                    # Sanitize and limit the title length
                    safe_title = sanitize_filename(title, max_length=100)
                    # Place the counter at the beginning for correct ordering
                    file_name = output_folder / f"{file_counter:03}_{safe_title}.txt"
                    
                    # Ensure the final file path doesn't exceed OS limits
                    if len(str(file_name)) > 255:
                        # Further truncate if necessary
                        safe_title = sanitize_filename(title, max_length=100 - (len(f"{file_counter:03}_") + len(".txt")))
                        file_name = output_folder / f"{file_counter:03}_{safe_title}.txt"
                    
                    with open(file_name, 'w', encoding='utf-8') as file:
                        file.write(content)
                    file_counter += 1
                else:
                    # Accumulate smaller content into a single non-chapter file
                    non_chapter_content += content + "\n\n"

    # Save all non-chapter content in a single file if any exists
    if non_chapter_content.strip():
        non_chapter_file = output_folder / "000_non_chapter_content.txt"
        with open(non_chapter_file, 'w', encoding='utf-8') as file:
            file.write(non_chapter_content)

def extract_titles_from_nav(book):
    """Extracts chapter titles from the EPUB navigation (TOC) if available."""
    nav_map = {}
    for item in book.get_items_of_type(ITEM_NAVIGATION):
        soup = BeautifulSoup(item.get_content(), 'html.parser')
        for nav_point in soup.find_all('navPoint'):
            play_order = nav_point.get('playOrder')
            label = nav_point.find('text').get_text(strip=True)
            content_src = nav_point.find('content').get('src').split('#')[0]
            nav_map[content_src] = label
    return nav_map

def is_likely_title(em_element):
    """Determines if an <em> tag is likely to be a title based on its context."""
    # Consider an <em> tag to be a title if it is one of the first elements,
    # is not followed by much text, or is inside a specific parent element like a header or div.
    if len(em_element.get_text(strip=True)) > 5:  # Avoid very short <em> text like 'e.g.'
        parent_name = em_element.find_parent().name
        if parent_name in ['h1', 'h2', 'h3', 'div', 'header', 'title', 'nav']:
            return True
        # Check if it is at the beginning of a document or section
        if em_element == em_element.find_parent().contents[0]:
            return True
    return False

def process_all_epubs(input_folder, output_folder):
    """Processes all EPUB files in the input folder."""
    input_folder = Path(input_folder)
    output_folder = Path(output_folder)
    output_folder.mkdir(exist_ok=True)

    for epub_file in input_folder.glob('*.epub'):
        print(f"Processing '{epub_file.name}'...")
        extract_text_from_epub(epub_file, output_folder)
    print("Processing complete.")

# Example usage
if __name__ == "__main__":
    input_folder = Path('epub_files')      # Folder containing your EPUB files
    output_folder = Path('extracted_text') # Folder to save the extracted text
    process_all_epubs(input_folder, output_folder)
