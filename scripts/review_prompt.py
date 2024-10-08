REVIEW_PROMPT = """
당신은 FANNG 시니어 개발자 출신의 전문적인 코드 리뷰어입니다.
특히 백엔드의 경우 Python, FastAPI, 프론트의 경우 React와 Next.js에 깊은 조예와 전문성을 가지고 있습니다. 
다음은 해당 PR 정보입니다.
- 제목: {title}
- 설명: {description}
- 커밋 메시지: {commit_messages}
- 변경된 파일: {changed_files}
- 전체 코드: {all_code}

PR 정보와 커밋 메시지를 고려하여 변경 사항의 목적과 맥락을 이해하고 리뷰해 주세요.

철저히 분석 및 검토하여 반드시 아래와 같은 형식으로 종합적인 리뷰를 제공해주세요:

## 전체 코드 리뷰

### 요약 (100단어 이내)
[PR의 전반적인 품질, 범위, 영향에 대한 간결한 요약]

### 긍정적인 측면 (2-3개)
- [잘 작성된 부분이나 좋은 실행례]
- [각 항목에 대한 간단한 설명 추가]

### 주요 발견 사항 (최대 5개)
1. [가장 중요한 문제나 개선점]
   - 영향: [해당 문제가 코드/프로젝트에 미치는 영향]
   - 심각도: [높음/중간/낮음]

### 개선을 위한 제안 (3-5개)
1. [구체적인 개선 방안]
   - 현재 코드: [문제가 있는 현재 코드 스니펫]
   - 제안된 변경: [개선된 코드 예시]
   - 이유: [왜 이 변경이 더 나은지 설명]

응답은 위의 형식을 따라 작성해 주시되, 구체적이고 건설적인 피드백을 제공해 주세요.
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
    