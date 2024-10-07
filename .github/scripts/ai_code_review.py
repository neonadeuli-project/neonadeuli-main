import json
import os
import requests
import re
import logging
from scripts.review_prompt import generate_review_prompt

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

def review_code(review_prompt):
    # prompt = review_prompt.format(code=pr_content)
    url = 'http://localhost:11434/api/generate'
    data = {
        "model": "llama3.1",
        "prompt": review_prompt,
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

    line_numbers = get_line_numbers(patch)
    
    # 라인 코멘트 파싱 및 게시
    for comment in line_comments.split('\n'):
        match = re.match(r'(\d+):\s*(.*)', comment)
        if match:
            line_num, comment_text = match.groups()
            try:
                line_num = int(line_num)
                if 0 <= line_num - 1 < len(line_numbers):
                    position = line_numbers[line_num - 1]
                    post_single_comment(line_num, comment_text, position)
                else:
                    logger.warning(f"라인 {line_num}이 유효한 범위를 벗어났습니다.")
            except ValueError:
                logger.warning(f"잘못된 라인 번호 형식: {line_num}")
        else:
            logger.warning(f"파싱할 수 없는 코멘트 형식: {comment}")

    logger.info("모든 라인 코멘트 처리 완료")

def parse_and_post_review(repo, pr_number, commit_sha, review_result, token):
    lines = review_result.split('\n')
    overall_review = ""
    current_file = ""
    file_review = ""
    line_comments = {}

    for line in lines:
        if line.startswith("1. 전체 리뷰:"):
            overall_review = line[len("1. 전체 리뷰:"):].strip()
        elif line.startswith("2. 중요 파일 상세 리뷰:"):
            continue
        elif line.startswith("   ") and ": " in line:
            filename, _ = line.strip().split(": ", 1)
            current_file = filename
            file_review = ""
            line_comments[current_file] = {}
        elif line.startswith("   - 전반적인 리뷰:"):
            file_review = line[len("   - 전반적인 리뷰:"):].strip()
        elif line.startswith("   - 라인별 코멘트:"):
            continue
        elif line.startswith("     ") and ": " in line:
            line_num, comment = line.strip().split(": ", 1)
            line_comments[current_file][int(line_num)] = comment

    # 전체 리뷰 게시
    post_pr_comment(repo, pr_number, f"전체 리뷰:\n{overall_review}", token)

    # 파일별 리뷰 및 라인 코멘트 게시
    for file, comments in line_comments.items():
        file_content = f"파일: {file}\n\n전반적인 리뷰:\n{file_review}\n\n라인별 코멘트:"
        for line_num, comment in comments.items():
            file_content += f"\n{line_num}: {comment}"
        
        post_review_comment(repo, pr_number, commit_sha, file, 1, file_content, token)

        # 개별 라인 코멘트 게시
        for line_num, comment in comments.items():
            post_review_comment(repo, pr_number, commit_sha, file, line_num, comment, token)

    logger.info("모든 리뷰 코멘트가 성공적으로 게시되었습니다.")

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
        latest_commit_id = get_latest_commit_id(repo, pr_number, github_token)

        all_code = ""
        important_files_content = {}

        if pr_files:
            important_files = [f for f in pr_files if f['changes'] > 50]

            for file in pr_files:
                if file['status'] != 'removed':  
                    logger.info(f"파일 리뷰 중: {file['filename']}")
                    content = requests.get(file['raw_url']).text
                    all_code += f"File: {file['filename']}\n{content}\n\n"
                    if file in important_files:
                        important_files_content[file['filename']] = content

            # 새로운 리뷰 프롬프트 생성
            review_prompt = generate_review_prompt(all_code, important_files_content)

            # 전체 코드에 대한 리뷰
            overall_review = review_code(review_prompt)

            # 리뷰 결과 파싱 및 코멘트 게시
            parse_and_post_review(repo, pr_number, latest_commit_id, overall_review, github_token)

            # # 중요 파일에 대한 상세 리뷰
            # detailed_reviews = []
            # for file in important_files:
            #     content = requests.get(file['raw_url']).text
            #     review = review_code(content)
            #     detailed_reviews.append(f"File: {file['filename']}\n{review}\n\n")

            #     line_comments_prompt = f"다음 {file['filename']} 파일의 코드를 리뷰하고, 중요한 라인에 대해 구체적인 코멘트를 제공해주세요. 형식은 '라인 번호: 코멘트'로 해주세요.\n\n{content}"
            #     line_comments = review_code(line_comments_prompt)

            #     post_line_comments(
            #         repo, 
            #         pr_number, 
            #         latest_commit_id, 
            #         file['filename'], 
            #         file['patch'], 
            #         line_comments, 
            #         github_token
            #     )

            # 전체 요약 생성
            # final_summary = f"Overall Review:\n{overall_review}\n\nDetailed Reviews:\n{''.join(detailed_reviews)}"

            # post_pr_comment(
            #     repo,
            #     pr_number,
            #     final_summary,
            #     github_token
            # )

        else:
            logger.warning("파일을 찾을 수 없거나 PR 파일을 가져오는 데 실패했습니다.")

    except KeyError as e:
        logger.error(f"환경 변수가 설정되지 않음: {str(e)}")
    except Exception as e:
        logger.error(f"예상치 못한 오류 발생: {str(e)}")

if __name__ == "__main__":
    main()
