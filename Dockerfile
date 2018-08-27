FROM pypy:3
LABEL maintainer="dengqi935@outlook.com"
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY KindleBot ./
COPY app.py ./
COPY ./example.toml ./kindlebot.toml

CMD ["pypy3", "./app.py", "-c", "./kindlebot.toml"]