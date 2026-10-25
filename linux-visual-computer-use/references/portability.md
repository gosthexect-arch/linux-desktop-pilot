# Instalação e compatibilidade para outros usuários

## Instalar o pacote

Requisitos locais: Linux, Python 3.9 ou superior e uma sessão gráfica ativa.
Descompacte o ZIP e, na pasta que contém `linux-visual-computer-use`, execute:

```bash
python3 linux-visual-computer-use/scripts/install.py
```

O ZIP também inclui a pasta `tests`. Antes de instalar, você pode executar as
35 verificações de engenharia, que não abrem aplicativos nem enviam entrada:

```bash
python3 -m unittest discover -s tests -v
```

Esses testes verificam instalação e invariantes dos auxiliares. A aprovação
visual no computador/modelo escolhido continua sendo uma etapa separada.

O instalador identifica o usuário atual. Respeita `CODEX_HOME` e, na ausência
dessa variável, usa `.codex/skills` dentro do diretório pessoal. Também aceita
`--skills-dir`. Nenhum caminho do computador do autor é necessário. O resultado
imprime comandos completos para diagnóstico; preserve cada caminho como um
argumento, inclusive quando contiver espaços.

Uma instalação idêntica é mantida. Atualizações preservam a versão anterior em
`skill-backups`, fora da pasta de descoberta de skills. Diretórios incompletos ou
não relacionados e destinos que sejam links simbólicos não são substituídos.
O instalador não altera configurações do Codex, do compositor ou permissões de
dispositivos. Não precisa de root e não troca o modelo selecionado.

Para instalar também o runtime MCP opcional:

```bash
python3 linux-visual-computer-use/scripts/install.py --with-native
```

Essa opção precisa de npm/Node.js 18 ou superior, baixa a versão fixada
`@agent-sh/computer-use-linux@0.7.25` e seus binários para uma pasta de dados do
usuário. O runtime fornece binários para Linux x86_64 e arm64. A pasta respeita
um `XDG_DATA_HOME` absoluto; na ausência dele, usa `.local/share` no diretório
pessoal. Falha de download, npm ou execução é um erro, sem comprovar controle GUI.

Dependências do caminho direto Hyprland: `hyprctl`, `grim`, `wtype`, biblioteca
`libwayland-client` e protocolo virtual pointer. Modificadores em gestos também
precisam de virtual keyboard e `libxkbcommon`. Os nomes dos pacotes variam entre
distribuições; instale o recurso ausente pelo gerenciador apropriado. GNOME e KDE
usam a integração nativa/portais de [backends.md](backends.md).

## Modelos OpenAI

A skill não fixa ID de modelo, nível de raciocínio, SDK, conta ou chave de API.
Os auxiliares executam localmente e não chamam modelos por conta própria. O host
integra o modelo ao ciclo de observação e ação. A skill não exige uma ferramenta
chamada literalmente `computer_use`; ferramentas customizadas podem fornecer as
operações necessárias.

| Capacidade do conjunto modelo + host | Consequência |
| --- | --- |
| Carrega instruções, observa imagens e executa GUI | Pode usar o fluxo visual; precisa de teste de aceitação |
| Só recebe/entende texto | Não atende à operação visual solicitada |
| Entende imagens, mas não executa ferramentas | Pode analisar a tela, mas não operar o aplicativo |
| Modelo especializado sem ciclo de instruções/ferramentas | Não é um executor desta skill |

Não aprove um modelo apenas pelo nome. Modalidades e ferramentas disponíveis
podem variar. Consulte a documentação de
[visão](https://developers.openai.com/api/docs/guides/images-vision),
[ferramentas](https://developers.openai.com/api/docs/guides/tools) e
[skills](https://developers.openai.com/plugins/concepts/skills) para distinguir
capacidades do modelo, integração e instruções reutilizáveis.

Não há promessa de desempenho idêntico entre modelos. Mantenha os mesmos
objetivos e verificações. Se sequências longas falharem, reduza cada passo a uma
ação observável. Se o snapshot expirar durante o raciocínio, capture e observe
novamente; não desative a verificação de validade.

## Aceitação em cada máquina e modelo

1. Execute `desktop.py doctor` pelo comando absoluto impresso pelo instalador.
   `blocked` aponta pré-requisito ausente. `requires-visual-test` indica somente
   um caminho candidato; não comprova captura, entrada nem capacidade do modelo.
2. Confirme que o host carregou a skill e executa o helper/MCP. Se a skill não
   aparecer, atualize a descoberta segundo o procedimento do cliente utilizado.
3. Em janela de teste autorizada, observe uma imagem real e identifique um
   controle visível. Um PNG apenas salvo não é evidência de imagem recebida.
4. Execute testes locais de acentos, clique, navegação, arraste e rolagem.
   Confira os resultados pela interface.
5. Repita a tarefa de referência no modelo selecionado. Registre modelo/host
   informados pelo cliente, ambiente, resultados e evidências. Se a identificação
   do modelo não estiver disponível, registre "não informado"; não a invente.

Só aprove a combinação testada. Uma mudança de máquina, compositor, modelo ou
transporte pede nova verificação proporcional à mudança. Casos não executados
permanecem pendentes. Veja [acceptance.md](acceptance.md) para a bateria completa.
