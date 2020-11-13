import functools
import http.client
import mimetypes
import re
import subprocess

import numpy as np
import requests
from flask import Flask
from flask_cors import CORS
from flask_restful import Api, Resource, reqparse

app = Flask(__name__)
# Add CORS
CORS(app)
app.config['SECRET_KEY'] = 'disable the web security'
app.config['CORS_HEADERS'] = 'Content-Type'

api = Api(app, default_mediatype='text/plain')

def verify_domain(domain):
    # if domain is arxiv -> get arxiv vanity URL
    if re.search('arxiv\.org', domain):
        arxiv_id = re.search('\d{4}\.\d{4,5}', domain)
        if arxiv_id:
            domain = f"https://www.arxiv-vanity.com/papers/{arxiv_id[0]}/"

    return domain


@functools.lru_cache(128)
def get_domain_contents(domain):
    domain = verify_domain(domain)
    ps = subprocess.Popen(["curl", "-Ls", domain], stdout=subprocess.PIPE)
    output = subprocess.check_output(["scrape"], stdin=ps.stdout)
    ps.wait()
    out = output.decode('utf-8')
    if out == "arXiv Vanity renders academic papers from arXiv as responsive web pages so you don’t have to squint at a PDF. Read this paper on arXiv.org.":
        out = ""
    return out


class Users(Resource):

    def post(self):
        parser = reqparse.RequestParser()

        parser.add_argument('domains', 
        action='append', 
        required=True)
        parser.add_argument('query', required=True)

        args = parser.parse_args()
        domains = args["domains"]#.split(',')
        print("AIDAN", domains)
        query = args["query"]

        order, scores, sorted_urls = sort_urls(query, domains)
        print(sorted_urls)
        return sorted_urls


api.add_resource(Users, '/domain')

headers = {'X-API-Key': '1n-Wl546DpbLfH346skL03lxG4fhd-uJkc1l1zxCI68=', 'Content-Type': 'application/json'}
url = "https://api.cohere.ai/baseline-1b/embed"


def sort_urls(query, tab_urls):
    #import ipdb
    #ipdb.set_trace()
    tab_texts = [get_domain_contents(tab_url) for tab_url in tab_urls]

    # query = 'joe biden'
    # tab_texts = ['barack obama', 'donald trump']

    @functools.lru_cache(10000)
    def get_embedding(text):
        # import ipdb
        # ipdb.set_trace()
        payload = {"text": text}
        response = requests.post(url, json=payload, headers=headers)
        embedding = response.json()['embedding']
        return np.array(embedding)

    def compute_similarity(left, right):
        return np.dot(left, right) / (np.linalg.norm(left) * np.linalg.norm(right))

    query_embed = get_embedding(query.lower())
    scores = []
    segments = []
    for tab_text in tab_texts:
        max_sim = 0
        max_sim_idx = 0
        #print(len(tab_text) // 1024, max(1, len(tab_text) // 1024), min(1000, len(tab_text) // 1024 + 1))
        seg_len = 100
        for i in range(min(10, max(1, len(tab_text) // seg_len))):
            if len(tab_text) > 250:
                text_segment = tab_text[i * seg_len:(i + 1) * seg_len]
                text_emb = get_embedding(text_segment.lower())
                new_sim = compute_similarity(query_embed, text_emb)
                if new_sim > max_sim:
                    max_sim = new_sim
                    max_sim_idx = i
            # Segment is too short
            elif 0 < len(tab_text) < 250:
                #print('SHORT: ', tab_text)
                max_sim = 0.1
                max_sim_idx = 0
                # Failed to parse
            else:
                max_sim = 0.0
                max_sim_idx = 0
        segments.append(tab_text[max_sim_idx * seg_len:(max_sim_idx + 1) * seg_len])
        scores.append(max_sim)

    # argsort returns indices of ascending value
    order = np.argsort(scores)[::-1]
    sort_by_score = lambda arr: [arr[idx] for idx in order]

    print('=' * 20)
    print(f'QUERY: {query}')
    for idx in order:
        print('\nURL: ', tab_urls[idx])
        print('SCORE: ', round(scores[idx], 3))
        print('SEGMENT: ', segments[idx])

    return order, sort_by_score(scores), sort_by_score(tab_urls)


if __name__ == '__main__':
    app.run(port=3337, debug=True)

