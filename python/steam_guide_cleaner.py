import requests
from bs4 import BeautifulSoup
import argparse
import re

def sanitize_filename(filename):
    """
    Sanitizes a filename by replacing spaces with underscores and removing
    characters that are invalid in filenames.
    
    Args:
        filename (str): The original filename
        
    Returns:
        str: The sanitized filename
    """
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    # Remove or replace invalid characters for filenames
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Remove extra underscores and trim
    filename = re.sub(r'_+', '_', filename).strip('_')
    return filename

def download_and_clean_page(url, divs_to_remove_ids=None, divs_to_remove_classes=None):
    """
    Downloads a page from a URL and removes specified divs by ID and/or class.

    Args:
        url (str): The URL of the page to download.
        divs_to_remove_ids (list, optional): A list of div IDs to remove. Defaults to None.
        divs_to_remove_classes (list, optional): A list of div class names to remove. Defaults to None.

    Returns:
        tuple: A tuple containing (html_content, guide_title)
               html_content (str): The HTML content of the page with specified divs removed
               guide_title (str): The title of the guide, or None if not found
               Returns (None, None) if an error occurs.
    """
    try:
        # Download the page content
        headers = { # Add a user-agent to mimic a browser request
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        html_content = response.text

        # Parse the HTML content
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract the guide title before removing any divs
        guide_title = None
        title_div = soup.find('div', class_='workshopItemTitle')
        if title_div:
            guide_title = title_div.get_text().strip()
            print(f"Found guide title: {guide_title}")
        else:
            print("Guide title not found (div with class 'workshopItemTitle' not found)")

        # Remove divs by ID
        if divs_to_remove_ids:
            for div_id in divs_to_remove_ids:
                div_to_remove = soup.find('div', id=div_id)
                if div_to_remove:
                    div_to_remove.decompose()  # Remove the div and its contents
                    print(f"Removed div with ID: {div_id}")
                else:
                    print(f"Div with ID '{div_id}' not found.")


        # Remove divs by class
        if divs_to_remove_classes:
            for div_class in divs_to_remove_classes:
                # Find all divs with the specified class
                divs = soup.find_all('div', class_=div_class)
                if divs:
                    for i, div in enumerate(divs):
                        div.decompose() # Remove the div and its contents
                        print(f"Removed div with class '{div_class}' (occurrence {i+1})")
                else:
                    print(f"Div with class '{div_class}' not found.")


        # Return the modified HTML content and guide title
        return soup.prettify(), guide_title

    except requests.exceptions.RequestException as e:
        print(f"Error downloading the page: {e}")
        return None, None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Download a webpage and remove specified div elements.")
    parser.add_argument("url", help="The URL of the webpage to process.")
    parser.add_argument("--ids", nargs='*', default=["global_header", "-1"], help="A list of div IDs to remove (e.g., --ids id1 id2). Defaults to 'global_header' and '-1'.")
    parser.add_argument("--classes", nargs='*', default=[], help="A list of div class names to remove (e.g., --classes class1 class2).")
    parser.add_argument("--output", default=None, help="The name of the output HTML file. If not provided, will use the guide title from the page.")


    args = parser.parse_args()

    target_url = args.url
    ids_to_remove_from_page = args.ids
    classes_to_remove_from_page = args.classes
    output_filename = args.output


    print(f"Processing URL: {target_url}")
    print(f"Attempting to remove divs with IDs: {ids_to_remove_from_page}")
    if classes_to_remove_from_page:
        print(f"Attempting to remove divs with classes: {classes_to_remove_from_page}")


    cleaned_html, guide_title = download_and_clean_page(target_url,
                                                       divs_to_remove_ids=ids_to_remove_from_page,
                                                       divs_to_remove_classes=classes_to_remove_from_page)

    if cleaned_html:
        # Determine the output filename
        if output_filename is None:
            if guide_title:
                output_filename = sanitize_filename(guide_title) + ".html"
            else:
                output_filename = "cleaned_page.html"
                print("Warning: Could not extract guide title, using default filename.")
        
        print(f"Using output filename: {output_filename}")
        
        # Save the cleaned HTML to a file
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(cleaned_html)
        print(f"Page downloaded and cleaned successfully. Saved as {output_filename}")
    else:
        print("Failed to retrieve or clean the page.")