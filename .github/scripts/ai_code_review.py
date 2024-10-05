import json
import os
import requests
import logging
from scripts.review_prompt import review_prompt

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_pr_files(repo, pr_number, token):
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    logger.debug(f"PR 파일 가져오는 중. URL: {url}")
    logger.debug(f"헤더: {headers}")
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"PR 파일 가져오기 오류: {str(e)}")
        return None
    
def get_latest_commit_id(repo, pr_number, token):
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    pr_data = response.json()
    return pr_data['head']['sha']

def review_code(pr_content):
    prompt = review_prompt.format(code=pr_content)
    url = 'http://localhost:11434/api/generate'
    data = {
        "model": "codellama",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 40,
            "num_predict": 1024
        }
    }
    logger.debug(f"코드 리뷰 중. URL: {url}")
    logger.debug(f"요청 데이터: {data}")

    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()['response']
    except requests.RequestException as e:
        logger.error(f"코드 리뷰 중 오류 발생: {str(e)}")
        return f"코드 리뷰 중 발생한 에러: {str(e)}"
    
def post_review_comment(repo, pr_number, commit_sha, path, position, body, token):
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    data = {
        "body": body,
        "commit_id": commit_sha,
        "path": path,
        "position": position 
    }
    logger.debug(f"리뷰 코멘트 게시 중. URL: {url}")
    logger.debug(f"헤더: {headers}")
    logger.debug(f"데이터: {data}")

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        logger.info("리뷰 코멘트가 성공적으로 게시되었습니다")
    except requests.RequestException as e:
        logger.error(f"리뷰 코멘트 게시 중 오류 발생: {str(e)}")
        logger.error(f"응답 내용: {response.content if 'response' in locals() else '응답 없음'}")
        logger.error(f"응답 상태 코드: {e.response.status_code}")
        logger.error(f"응답 헤더: {e.response.headers}")
        logger.error(f"응답 내용: {e.response.text}")

def summarize_reviews(all_reviews):
    summary_prompt = f"다음은 여러 파일에 대한 코드 리뷰 결과입니다. 이를 간결하고 통합된 하나의 리뷰 코멘트로 요약해주세요:\n\n{''.join(all_reviews)}"
    summary = review_code(summary_prompt)
    return summary

def post_pr_comment(repo, pr_number, body, token):
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    data = {"body": body}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        logger.info("PR 코멘트가 성공적으로 게시되었습니다.")
    except requests.RequestException as e:
        logger.error(f"PR 코멘트 게시 중 오류 발생: {str(e)}")
        logger.error(f"응답 내용: {response.content if 'response' in locals() else '응답 없음'}")

def main():
    try:
        github_token = os.environ['GITHUB_TOKEN']
        repo = os.environ['GITHUB_REPOSITORY']
        event_path = os.environ['GITHUB_EVENT_PATH']
            
        logger.info(f"저장소 리뷰 시작: {repo}")
        logger.debug(f"GitHub 토큰 (처음 5자): {github_token[:5]}...")

        with open(event_path) as f:
            event = json.load(f)

        pr_number = event['pull_request']['number']
        logger.info(f"PR 번호 리뷰 중: {pr_number}")
        
        pr_files = get_pr_files(repo, pr_number, github_token)
        # latest_commit_id = get_latest_commit_id(repo, pr_number, github_token)

        all_reviews = []

        if pr_files:
            for file in pr_files:
                if file['status'] != 'removed':  
                    logger.info(f"파일 리뷰 중: {file['filename']}")
                    content = requests.get(file['raw_url']).text
                    review = review_code(content)
                    all_reviews.append(f"File: {file['filename']}\n{review}\n\n")

            combined_review = summarize_reviews(all_reviews)
            
            # post_review_comment(
            #     repo,
            #     pr_number,
            #     latest_commit_id, 
            #     file['filename'],  
            #     file['changes'],  
            #     f"AI Code Review:\n\n{review}",  
            #     github_token
            # )

            post_pr_comment(
                repo,
                pr_number,
                f"AI Code Review 요약:\n\n{combined_review}",
                github_token
            )

        else:
                logger.warning("파일을 찾을 수 없거나 PR 파일을 가져오는 데 실패했습니다.")

    except KeyError as e:
        logger.error(f"환경 변수가 설정되지 않음: {str(e)}")
    except Exception as e:
        logger.error(f"예상치 못한 오류 발생: {str(e)}")

if __name__ == "__main__":
    main()
