# Simulador de fila M/M/1 
Avaliação e Desempenho - 2019-1

### Requisitos (para execução em container)

* Linux
* Docker

### Como usar

* Clonar o repositório ou fazer o download do zip do projeto.

* Entre na pasta do projeto

* Dentro da pasta do projeto, executar o seguinte comando para dar permissão de execução ao script:

```
chmod +x build-docker.sh

```

* Certifique-se de que o daemon do docker esta rodando:

```
sudo systemctl status docker
``` 

* Se o daemon do docker não estiver rodando, execute:

```
sudo systemctl start docker
``` 

* Por último, execute o script:

```
sudo ./build-docker.sh
```



