import json
import os
import requests
from scripts.review_prompt import review_prompt

def get_pr_files(repo, pr_number, token):
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None

def review_code(file_content):
    prompt = review_prompt.format(code=file_content)
    try:
        response = requests.post('http://localhost:11434/api/generate', 
                                json={
                                    "model": "llama3.2",
                                    "prompt": prompt,
                                    "stream": False,
                                    "options": {
                                        "temperature": 0.7,
                                        "top_p": 0.8,
                                        "top_k": 40,
                                        "num_predict": 1024
                                    }
                                })
        if response.status_code == 200:
            return response.json()['response']
        else:
            return f"Error: {response.status_code}, {response.text}"
    except Exception as e:
        return f"Exception occurred during API call: {str(e)}"
    
def post_review_comment(repo, pr_number, commit_id, path, position, body, token):
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    data = {
        "body": body,
        "commit_id": commit_id,
        "path": path,
        "position": position 
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 201:
        print(f"Error posting comment: {response.status_code}, {response.text}")
        print(f"Response content: {response.content}")
        print(f"Request URL: {url}")
        print(f"Request headers: {headers}")
        print(f"Request data: {data}")

def main():
    github_token = os.environ['GITHUB_TOKEN']
    repo = os.environ['GITHUB_REPOSITORY']

    with open(os.environ['GITHUB_EVENT_PATH']) as f:
        event = json.load(f)
    pr_number = event['pull_request']['number']
    
    pr_files = get_pr_files(repo, pr_number, github_token)

    if pr_files:
        for file in pr_files:
            if file['status'] != 'removed':  
                content = requests.get(file['raw_url']).text
                review = review_code(content)

                post_review_comment(
                    repo,
                    pr_number,
                    file['sha'],  
                    file['filename'],  
                    file['changes'],  
                    f"AI Code Review:\n\n{review}",  
                    github_token
                )
    else:
        print("No files found or failed to fetch PR files.")

if __name__ == "__main__":
    main()
