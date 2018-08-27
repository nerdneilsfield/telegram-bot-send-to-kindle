FROM pypy:3
LABEL maintainer="dengqi935@outlook.com"
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["pypy3", "./all-in-one.py", "-c", "./example.toml"]