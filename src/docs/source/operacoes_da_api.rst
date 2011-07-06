================
Operações da API
================

A API do Passaporte Web utiliza REST sobre SSL e disponibiliza dados no formato JSON.

Para execução dessas operações é necessário que o seu serviço seja autorizado pela Myfreecomm.

Operações relacionadas a identidades
------------------------------------

+---------------+-------------------------------------------------------------+
| Criação de identidades                                                      |
+===============+=============================================================+
| Método        |  POST                                                       |
+---------------+-------------------------------------------------------------+
| Utilizada por |  serviços                                                   |
+---------------+-------------------------------------------------------------+
| URI           |  /accounts/api/create/                                      |
+---------------+-------------------------------------------------------------+
| Parâmetros    | - *email*, senha, nome, sobrenome, credenciais do serviço   |
+---------------+-------------------------------------------------------------+
| Respostas     | -                                                           |
|               |    sucesso: 200 *OK* + dados do usuário + *token* SSO +     |
|               |    lista de serviços associados a esse usuario              |
|               | - falha:                                                    |
|               |    -                                                        |
|               |       Credenciais erradas: 401 *Unauthorized*               |
|               |    -                                                        |
|               |       Dados inválidos: 409 *Conflict* + lista de erros      |
|               |    -                                                        |
|               |       Método incorreto: 501 *Not Implemented*               |
+---------------+-------------------------------------------------------------+

===============================================================================

+---------------+-------------------------------------------------------------+
| Autenticação                                                                |
+===============+=============================================================+
| Método        |  GET                                                        |
+---------------+-------------------------------------------------------------+
| Utilizada por |  serviços em nome do usuário                                |
+---------------+-------------------------------------------------------------+
| URI           |  /accounts/api/auth/                                        |
+---------------+-------------------------------------------------------------+
| Parâmetros    | *email* e senha                                             |
+---------------+-------------------------------------------------------------+
| Respostas     | -                                                           |
|               |    sucesso: 200 *OK* + dados do usuário + *token* SSO +     |
|               |    lista de serviços associados a esse usuario              |
|               | - falha:                                                    |
|               |    -                                                        |
|               |       Credenciais erradas: 401 *Unauthorized*               |
|               |    -                                                        |
|               |       Método incorreto: 501 *Not Implemented*               |
+---------------+-------------------------------------------------------------+
| Casos de uso  |  - autenticação em um serviço web                           |
+---------------+-------------------------------------------------------------+

===============================================================================

+---------------+-------------------------------------------------------------+
| Leitura de dados de uma identidade                                          |
+===============+=============================================================+
| Método        | GET                                                         |
+---------------+-------------------------------------------------------------+
| Utilizada por | serviços                                                    |
+---------------+-------------------------------------------------------------+
| URI           | /profile/api/info/<*uuid* usuário>                          |
+---------------+-------------------------------------------------------------+
| Parâmetros    | credenciais do serviço                                      |
+---------------+-------------------------------------------------------------+
| Respostas     | -                                                           |
|               |    sucesso: 200 *OK* + dados do usuário +                   |
|               |    lista de serviços associados a esse usuario              |
|               | - falha:                                                    |
|               |    -                                                        |
|               |       Credenciais erradas: 401 *Unauthorized*               |
|               |    -                                                        |
|               |       Identidade inexistente: 404 *Not Found*               |
|               |    -                                                        |
|               |       Método incorreto: 501 *Not Implemented*               |
+---------------+-------------------------------------------------------------+
| Casos de uso  |  -                                                          |
|               |     obtenção dos dados do usuário para cadastro especifico  |
|               |     da aplicação.                                           |
+---------------+-------------------------------------------------------------+

===============================================================================

