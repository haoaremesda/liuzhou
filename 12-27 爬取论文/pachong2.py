import requests
from bs4 import BeautifulSoup

# URL of the web page
url = "https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0260187"

# Send a GET request to the URL
response = requests.get(url)


final_text = ""
# Check if the request was successful (status code 200)
if response.status_code == 200:
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract article title
    article_title = soup.find('h1', {'id': 'artTitle'}).text.strip()

    # Extract author list
    author_list = []
    authors = soup.find_all('a', {'class': 'author-name'})
    for author in authors:
        author_name = author.text.strip()
        author_list.append(author_name)

    # Extract publication information
    published_date = soup.find('li', {'id': 'artPubDate'}).text.strip()
    doi = soup.find('li', {'id': 'artDoi'}).find('a')['href']

    # Print the extracted information
    print("Article Title:", article_title)
    print("Author List:", author_list)
    print("Published Date:", published_date)
    print("DOI:", doi)
    
    final_text += f'[title-en]{article_title}\n'
    final_text += f'[author-list]{author_list}\n'
    final_text += f'[published-date]{published_date}\n'
    final_text += f'[DOI]{doi}\n'

    # Extract the abstract
    abstract_section = soup.find('div', class_='abstract-content')
    abstract_text = abstract_section.get_text(strip=True) if abstract_section else "Abstract not found."
    final_text += f'[abstract-en]{abstract_text}\n'

    # Extract the content sections
    content_sections = soup.find_all(['h2', 'h3', 'div'], class_=['section', 'toc-section'])
    
     # List of h2 and h3 sections to skip
    skip_sections = ['Supporting information', 'Acknowledgments', 'References']

    # Create a dictionary to store section titles and text
    content_data = {}

    # Loop through content sections
    for section in content_sections:
        # Skip specified h2 and h3 sections
        if section.name in ['h2', 'h3']:
            section_title = section.get_text(strip=True)
            if section_title in skip_sections:
                continue
            
        # if section.name == 'div' and not section.find('div', class_='figure'):
        if section.name == 'div':
            try:
                title = section.find('h2') or section.find('h3')
                section_1 = section.find('div', class_='figure')
                text_1 = section_1.get_text(strip=True)
                text = section.get_text(strip=True)
                text = text.replace(text_1,'')
            except:
            # content_33 = soup.find_all(['div'], class_=['section', 'toc-section'])
                title = section.find('h2') or section.find('h3')
                text = section.get_text(strip=True)
            # text = '\n'.join([f'[para]{p.get_text(strip=True)}' for p in section.find_all_next('p')])
        else:
            title = section
            text = '\n'.join([f'[para]{p.get_text(strip=True)}' for p in section.find_all_next('p')])
        # else:
        #     title = section
        # # Only include paragraphs from div elements without class=figure
        #     if section.name == 'div' and not section.find(class_='figure'):
        #         text = '\n'.join([f'[para]{p.get_text(strip=True)}' for p in section.find_all_next('p')])
        #     else:
        #         text = '\n'.join([f'[para]{p.get_text(strip=True)}' for p in section.find_all_next('p')])
    # Continue processing title and text as needed
        # Add title and text to the dictionary
        if title:
            if title.name == 'h2':
                title_prefix = '[title-first]'
            elif title.name == 'h3':
                title_prefix = '[title-second]'
            else:
                title_prefix = ''

            content_data[f"{title_prefix}{title.get_text(strip=True)}"] = text

    # Print the abstract
    # print("[abstract-en]")
    # print(abstract_text)
    # print("\n")

    # Print content sections
    for title, text in content_data.items():
        # print(f"{title}:")
        c_title = title.replace("[title-first]","").replace("[title-second]","")
        if c_title == 'Abstract' or c_title == 'Supporting information' or c_title == 'Acknowledgments' or c_title == 'References':
            continue
        final_text += f'{title}\n'
        # print(text)
        # c_title = title.replace("[title-first] ","").replace("[title-second] ","")
        # final_text += f'[para]{text[:]}\n'
        if text.startswith(c_title):
            n = len(c_title)
            text_q = text[n:]
            # print(text_q)
            final_text += f'[para]{text_q}\n'
        else:
            final_text += f'[para]{text[:]}\n'
        # print("\n")
        
    with open(r"output.txt", "w", encoding="utf-8") as file:
        file.write(final_text)

    print("Content saved to 'output.txt'")
else:
    print(f"Failed to retrieve the page. Status code: {response.status_code}")
