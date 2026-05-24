import requests
import time
import json

def get_all_xeno_canto_recordings(search_params, api_key):
    query_parts = []
    for key, value in search_params.items():
        if key == "raw":
            query_parts.append(value)
        else:
            query_parts.append(f'{key}:"{value}"')
    query_string = " ".join(query_parts)

    url = "https://xeno-canto.org/api/3/recordings"

    all_recordings = []
    current_page = 1
    total_pages = 1

    print(f"Starting bulk download for query: {query_string}")

    while current_page <= total_pages:
        payload = {
            'query': query_string,
            'key': api_key,
            'page': current_page
        }

        print(f"Fetching page {current_page} of {total_pages}...", end="\r")

        try:
            response = requests.get(url, params=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"\nError fetching page {current_page}: {e}")
            break

        total_pages = int(data.get("numPages", 1))

        recordings_on_page = data.get("recordings", [])
        all_recordings.extend(recordings_on_page)

        current_page += 1
        time.sleep(1.0)

    print(f"\nFinished! Retreived {len(all_recordings)} total recordings across {total_pages} pages.")
    return all_recordings


MY_API_KEY = "9225d4f13ebfac3ac6e527d58798c6b7c283f90a"

my_query = {
    "grp": "birds",
    "cnt": "Poland",
    "q": "A",
    "len": ">10"
}

all_results = get_all_xeno_canto_recordings(my_query, MY_API_KEY)

if all_results:
    with open('recordings_data.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=4)

    print("Data successfully saved to recordings_data.json!")