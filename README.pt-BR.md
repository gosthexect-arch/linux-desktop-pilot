<p align="center"><img src="docs/assets/hero.svg" alt="Linux Desktop Pilot — seu agente trabalhando nos seus aplicativos Linux" width="100%"></p>

# Linux Desktop Pilot

**Computer Use para Codex no Linux: observe a tela, use mouse e teclado e confira o resultado.**

[English](README.md) · [Instalação](#instalar-no-codex) · [Compatibilidade](#o-que-já-foi-validado) · [Contribuir](CONTRIBUTING.md)

Uma skill aberta para orientar o agente em aplicativos visíveis, no trabalho e
no dia a dia. Ela verifica o resultado de cada etapa e adapta a navegação quando
um atalho, clique ou caminho não funciona.

**O foco principal é Hyprland.** As integrações para GNOME e KDE Plasma usam um
runtime opcional e ainda precisam de validação em sessões reais.

## Instalar no Codex

Com o instalador do ecossistema skills, usando Node.js 22.20 ou superior:

```bash
npx skills add gosthexect-arch/linux-desktop-pilot --skill linux-visual-computer-use -a codex -g
```

Ou com Git e Python 3.9+, sem pacotes pip:

```bash
git clone https://github.com/gosthexect-arch/linux-desktop-pilot.git
cd linux-desktop-pilot
python3 linux-visual-computer-use/scripts/install.py
```

Escolha um método para evitar cópias duplicadas da skill. A instalação Python
respeita `CODEX_HOME`, usa `.codex/skills` por padrão e preserva backup em atualizações.
As dependências gráficas do sistema precisam estar disponíveis em ambos os métodos.

Abra uma nova conversa no Codex e peça:

```text
Use $linux-visual-computer-use para operar meu navegador pela interface.
Comece verificando o ambiente e confirme comigo qual página devo usar.
```

O nome técnico da skill permanece `linux-visual-computer-use`; a apresentação
do projeto e o nome exibido no cliente são **Linux Desktop Pilot**.

## Verificar o ambiente

Na pasta clonada:

```bash
python3 linux-visual-computer-use/scripts/desktop.py doctor
```

O diagnóstico não captura a tela nem envia entrada. Ele encontra um caminho
candidato, sem comprovar que a tarefa visual foi concluída.

Para instalar também o runtime MCP opcional, com npm/Node.js 18+:

```bash
python3 linux-visual-computer-use/scripts/install.py --with-native
```

[Guia detalhado de instalação e modelos](linux-visual-computer-use/references/portability.md)
· [Dependências dos ambientes](linux-visual-computer-use/references/backends.md)

## Exemplos de uso

**Navegador:**

```text
Use $linux-visual-computer-use no navegador aberto. Preencha o formulário
que eu indicar, confira os campos e pare antes de enviar.
```

**WhatsApp e comunicação:**

```text
Use $linux-visual-computer-use para preparar um rascunho na conversa
que eu selecionar. Confira destinatário e texto e pare antes de enviar.
```

**Blender:**

```text
Use $linux-visual-computer-use no projeto Blender aberto. Trabalhe pela
interface, preserve a cena existente e salve uma cópia separada.
```

WhatsApp e Blender são exemplos dos fluxos pretendidos; os testes reais nesses
aplicativos ainda estão pendentes. No modo visual, o agente usa a interface,
sem substituir a tarefa por APIs, DOM ou scripts de modelagem.

## O que já foi validado

| Área | Evidência atual |
| --- | --- |
| Hyprland / Wayland | Teste real no Chromium, em Omarchy / Hyprland 0.56.2 |
| Navegação | Clique, acentos, teclado, formulário local e links de seção |
| Gestos | Arraste com botão central + Shift e rolagem nos dois eixos |
| Proteções | Recusa após mudança de foco e verificações de estado nos testes |
| Auxiliares e instalação | 35 testes automatizados aprovados |
| GNOME / KDE | Integrações disponíveis; validação real pendente |
| Outros modelos, WhatsApp e Blender | Validação real pendente |

[Veja os resultados e limitações](docs/validation.md).

O conjunto modelo + cliente precisa carregar a skill, receber imagens reais e
executar ferramentas de GUI. A skill não fixa um modelo, mas também não promete
compatibilidade universal com todos os modelos, aplicativos ou distribuições.

## Contribua

Relatos de ambientes testados, correções, traduções e melhorias de navegação são
bem-vindos. Abra uma [issue](https://github.com/gosthexect-arch/linux-desktop-pilot/issues/new/choose)
ou envie um pull request seguindo [CONTRIBUTING.md](CONTRIBUTING.md).

```bash
python3 -m unittest discover -s tests -v
python3 tools/build_release.py
```

## Gratuito e aberto

Código e instruções estão sob a [licença MIT](LICENSE), com uso pessoal e
comercial permitido. Assinaturas ou uso de API do seu provedor de modelos são
separados. Veja os [avisos de terceiros](THIRD_PARTY_NOTICES.md).

Projeto independente, sem afiliação com OpenAI, Anthropic, Hyprland, Blender ou WhatsApp.
