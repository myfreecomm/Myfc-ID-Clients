==================
HTTP Basic e OAuth
==================

A API do Passaporte Web utiliza HTTP Basic e OAuth para autenticação de usuários.

Explicaremos as diferenças entre esses protocolos a seguir:


HTTP Basic
----------
O HTTP Basic (definido na `RFC2617`_) é parte do protocolo de comunicação HTTP. Essa forma de autenticação
utiliza parâmetros no cabeçalho da requisição HTTP para autenticar o usuário. Um
exemplo de de requisição utilizando o HTTP Basic foi dado na página anterior, onde os
parâmetros de autenticação foram passados por opção da ferramenta curl ou pela caixa
aberta no seu navegador.

Os parâmetros de cabeçalho de uma requisição com HTTP Basic são apenas login e 
senha do usuário. Todas as requisições na API do Passaporte Web são feitas via SSL, garantindo
a segurança dos dados.

OAuth
-----

A API do Passaporte Web utiliza o protocolo OAuth na versão 1 para operações utilizadas
por serviços para acesso a dados em nome do usuário. Esse protocolo utiliza as credenciais
de serviço validadas no cadastro de aplicações.

Para autenticar um usuário no protocolo OAuth são necessárias as credencias do serviço
e as credenciais de autorização do usuário para utilização do serviço no Passaporte Web.
É utilizado o seguinte modelo para a validação de serviços na API do Passaporte Web.

Um exemplo de utilização do OAuth para buscar informações do usuário é:

::

    curl -u '<token_da_aplicação>:<secret_do_serviço>' http://localhost:8001/profile/api/info/<token_da/<uuid_do_usuário>



Referências
-----------
- `RFC2617 <http://www.faqs.org/rfcs/rfc2617.html>`_
