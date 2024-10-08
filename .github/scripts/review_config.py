# 리뷰에서 제외할 파일 목록
IGNORED_FILES = [
    '.gitignore',
    'requirements.txt',
    'docker-compose.yml',
    'Dockerfile',
    'setup.cfg',
    'pyproject.toml',
    '.env.example',
    'README.md',
    'LICENSE',
]

# 리뷰에서 제외할 파일 확장자
IGNORED_EXTENSIONS = [
    '.md',  
    '.txt',  
    '.log',  
    '.json',  
    '.yaml', '.yml',  
]

# 중요 파일 판단 기준
IMPORTANT_FILE_CHANGE_THRESHOLD = 100
IMPORTANT_FILE_CHANGE_RATIO = 0.5

# 파일당 최대 코멘트 수
MAX_COMMENTS_PER_FILE = 3