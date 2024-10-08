REVIEW_PROMPT = """
다음은 해당 PR 정보입니다.
- 제목: {title}
- 설명: {description}
- 커밋 메시지: {commit_messages}
- 변경된 파일: {changed_files}

PR 정보와 커밋 메시지를 고려하여 변경 사항의 목적과 맥락을 이해하고 리뷰해 주세요.
철저히 분석 및 검토하여 반드시 아래와 같은 형식을 엄격하게 지켜서 종합적인 리뷰를 제공해주세요:
--------------------------------------------------------
## 전체 코드 리뷰

### 🧑🏻‍💻 개선할 점

- 개선이 필요한 점 최대 5가지

### 📢 개선을 위한 제안

- 구체적인 개선 방안

- 현재 코드

- 제안된 변경

- 이유
--------------------------------------------------------

전체 코드: {all_code}

응답은 꼭 위의 형식을 엄격하게 따라 작성해 주시되, 구체적이고 건설적인 피드백을 제공해 주세요.
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
    