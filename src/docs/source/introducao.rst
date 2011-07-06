==========
Introdução
==========

--------------------------
Modelo de Dados de Usuário
--------------------------

Para visualizar o modelo de dados de usuários, utilizamos a
própria API do Passaporte Web. Assim, você já pode se familiarizar.

Todas as requisições feitas à nossa API são respondidas em formato JSON
(JavaScript Object Notation)

Utilizando o navegador
----------------------

Um navegador de sua preferência pode ser utilizado para acessar o nosso
modelo de usuário:

1. 
    Digite a URL https://app.passaporteweb.com.br/accounts/api/auth/ na barra 
    de endereço do seu navegador.

2. 
    Logo após. irá aparecer uma tela para digitar seu login e senha. Utilize o
    seu email e senha cadastrados no Passaporte Web.

3. 
    A resposta será um JSON com as suas informações de usuário descrito abaixo.

Utilizando a linha de comando
-----------------------------

1. 
    Para utilizar a linha de comando, digite:
    
    ::

        curl -u '<email_cadastrado>:<senha>' https://app.passaporteweb.com.br/accounts/api/auth/


2. 
    A resposta será o mesmo JSON descrito abaixo.


O Modelo
--------

Você receberá um modelo semelhante a esse:

::

   {
        "first_name": "Lima",
        "last_name": "Barreto",
        "nickname": "Fulano",
        "email": "lima.barreto@myfreecomm.com.br"
        "uuid": "7051a4dc-224f-423a-8a29-d23da90dc09a",
        "authentication_key": "$2a$12$gE4RqqgrAvd1uucWJcmYjulC4fGLVMnYq/lfcvr2KnOE22kOYqpvm", 
        "country": "BR",
        "gender": "M",
        "birth_date": "1881-05-13",
        "language": "por",
        "timezone": "America/Sao_Paulo",
        "cpf": "12345678912",
        "is_active": true,
        "services": {},
        "send_partner_news": true,
        "send_myfreecomm_news": true,
        "id_token": "e759db7c52e2d3ea5bf5b8340fa43fde37ed53e331ff4b6f",
        "update_info_url": "/profile/api/info/7051e4bc-224f-423a-8b29-d23da90dc09a/",
    } 


- Nome
    - Tipo: String com tamanho máximo de 50 caracteres
- Sobrenome
    - Tipo: String com tamanho máximo de 100 caracteres
- Apelido
    - Tipo: String com tamanho máximo de 50 caracteres
- *Email identidade*
    - Tipo: String de acordo com a `RFC2822`_
- *UUID identidade*
    - Tipo: String de acordo com a `RFC4122`_
    - Campo utilizado como identificador de um usuário do Passaporte Web
- Senha
    - Tipo: Hash calculada pelo algoritmo `bcrypt`_
- País
    - Tipo: String de acordo com a especificação `ISO3166`_.
    - Exemplo: Brasil: 'BR'
- Gênero
    - Tipo: Caractere
    - Opções: 'M' para masculino e 'F' para feminino
- Nascimento
    - Tipo: Date
    - Exemplo: '1990-07-03'
- Idioma
    - Tipo: String de acordo com a especificação `ISO639`_
- Fuso horário
    - Tipo: String de acordo com o `TimeZone`_ database
- CPF
    - Tipo: String numérica com tamanho exato de 11 dígitos
- Flag de ativação
    - Tipo: Booleano
- Serviços
    - Tipo: Dicionário de dados
    - Informações referentes aos serviços cadastrados pelo usuário no Passaporte Web.
- Envio de mala-direta de parceiros
    - Tipo: Booleano
- Envio de mala-direta da Myfreecomm
    - Tipo: Booleano
- Token de identidade
    - Token utilizado para autenticação do usuário na API
- URL de atualização de informações
    - URL para alterar informações do usuário na API
