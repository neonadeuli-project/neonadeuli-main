REVIEW_PROMPT = """
You have deep knowledge and expertise in Python, FastAPI for the back end, React and Next.js for the front.
Here is the new PR information.
- title: {title}
- description: {description}
- commit messages: {commit_messages}
- changed files: {changed_files}

Please understand and review the purpose and context of the change considering PR information and commit message.
Please be sure to thoroughly analyze and review the following format and provide a comprehensive review.
Find just one area of your current code that needs the most improvement and write it in the format below.
--------------------------------------------------------
## 🧑🏻‍💻 주요 기능

[핵심 기능, 입력 및 출력 예상, 처리하는 특정 예외 사례를 포함하여 이 파일의 주요 기능에 대한 간략한 설명을 제공하세요]

## 🔍 개선할 점

[성능 병목 현상, 가독성 문제, 보안 취약점 등 개선이 필요한 모든 영역을 나열합니다.]

## 📢 제안된 솔루션

1. 현재 코드

[문제가 있는 코드 조각]

2. 권장되는 변경

[업데이트된 코드 조각]

3. 변경 이유

[성능, 가독성, 보안 등을 고려하여 새로운 접근 방식이 더 나은 간략한 이유]
--------------------------------------------------------

Full Code: {all_code}

If you need to put in a code block, keep it brief, no more than 10 lines of code that needs improvement.
Please write one sentence within 70 characters, including the maximum space, that you need to explain.
If you write one sentence for readability, please write the next sentence in the next column instead of the next one.

The person receiving this feedback is a Korean developer.
Please make sure to follow the above format strictly in Korean, but please provide specific and constructive feedback.
"""

FILE_REVIEW_PROMPT = """
다음 {filename} 파일의 코드를 리뷰하고, 아래 형식으로 상세한 리뷰를 제공해주세요:

## {filename} 파일 리뷰

### 주요 기능
[파일의 주요 기능 설명]

### 좋은 점
[좋은 점 나열]

### 개선할 점
[개선이 필요한 점 나열]

### 제안 사항
[구체적인 개선 제안, 코드 예시 포함]

파일 내용:
{content}
"""

LINE_COMMENTS_PROMPT = """
다음 {filename} 파일의 코드를 리뷰하고, 중요한 라인에 대해 구체적인 코멘트를 제공해주세요. 
형식은 '라인 번호: 코멘트'로 해주세요.

{content}
"""

OVERALL_COMMENTS_PROMPT = """
## AI 코드 리뷰 요약

{overall_review}
"""

def get_review_prompt(all_code, pr_context, commit_messages, changed_files):
    formatted_commit_messages = "\n".join([f"- {msg}" for msg in commit_messages])
    return REVIEW_PROMPT.format(
        title=pr_context['title'],
        description=pr_context['description'],
        commit_messages=formatted_commit_messages,
        changed_files=changed_files,
        all_code=all_code
    )

def get_file_review_prompt(filename, content):
    return FILE_REVIEW_PROMPT.format(filename=filename, content=content)

def get_line_comments_prompt(filename, content):
    return LINE_COMMENTS_PROMPT.format(filename=filename, content=content)

def get_total_comments_prompt(overall_review):
    return OVERALL_COMMENTS_PROMPT.format(overall_review=overall_review)
    