#!/bin/bash

printf "\n\n#################################################\n"
printf "Construindo container e instalando dependências\n"
printf "#####################################################\n\n"
docker build -t simuladorad .
printf "\n\n##############################\n"
printf "INICIANDO SIMULAÇÃO FILA M/M/1\n"
printf "##################################\n\n"
sudo docker run simuladorad
printf "\n\n##############################\n"
printf "FIM\n"
printf "##################################\n\n"