import requests
from bs4 import BeautifulSoup
import json
import re

# Base URLs for different movie genres
urls = {
    'hollywood': 'https://0gomovies.id/genre/hollywood/',
    'multi': 'https://0gomovies.id/genre/multi-language/',
    'tamil': 'https://0gomovies.id/genre/watch-tamil-movies/',
    'netflix': 'https://0gomovies.mov/genre/watch-tamil-movies/'  # Adjust as per your requirement
}

# Function to scrape data for a given genre URL (First Script)
def scrape_data(base_url, genre):
    poster_links = []
    movie_links = []
    page_number = 1
    max_pages = 1  # Limiting to 2 pages for demo purposes

    while page_number <= max_pages:
        if page_number == 5:
            print(f"Skipping page {page_number}")
            page_number += 1
            continue

        url = f'{base_url}page/{page_number}/'
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Failed to retrieve page {page_number}, status code:", response.status_code)
            break

        soup = BeautifulSoup(response.text, 'html.parser')
        images = soup.find_all('img', class_='thumb mli-thumb lazy')
        for img in images:
            img_url = img.get('data-original') or img.get('src')
            if img_url:
                poster_links.append(img_url)

        items = soup.find_all('div', class_='ml-item')
        if not items:
            print(f"No more items found for {genre}, ending pagination.")
            break

        for div in items:
            a_tag = div.find('a', class_='ml-mask')
            if a_tag:
                movie_url = a_tag.get('href')
                if movie_url:
                    movie_links.append(movie_url)

        print(f"Fetched page {page_number} for {genre} with {len(images)} images and {len(items)} items.")
        page_number += 1

    return poster_links, movie_links

# Function to fetch movie details from the movie links (First Script)
def fetch_movie_details(movie_links, poster_links):
    movie_details = []

    for index, movie_url in enumerate(movie_links):
        print(f"\nFetching details from: {movie_url}")
        response = requests.get(movie_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        movie_name = soup.find('h3').text.strip() if soup.find('h3') else "Unknown"
        video_url_player1 = None
        video_url_player2 = None

        button_tags = soup.find_all('button', {'class': 'chbtn'})
        for button_tag in button_tags:
            if "WATCH ON PLAYER 2" in button_tag.text:
                onclick_attr = button_tag['onclick']
                start = onclick_attr.find("('") + 2
                end = onclick_attr.find("')", start)
                if start != -1 and end != -1:
                    external_link = onclick_attr[start:end]
                    if "cdn.bewab.co" in external_link:
                        video_url_player2 = external_link[external_link.find("https://cdn.bewab.co"):]

        if not video_url_player2:
            for button_tag in button_tags:
                if "WATCH ON PLAYER 1" in button_tag.text:
                    onclick_attr = button_tag['onclick']
                    start = onclick_attr.find("('") + 2
                    end = onclick_attr.find("')", start)
                    if start != -1 and end != -1:
                        video_url_player1 = onclick_attr[start:end]

        if index < len(poster_links):
            if video_url_player2 or video_url_player1:
                movie_detail = {
                    'name': movie_name,
                    'uri': poster_links[index]
                }
                if video_url_player2:
                    movie_detail['link'] = video_url_player2.replace(
                        "https://cdn.bewab.co/", "https://videooo.news/"
                    )
                elif video_url_player1:
                    movie_detail['link'] = video_url_player1.replace(
                        "https://cdn.bewab.co/", "https://videooo.news/"
                    )
                movie_details.append(movie_detail)

    return movie_details

# Function to fetch movie details from the second script (Netflix section)
def fetch_movies(base_url, pages):
    movie_details = []
    for page in range(1, pages + 1):
        url = f"{base_url}/page/{page}/"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Failed to retrieve page {page}. Status code: {response.status_code}")
            continue

        soup = BeautifulSoup(response.text, 'html.parser')
        movie_links = soup.find_all('a', class_='ml-mask')

        for link in movie_links:
            title = link.get('title', '')
            image_tag = link.find('img', class_='thumb mli-thumb lazy')

            if image_tag:
                image_src = image_tag.get('data-original', '')
                next_link = link.get('href', '')
                next_url = f"{next_link[:-1]}/watching/" if next_link.endswith('/') else f"{next_link}/watching/"

                movie_details.append({
                    'title': title,
                    'image': image_src,
                    'next_link': next_url
                })

    return movie_details

def fetch_links(url):
    response = requests.get(url)
    html_content = response.text
    pattern = r'https://18rule\.com/\d+'
    matches = re.findall(pattern, html_content)
    return matches

def fetch_video_links(second_link):
    response = requests.get(second_link)
    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')

    video_links = []
    for a in soup.find_all('a', href=True):
        if 'link.php?link=' in a['href']:
            title = a.get_text(strip=True)
            link = a['href'].replace('https://lesmandalas.net/link.php?link=', '')
            link = link.replace('https://cdn.bewab.co/', 'https://videooo.news/')
            video_links.append({'title': title, 'link': link})

    video_links.sort(key=lambda x: int(re.search(r'(\d+)', x['title']).group()))
    return video_links

# Main function to fetch and combine all movie details
def main():
    final_data = {
        'hollywood': [],
        'multi': [],
        'tamil': [],
        'netflix': []
    }

    # Fetch data for each genre (First Script)
    for genre, base_url in urls.items():
        if genre in ['hollywood', 'multi', 'tamil']:
            poster_links, movie_links = scrape_data(base_url, genre)
            genre_data = fetch_movie_details(movie_links, poster_links)
            final_data[genre].extend(genre_data)

        # Fetch Netflix data (Second Script)
        if genre == 'netflix':
            movies = fetch_movies(base_url, 56)
            for movie in movies:
                video_links = fetch_links(movie['next_link'])
                if len(video_links) < 2:
                    print(f"Not enough links found for {movie['title']}.")
                    continue
                second_link = video_links[1]
                videos = fetch_video_links(second_link)
                final_data['netflix'].append({
                    "name": movie['title'],
                    "uri": movie['image'],
                    "videos": videos
                })

    # Save the final data to db.json
    with open('db.json', 'w') as json_file:
        json.dump(final_data, json_file, indent=4)

    print("Data successfully written to db.json")

if __name__ == '__main__':
    main()
