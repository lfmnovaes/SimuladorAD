FROM faizanbashir/python-datascience:3.6
WORKDIR /SimuladorAD
COPY . /SimuladorAD
#RUN pip install -r requirements.txt
CMD ["python", "main.py", "fcfs", "0.4", "15000"]
