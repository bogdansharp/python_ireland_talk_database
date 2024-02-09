'''
    Meetup API scraping here. 
    
    created 29.01.2024 by bogdansharpy@gmail.com, updated 09.02.2024

    Uses publicly accessible Meetup GraphQL API to get information about Events: https://www.meetup.com/api/schema/#Event
    API Endpoint: "https://api.meetup.com/gql"

    Example of how to use script:
        python meetup.py --group pythonireland

    With no arguments by default will get events for group: "pythonireland"
'''

import argparse
import requests
import csv

class Meetup:
    def __init__(self, group=None) -> None:
        self.group = group if group else "pythonireland"
        self.api_url = "https://api.meetup.com/gql" 

    def get_meetup_data(self):
        headers = {"Content-Type": "application/json"}
        csv_file_name = f"{self.group}_meetups.csv"
        payload = { "query": 
            """
            query ($urlname: String!) {
                groupByUrlname(urlname: $urlname) {
                    id
                    name
                    pastEvents(input: { first: 100500 }) {
                        count
                        pageInfo {
                            hasNextPage
                            hasPreviousPage
                            startCursor
                            endCursor
                        }
                        edges {
                            node {
                                id
                                status
                                token
                                eventUrl
                                title
                                dateTime
                                endTime
                                description
                                going
                                eventType
                                imageUrl
                                venue {
                                    name
                                    city
                                    address
                                    postalCode
                                    lat
                                    lng
                                }
                                hosts {
                                    id
                                    name
                                }
                                topics {
                                    count
                                    edges {
                                        node {
                                            urlkey
                                            name
                                            id
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            """,
            "variables": { "urlname": self.group }
        }
        events = []
        try:
            response = requests.post(self.api_url, json=payload, headers=headers)
            if response.status_code == 200:
                result = response.json()
                if (not result) or ('data' not in result) or \
                    ('groupByUrlname' not in result['data']) or \
                    (not result['data']['groupByUrlname']):
                    raise Exception(f"GraphQL empty result")
                events = [event['node'] for event in result['data']['groupByUrlname']['pastEvents']['edges']]
            else:
                raise Exception(f"GraphQL request failed with status code {response.status_code}: {response.text}")

            rows = []
            max_hosts = 0
            max_topics = 0
            for e in events:
                row = {}
                if 'id' in e: row['id'] = e['id'].strip()
                if 'status' in e: row['status'] = e['status'].strip()
                if 'title' in e: row['title'] = e['title'].strip()
                if 'eventUrl' in e: row['url'] = e['eventUrl'].strip()
                if 'dateTime' in e: row['start_at'] = e['dateTime'].strip()
                if 'endTime' in e: row['end_at'] = e['endTime'].strip()
                if 'going' in e: row['going'] = e['going']  # int
                if 'eventType' in e: row['eventType'] = e['eventType'].strip()
                if 'venue' in e and e['venue']:
                    venue = e['venue']
                    if 'name' in venue: row['venue'] = venue['name'].strip()
                    if 'city' in venue: row['city'] = venue['city'].strip()
                    if 'address' in venue: row['address'] = venue['address'].strip()
                    if 'postalCode' in venue: row['postalCode'] = venue['postalCode'].strip()
                    if 'lat' in venue: row['lat'] = venue['lat']  # float
                    if 'lng' in venue: row['lng'] = venue['lng']  # float
                if e['hosts']: 
                    hosts = [host['name'] for host in e['hosts']]
                    max_hosts = max(max_hosts, len(hosts))
                    for i, host in enumerate(hosts):
                        row[f"host{i + 1}"] = host.strip()
                if 'topics' in e and 'edges' in e['topics'] and e['topics']['edges']:
                    topics = [topic['node'] for topic in e['topics']['edges']]
                    max_topics = max(max_topics, len(topics))
                    for i, topic in enumerate(topics):
                        row[f"topic{i + 1}"] = topic['name'].strip()
                if 'description' in e: row['description'] = e['description'].strip()
                rows.append(row)

            headers = ['id', 'status', 'title', 'url', 'start_at', 'end_at', 'going', \
                'eventType', 'venue', 'city', 'address', 'postalCode', 'lat', 'lng']
            for i in range(max_hosts):
                headers.append(f"host{i + 1}")
            for i in range(max_topics):
                headers.append(f"topic{i + 1}")
            headers.append('description')

            with open(csv_file_name, 'w', newline='', encoding='utf-8') as outf:
                csvwriter = csv.DictWriter(outf, delimiter =',', fieldnames=headers)
                csvwriter.writeheader()
                for row in rows:
                    csvwriter.writerow(row)
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process meetup group url.')
    parser.add_argument('--group', type=str, help='The group url in meetup', default=None)
    args = parser.parse_args()
    meetupScraper = Meetup(args.group)
    meetupScraper.get_meetup_data()