================
*Single Sign On*
================

O *Single Sign On* (SSO) é um mecanismo pelo qual torna-se possível que um usuário 
obtenha acesso a múltiplos serviços após autenticar-se somente uma vez 
em qualquer um destes serviços.


Fluxo do *Single Sign On*
-------------------------

- 
    O usuário acessa a aplicação desejada. 

- 
    A aplicação checa se este usuário já possui uma sessão ativa. Caso não 
    exista, efetua uma requisição para a url de requisição de credenciais 
    temporárias no sistema SSO (/sso/initiate), fornecendo sua identificação e 
    uma url de callback.

- 
    O sistema de SSO valida as credenciais do serviço e, em caso de sucesso, 
    responde à requisição com um conjunto de credenciais temporárias.

-
    A aplicação redireciona o usuário para a url de autenticação no sistema 
    SSO, adicionando à requisição a credencial temporária obtida na requisição 
    anterior.

-
    O sistema de SSO checa se este usuário já possui uma sessão ativa. Caso 
    não exista, exibe ao usuário uma página onde o mesmo pode se autenticar.
    
-
    Após a autenticação do usuário, é feita uma consulta ao Passaporte Web para checar 
    se existe uma associação deste usuário com o serviço que solicitou sua 
    autenticação. Em caso negativo, é exibida uma tela na qual o usuário é 
    notificado que tal serviço solicitou acesso a seus dados. O usuário tem a 
    opção de permitir o acesso permanentemente, permitir o acesso somente nesta
    sessão, ou negar o acesso a seus dados. Caso o usuário permita o acesso 
    permanentemente, deve ser criada uma associação entre o usuário e o serviço.

- 
    Caso o usuário não permita o acesso a seus dados, o processo de login é 
    finalizado. Caso contrário o usuário é redirecionado para a url de callback
    fornecida pela aplicação cliente no inicio do processo, adicionando a 
    credencial temporária do serviço e um verificador.

-
    A aplicação extrai a credencial e o verificador e efetua uma requisição 
    para a url de validação de tokens no sistema SSO. 

- 
    O sistema de SSO valida os tokens e responde à requisição com um conjunto 
    de credenciais que possibilitam o acesso aos dados do usuário.

- 
    De posse destas informações, a aplicação cliente solicita ao sistema de SSO
    os dados do usuário, de forma a autenticá-lo localmente.



URI's
````````````````````````````````````````````````````

-
    Ambiente de produção do passaporte web: `<https://app.passaporteweb.com.br>`_

-
    Solicitação de request token: /sso/initiate

-
    Autorização de acesso: /sso/authorize

-
    Solicitação de access token: /sso/token



Considerações para aplicações cliente
`````````````````````````````````````

Para uso do SSO no Passaporte Web, os serviços parceiros devem utilizar o protocolo
OAuth definido abaixo:

Logout
------

Para efetuar o logout no serviço e no passaporte web, é recomendado o seguinte 
procedimento:

#.
    Efetue o logout na sua aplicação

#.
    Redirecione o usuário para a url de logout do Passaporte Web, fornecendo no 
    parâmetro 'next' a url de acesso à sua aplicação. Exemplo:

    ::

        https://app.passaporteweb.com.br/accounts/logout?next=http://meuservico.minhaempresa


Token de identificação
----------------------

Para utilizar o *Single Sign On* implementamos um token para identificar os usuários
do Passaporte Web. Este token se encontra no modelo de dados apresentado na Introdução
desta documentação.
