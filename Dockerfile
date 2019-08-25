FROM python:3
WORKDIR /SimuladorAD
COPY . /SimuladorAD
RUN pip install -r requirements.txt
CMD ["python", "main.py", "fcfs"]
