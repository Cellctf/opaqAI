FROM python:3.8
WORKDIR /opaqAI/
COPY . /opaqAI/
RUN pip install -r requirements.txt -i https://pypi.mirrors.ustc.edu.cn/simple
CMD ["gunicorn","run:app","-c","gunicorn.conf.py"]
