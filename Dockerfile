FROM python:3.8.16-buster

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD [ "streamlit", "run", "marathiui.py", "--server.port", "8501" ]
