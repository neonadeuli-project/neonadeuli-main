import json
import os
from typing import List, Tuple
import requests
import re
import groq
import logging
from review_config import (
    IGNORED_EXTENSIONS, 
    IGNORED_FILES, 
    IMPORTANT_FILE_CHANGE_THRESHOLD, 
    IMPORTANT_FILE_CHANGE_RATIO,
    MAX_COMMENTS_PER_FILE
)

from scripts.review_prompt import (
    get_review_prompt,
    get_file_review_prompt,
    get_line_comments_prompt,
    get_total_comments_prompt
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

groq_client = groq.Groq(api_key=os.environ["GROQ_API_KEY"])

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

def review_code_groq(pr_content):
    prompt = get_review_prompt(pr_content)
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-70b-versatile",  
            messages=[
                {"role": "system", "content": "You are an expert code reviewer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1024
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq API 호출 중 오류 발생: {str(e)}")
        return f"코드 리뷰 중 발생한 에러: {str(e)}"

def review_code_ollama(pr_content):
    prompt = get_review_prompt(pr_content)
    url = 'http://localhost:11434/api/generate'
    data = {
        "model": "llama3.1",
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
    summary_prompt = f"다음은 전체적인 코드 리뷰 결과입니다 : \n\n{''.join(all_reviews)}"
    summary = review_code_groq(summary_prompt)
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

def post_line_comments(repo, pr_number, commit_sha, filename, patch, line_comments, token):
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    def get_line_numbers(patch):
        lines = patch.split('\n')
        line_numbers = []
        current_line = 0
        for line in lines:
            if line.startswith('@@'):
                current_line = int(line.split('+')[1].split(',')[0]) - 1
            elif not line.startswith('-'):
                current_line += 1
                if line.startswith('+'):
                    line_numbers.append(current_line)
        return line_numbers

    def post_single_comment(line_num, comment_text, position):
        data = {
            "body": comment_text.strip(),
            "commit_id": commit_sha,
            "path": filename,
            "line": position
        }
        logger.debug(f"라인 {line_num}에 리뷰 코멘트 게시 중. URL: {url}")
        logger.debug(f"헤더: {headers}")
        logger.debug(f"데이터: {data}")

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            logger.info(f"라인 {line_num}에 리뷰 코멘트가 성공적으로 게시되었습니다")
        except requests.RequestException as e:
            logger.error(f"라인 {line_num} 리뷰 코멘트 게시 중 오류 발생: {str(e)}")
            logger.error(f"응답 내용: {response.content if 'response' in locals() else '응답 없음'}")
            logger.error(f"응답 상태 코드: {e.response.status_code if 'response' in locals() else '알 수 없음'}")
            logger.error(f"응답 헤더: {e.response.headers if 'response' in locals() else '알 수 없음'}")
            logger.error(f"응답 내용: {e.response.text if 'response' in locals() else '알 수 없음'}")

    def parse_comments(line_comments: str) -> List[Tuple[int, str]]:
        parsed_comments = []
        for comment in line_comments.split('\n'):
            match = re.match(r'(\d+):\s*(.*)', comment)
            if match:
                line_num, comment_text = match.groups()
                try:
                    line_num = int(line_num)
                    parsed_comments.append((line_num, comment_text))
                except ValueError:
                    logger.warning(f"잘못된 라인 번호 형식: {line_num}")
            else:
                logger.warning(f"파싱할 수 없는 코멘트 형식: {comment}")
        return parsed_comments

    def evaluate_importance(comment: str) -> int:
        # 여기에 코멘트의 중요도를 평가하는 로직을 구현합니다.
        # 예를 들어, 특정 키워드의 존재 여부, 코멘트의 길이 등을 고려할 수 있습니다.
        importance = 0
        if "중요" in comment or "critical" in comment.lower():
            importance += 5
        if "버그" in comment or "bug" in comment.lower():
            importance += 4
        if "개선" in comment or "improvement" in comment.lower():
            importance += 3
        importance += len(comment) // 50  # 긴 코멘트에 약간의 가중치 부여
        return importance

    line_numbers = get_line_numbers(patch)
    parsed_comments = parse_comments(line_comments)
    
    # 중요도에 따라 코멘트 정렬
    sorted_comments = sorted(parsed_comments, key=lambda x: evaluate_importance(x[1]), reverse=True)

    comments_posted = 0
    # 라인 코멘트 파싱 및 게시
    for line_num, comment_text in sorted_comments[:MAX_COMMENTS_PER_FILE]:
        if 0 <= line_num - 1 < len(line_numbers):
            position = line_numbers[line_num - 1]
            if post_single_comment(line_num, comment_text, position):
                comments_posted += 1
        else:
            logger.warning(f"라인 {line_num}이 유효한 범위를 벗어났습니다.")

    # for comment in line_comments.split('\n'):
        # if comments_posted >= MAX_COMMENTS_PER_FILE:
        #     logger.info(f"{filename}: 최대 코멘트 수({MAX_COMMENTS_PER_FILE})에 도달했습니다. 나머지 코멘트는 생략됩니다.")
        #     break

        # match = re.match(r'(\d+):\s*(.*)', comment)
        # if match:
        #     line_num, comment_text = match.groups()
        #     try:
        #         line_num = int(line_num)
        #         if 0 <= line_num - 1 < len(line_numbers):
        #             position = line_numbers[line_num - 1]
        #             if post_single_comment(line_num, comment_text, position):
        #                 comments_posted += 1
        #         else:
        #             logger.warning(f"라인 {line_num}이 유효한 범위를 벗어났습니다.")
        #     except ValueError:
        #         logger.warning(f"잘못된 라인 번호 형식: {line_num}")
        # else:
        #     logger.warning(f"파싱할 수 없는 코멘트 형식: {comment}")
    
    if comments_posted == 0:
        logger.info(f"{filename}: 추가된 코멘트가 없습니다.")
    else:
        logger.info(f"{filename}: 총 {comments_posted}개의 코멘트가 추가되었습니다.")

    logger.info("모든 라인 코멘트 처리 완료")

def get_environment_variables():
    try:
        github_token = os.environ['GITHUB_TOKEN']
        repo = os.environ['GITHUB_REPOSITORY']
        event_path = os.environ['GITHUB_EVENT_PATH']
        return github_token, repo, event_path
    except KeyError as e:
        logger.error(f"환경 변수가 설정되지 않음: {str(e)}")
        raise

def fetch_pr_data(repo, pr_number, github_token):
    pr_files = get_pr_files(repo, pr_number, github_token)
    if not pr_files:
        logger.warning("파일을 찾을 수 없거나 PR 파일을 가져오는 데 실패했습니다.")
        return None, None
    latest_commit_id = get_latest_commit_id(repo, pr_number, github_token)
    return pr_files, latest_commit_id

def is_important_file(file):
    filename = file['filename']
    if filename in IGNORED_FILES:
        logger.debug(f"무시된 파일: {filename}")
        return False
    
    if any(filename.endswith(ext) for ext in IGNORED_EXTENSIONS):
        logger.debug(f"무시할 확장자 파일: {filename}")
        return False

    if file['status'] == 'removed':
        logger.info(f"삭제된 파일: {file['filename']}")
        return True
    
    total_lines = file.get('additions', 0) + file.get('deletions', 0)
    change_ratio = total_lines / file.get('changes', 1)
    is_important = file['changes'] > IMPORTANT_FILE_CHANGE_THRESHOLD or change_ratio > IMPORTANT_FILE_CHANGE_RATIO
    
    if is_important:
        logger.info(f"중요 파일로 선정: {file['filename']} (변경: {file['changes']}줄, 비율: {change_ratio:.2f})")
    else:
        logger.debug(f"일반 파일: {file['filename']} (변경: {file['changes']}줄, 비율: {change_ratio:.2f})")
    
    return is_important

def generate_reviews(pr_files, repo, pr_number, latest_commit_id, github_token):
    all_code = ""
    important_files = [f for f in pr_files if is_important_file(f)]

    logger.info(f"총 {len(pr_files)}개 파일 중 {len(important_files)}개 파일이 중요 파일로 선정되었습니다.")
    
    for file in pr_files:
        if file['status'] == 'removed':
            all_code += f"File: {file['filename']} (DELETED)\n\n"
        else:
            logger.info(f"파일 리뷰 중: {file['filename']}")
            content = requests.get(file['raw_url']).text
            all_code += f"File: {file['filename']}\n{content}\n\n"

    if not all_code:
        logger.warning("리뷰할 코드가 없습니다. 모든 파일 내용을 가져오는 데 실패했습니다.")
        return None, []
    
    # 전체 코드에 대한 간략한 리뷰
    review_prompt = get_review_prompt(all_code)
    overall_review = review_code_groq(review_prompt)

    # 중요 파일에 대한 상세 리뷰
    for file in important_files:
        logger.info(f"중요 파일 상세 리뷰 중: {file['filename']}")
        if file['status'] == 'removed':
            file_review = f"파일 '{file['filename']}'이(가) 삭제되었습니다. 이 변경이 적절한지 확인해 주세요."
        else:
            content = requests.get(file['raw_url']).text
            file_review_prompt = get_file_review_prompt(file['filename'], content)
            file_review = review_code_groq(file_review_prompt)
        
        # 파일 전체에 대한 리뷰 코멘트
        post_file_comment(
            repo,
            pr_number,
            latest_commit_id,
            file['filename'],
            file_review,
            github_token
        )

        # 라인 별 코멘트
        line_comments_prompt = get_line_comments_prompt(file['filename'], content)
        line_comments = review_code_groq(line_comments_prompt)

        post_line_comments(
            repo,
            pr_number,
            latest_commit_id,
            file['filename'],
            file['patch'],
            line_comments,
            github_token
        )
    
    return overall_review

def post_file_comment(repo, pr_number, commit_sha, file_path, body, token):
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    data = {
        "body": body,
        "commit_id": commit_sha,
        "path": file_path,
        "position": 1
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        logger.info("PR 파일 코멘트가 성공적으로 게시되었습니다.")
    except requests.RequestException as e:
        logger.error(f"PR 코멘트 게시 중 오류 발생: {str(e)}")
        logger.error(f"응답 내용: {response.content if 'response' in locals() else '응답 없음'}")

def main():
    try:
        github_token, repo, event_path = get_environment_variables()
            
        logger.info(f"저장소 리뷰 시작: {repo}")
        logger.debug(f"GitHub 토큰 (처음 5자): {github_token[:5]}...")

        with open(event_path) as f:
            event = json.load(f)

        pr_number = event.get('pull_request', {}).get('number')
        if pr_number is None:
            logger.error("PR 번호를 찾을 수 없습니다. GitHub 이벤트 파일이 pull_request 이벤트를 포함하고 있는지 확인하세요.")

        logger.info(f"PR 번호 {pr_number} 리뷰 시작합니다.")
        
        pr_files, latest_commit_id = fetch_pr_data(repo, pr_number, github_token)
        if not pr_files:
            return
        
        overall_review = generate_reviews(
            pr_files, 
            repo, 
            pr_number, 
            latest_commit_id, 
            github_token
        )

        if overall_review:
            comment = get_total_comments_prompt(overall_review)
            post_pr_comment(
                repo,
                pr_number,
                comment,
                github_token
            )

    except KeyError as e:
        logger.error(f"환경 변수가 설정되지 않음: {str(e)}")
    except Exception as e:
        logger.error(f"예상치 못한 오류 발생: {str(e)}")

if __name__ == "__main__":
    main()
