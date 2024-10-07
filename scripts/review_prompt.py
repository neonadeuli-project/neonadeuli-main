import json


REVIEW_PROMPT_TEMPLATE = """전체 코드에 대한 간략한 리뷰를 제공하고, 다음 중요 파일들에 대해 상세한 리뷰와 라인별 코멘트를 제공해주세요:

전체 코드:
{all_code}

중요 파일들:
{important_files}

응답 형식:
1. 전체 리뷰: [여기에 전체 리뷰 내용]
2. 중요 파일 상세 리뷰:
   [파일명1]:
   - 전반적인 리뷰: [리뷰 내용]
   - 라인별 코멘트:
     [라인 번호]: [코멘트]
     ...
   [파일명2]:
   ...
"""

def generate_review_prompt(all_code, important_files_content):
    return REVIEW_PROMPT_TEMPLATE.format(
        all_code=all_code,
        important_files=json.dumps(important_files_content, indent=2)
    )