+---------------+-------------------------------------------------------------+
| Atualização de dados de uma identidade                                      |
+===============+=============================================================+
| Método        | PUT                                                         |
+---------------+-------------------------------------------------------------+
| Utilizada por | serviços                                                    |
+---------------+-------------------------------------------------------------+
| URI           | /profile/api/info/<*uuid* usuário>                          |
+---------------+-------------------------------------------------------------+
| Parâmetros    | credenciais do serviço, atributos atualizados               |
+---------------+-------------------------------------------------------------+
| Respostas     | -                                                           |
|               |    sucesso: 200 *OK* + dados do usuário +                   |
|               |    lista de serviços associados a esse usuario              |
|               | - falha:                                                    |
|               |    -                                                        |
|               |       Dados corrompidos: 400 *Bad Request*                  |
|               |    -                                                        |
|               |       Credenciais erradas: 401 *Unauthorized*               |
|               |    -                                                        |
|               |       Identidade inexistente: 404 *Not Found*               |
|               |    -                                                        |
|               |       Dados inválidos: 409 *Conflict* + lista de erros      |
|               |    -                                                        |
|               |       Método incorreto: 501 *Not Implemented*               |
+---------------+-------------------------------------------------------------+


Operações relacionadas a interação entre identidades e serviços
---------------------------------------------------------------

+---------------+-------------------------------------------------------------+
| Criação/atualização da relação entre um serviço e uma identidade            |
+===============+=============================================================+
| Método        | PUT                                                         |
+---------------+-------------------------------------------------------------+
| Utilizada por | serviços                                                    |
+---------------+-------------------------------------------------------------+
| URI           | /accounts/api/service-info/<*uuid* usuário>/<*service slug*>|
+---------------+-------------------------------------------------------------+
| Parâmetros    | credenciais do serviço, dados da associação ID ←→ serviço   |
+---------------+-------------------------------------------------------------+
| Respostas     | - sucesso:                                                  |
|               |     - Contratação: 201 *Created* + dados da associação      |
|               |     - Renovação: 200 *OK* + dados da associação             |
|               | - falha:                                                    |
|               |     - Credenciais erradas: 401 *Unauthorized*               |
|               |     - Identidade/serviço inexistente: 404 *Not Found*       |
|               |     - Parâmetros incorretos: 400 *Bad Request*              |
+---------------+-------------------------------------------------------------+
| Casos de uso  | - Aquisição de um serviço por uma identidade                |
|               | - Renovação de um serviço por uma identidade                |
|               | - Agendamento do cancelamento do servico de uma identidade  |
|               | - Armazenamento de dados para controle de acesso ao serviço |
+---------------+-------------------------------------------------------------+

===============================================================================

+---------------+-------------------------------------------------------------+
| Exclusão da relação entre um serviço e uma identidade                       |
+===============+=============================================================+
| Método        | PUT                                                         |
+---------------+-------------------------------------------------------------+
| Utilizada por | serviços                                                    |
+---------------+-------------------------------------------------------------+
| URI           | /accounts/api/service-info/<*uuid* usuário>/<*service slug*>|
+---------------+-------------------------------------------------------------+
| Parâmetros    | credenciais do serviço, dados da associação ID ←→ serviço   |
+---------------+-------------------------------------------------------------+
| Respostas     | - sucesso: 204 *No Content*                                 |
|               | - falha:                                                    |
|               |     - Credenciais erradas: 401 *Unauthorized*               |
|               |     - Identidade/serviço inexistente: 404 *Not Found*       |
|               |     - Parâmetros incorretos: 400 *Bad Request*              |
+---------------+-------------------------------------------------------------+

===============================================================================

+---------------+-------------------------------------------------------------+
| Status da relação entre um serviço e uma identidade                         |
+===============+=============================================================+
| Método        | GET                                                         |
+---------------+-------------------------------------------------------------+
| Utilizada por | serviços                                                    |
+---------------+-------------------------------------------------------------+
| URI           | /accounts/api/service-info/<*uuid* usuário>/<*service slug*>|
+---------------+-------------------------------------------------------------+
| Parâmetros    | credenciais do serviço                                      |
+---------------+-------------------------------------------------------------+
| Respostas     | - sucesso: 200 *OK* + dados da associação                   |
|               | - falha:                                                    |
|               |     - Credenciais erradas: 401 *Unauthorized*               |
|               |     - Identidade/serviço inexistente: 404 *Not Found*       |
|               |     - Parâmetros incorretos: 400 *Bad Request*              |
+---------------+-------------------------------------------------------------+
| Casos de uso  | - Obtenção de informação referente a um serviço             |
+---------------+-------------------------------------------------------------+
