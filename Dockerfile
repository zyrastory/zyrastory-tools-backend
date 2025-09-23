FROM python:3.11-slim
WORKDIR /app

# 複製 pyproject.toml 與 poetry.lock
COPY pyproject.toml poetry.lock /app/

# 安裝 Poetry
#RUN pip install --no-cache-dir poetry

# 生成 requirements.txt 並安裝依賴
#RUN poetry export -f requirements.txt --without-hashes | pip install --no-cache-dir -r /dev/stdin


RUN pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false \
    && poetry install --only main --no-root



# 複製專案程式碼
COPY . /app

RUN mkdir -p /app/tmp

# 啟動命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]