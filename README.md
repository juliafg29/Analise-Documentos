# API de Validação e Extração de Dados de Documentos Pessoais

O projeto é parte de um Trabalho de Conclusão de Curso de Ciências da Computação - UFSC.

Objetivo: API para validação de documento completo, classificação de documento e extração de informações de documentos pessoais a partir de arquivos PDF.

Feito por: Julia F Gazolla (juliafg29)
Entregue em julho de 2026.

## Funcionalidades

* Recebimento de documentos via API REST.
* Processamento de documentos escaneados e natos digitais.
* Extração de informações por OCR.
* Geração de resultados estruturados em XML.
* Suporte a execução via Docker (recomendado) ou local com Python.

---

# Requisitos

Antes de executar o projeto, certifique-se de possuir os seguintes softwares instalados:

* Python 3.11 ou superior
* pip
* Docker
* Git

Verifique as instalações com:

```bash
python --version
pip --version
docker --version
git --version
```

---

# Clonando o Projeto

```bash
git clone https://github.com/juliafg29/Analise-Documentos.git
cd Analise-Documentos
```
---

# Execução com Docker

## 1. Construir a imagem

```bash
docker build -t analisador-documentos .
```

---

## 2. Executar o container

```bash
docker run -d \
  --name analisador-documentos \
  -p 8000:8000 \
  analisador-documentos
```

Verificar se está em execução:

```bash
docker ps
```

---

## 3. Visualizar logs

```bash
docker logs -f analisador-documentos
```

---

## 4. Parar o container

```bash
docker stop analisador-documentos
```

---

## 5. Remover o container

```bash
docker rm analisador-documentos
```
---

# Execução Local (Sem Docker)

## 1. Criar ambiente virtual

### Linux / MacOS

```bash
python3 -m venv venv
source venv/bin/activate
```

### Windows

```powershell
python -m venv venv
venv\Scripts\activate
```

---

## 2. Instalar dependências Python

```bash
pip install -r requirements.txt
```

---

## 3. Instalar dependências do sistema

### Ubuntu/Debian

```bash
sudo apt update

sudo apt install -y \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    tesseract-ocr-por \
    poppler-utils \
    ccache
```

### Windows

Instalar manualmente:

* Tesseract OCR
* Poppler

Adicionar ambos ao PATH do sistema.

---

## 4. Executar a API

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

A aplicação ficará disponível em:

```text
http://localhost:8000
```

Documentação Swagger:

```text
http://localhost:8000/docs
```

---

# Utilização da API

## Endpoint

```http
POST /documentos/analisar
```

---

## Parâmetros

| Campo        | Tipo    | Obrigatório | Descrição                                 |
| ------------ | ------- | ----------- | ----------------------------------------- |
| arquivo      | PDF     | Sim         | Documento PDF a ser processado            |
| tipo_entrada | String  | Não         | cnh_digital OU documento_escaneado        |
| pasta_saida  | String  | Não         | Diretório onde os resultados serão salvos |

Caso não informado, o sistema utilizará o comportamento padrão definido na aplicação.

---

# Exemplo de Requisição

## Linux / MacOS

```bash
curl -X POST "http://localhost:8000/documentos/analisar" \
  -F "arquivo=@/home/USER/documento.pdf" \
  -F "tipo_entrada=documento_escaneado" \
  -F "pasta_saida=home/USER/pasta_saida"
```

---

## Windows (PowerShell)

```powershell
curl.exe -X POST "http://localhost:8000/documentos/analisar" `
  -F "arquivo=@/home/USER/documento.pdf" `
  -F "tipo_entrada=documento_escaneado" `
  -F "pasta_saida=home/USER/pasta_saida"
```

---

## Exemplo mínimo

Como `tipo_entrada` e `pasta_saida` são opcionais:

```bash
curl -X POST "http://localhost:8000/documentos/analisar" \
  -F "arquivo=@documento.pdf"
```

---

# Exemplo de Resposta

```xml
<?xml version="1.0" ?>
<documento>
  <tipo_documento>CARTEIRA NACIONAL DE HABILITAÇÃO</tipo_documento>
  <dados_extraidos>
    <NomeCompleto confianca="96.0">JOÃO SILVA</NomeCompleto>
    <DataNascimento confianca="72.33">01/01/2001</DataNascimento>
    <LocalNascimento confianca="96.0">FLORIANOPOLIS</LocalNascimento>
    <RG confianca="94.0">12345</RG>
    <CPF confianca="80.5">123.456.789-00</CPF>
    <OrgaoEmissor confianca="77.0">SSP</OrgaoEmissor>
  </dados_extraidos>
  <arquivo_original>
    <nome_arquivo>doc.pdf</nome_arquivo>
    <formato>application/pdf</formato>
    <conteudo_base64>JVBERi0xLjcK(....)
  </arquivo_original>
</documento>
```

---

# Estrutura do Projeto

```text
.
├── app/
│   ├── main.py
│   ├── services/
│   ├── models/
│   └── ...
├── requirements.txt
├── Dockerfile
└── README.md
```

---

# Solução de Problemas

## Porta 8000 já está em uso

Alterar a porta:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

ou

```bash
docker run -p 8080:8000 analisador-documentos
```

---

## Verificar containers ativos

```bash
docker ps
```

---

## Reiniciar container

```bash
docker restart analisador-documentos
```

---

