import requests
from bs4 import BeautifulSoup
import argparse

def download_and_clean_page(url, divs_to_remove_ids=None, divs_to_remove_classes=None):
    """
    Downloads a page from a URL and removes specified divs by ID and/or class.

    Args:
        url (str): The URL of the page to download.
        divs_to_remove_ids (list, optional): A list of div IDs to remove. Defaults to None.
        divs_to_remove_classes (list, optional): A list of div class names to remove. Defaults to None.

    Returns:
        str: The HTML content of the page with specified divs removed,
             or None if an error occurs.
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


        # Return the modified HTML content
        return soup.prettify()

    except requests.exceptions.RequestException as e:
        print(f"Error downloading the page: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Download a webpage and remove specified div elements.")
    parser.add_argument("url", help="The URL of the webpage to process.")
    parser.add_argument("--ids", nargs='*', default=["global_header", "-1"], help="A list of div IDs to remove (e.g., --ids id1 id2). Defaults to 'global_header' and '-1'.")
    parser.add_argument("--classes", nargs='*', default=[], help="A list of div class names to remove (e.g., --classes class1 class2).")
    parser.add_argument("--output", default="cleaned_page.html", help="The name of the output HTML file. Defaults to 'cleaned_page.html'.")


    args = parser.parse_args()

    target_url = args.url
    ids_to_remove_from_page = args.ids
    classes_to_remove_from_page = args.classes
    output_filename = args.output


    print(f"Processing URL: {target_url}")
    print(f"Attempting to remove divs with IDs: {ids_to_remove_from_page}")
    if classes_to_remove_from_page:
        print(f"Attempting to remove divs with classes: {classes_to_remove_from_page}")


    cleaned_html = download_and_clean_page(target_url,
                                         divs_to_remove_ids=ids_to_remove_from_page,
                                         divs_to_remove_classes=classes_to_remove_from_page)

    if cleaned_html:
        # You can now save the cleaned HTML to a file or process it further
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(cleaned_html)
        print(f"Page downloaded and cleaned successfully. Saved as {output_filename}")
    else:
        print("Failed to retrieve or clean the page.")