FROM python:3.6
RUN adduser --disabled-login app
WORKDIR /home/app
COPY . .
RUN pip install -r requirements.txt -i https://pypi.doubanio.com/simple/
RUN chmod -R +x .