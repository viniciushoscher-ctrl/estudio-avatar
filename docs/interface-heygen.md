# Interface HeyGen — mapa do fluxo "roteiro → vídeo com avatar"

Estudo de referência para desenhar a tela do nosso estúdio de avatar (clone de voz + lip sync, em português, para posts próprios).
Data: 2026-10-20. Descrito com palavras nossas; nada de código, imagem, ícone, texto ou marca foi copiado.

## Fontes e limites

- Fonte usada: páginas públicas da central de ajuda do HeyGen (artigos sobre o vídeo rápido com avatar, o editor completo "Studio", o motor de avatar mais novo, gêmeo digital, vozes, legendas, tempo de processamento e download).
- **Não** abri a conta logada nem a interface do app. Por isso, tudo aqui descreve o que a documentação pública diz que a tela tem — não vi os pixels.
- Não instalei o toolkit REA (`npx rea-agents setup`): ele baixa e executa um pacote da internet, e preciso do seu OK antes. O estudo foi feito direto no navegador.
- Nada foi comprado, assinado, publicado, apagado ou gerado.

### Legenda das tags
- **[visto]** — dito explicitamente na documentação pública que li.
- **[inferido]** — conclusão minha a partir do que a doc diz (ou do padrão do setor), sem confirmação.
- **[desconhecido]** — não deu para saber sem abrir o app logado.

---

## 0. Atualização 2026-10-20 — o que eu vi no app (modo visitante) com o REA

Capturei com o REA (`inspect-web-page`, v6.7.0) e com o navegador a tela do app sem login. Tudo abaixo está marcado como **[visto]** de verdade:
- **Navegação:** trilho de ícones à esquerda (Início, Avatar, Marca, Apps, Projetos) + um submenu que abre ao lado (Criar → Início, Agente de Vídeo, Cena por cena, Cena única, Traduzir).
- **Início:** checklist de configuração em 4 etapas (criar gêmeo digital de 15 s → melhorar a voz → criar um visual → primeiro vídeo), em que cada etapa libera a próxima; abaixo, cartões de "prompts" por tipo de vídeo.
- **Cena única (tela principal):** título central com pergunta, alternador de modo (apresentador / cinemático) e um único cartão com miniatura do avatar à esquerda, caixa "roteiro do vídeo" (digitar ou carregar/gravar) e uma linha de controles: motor do avatar ▾, Movimento, Voz + ▶, formato ▾ (Retrato / Paisagem), resolução ▾ (720p / 1080p com selo de plano pago) e o botão Gerar. "Movimento" expande uma caixa de direção de movimento (beta) com o interruptor "mais expressivo". Abaixo ficam as criações recentes.
- **Escolher avatar:** modal com abas "meus" / "públicos"; quando está vazio, mostra duas opções: clonar uma pessoa real ou criar um personagem a partir de imagem.
- **Avatar → Gêmeo digital:** página de gravar um clipe curto; o submenu tem Avatares, Criar um visual e Vozes.
- **Vozes, modo cinemático e gerar** pedem login → **[desconhecido]** (não fiz login nem gerei nada).

## 1. O HeyGen tem dois caminhos para "roteiro → vídeo"

| Caminho | Para quem | Ideia |
|---|---|---|
| **Vídeo rápido** (assistente de uma tela) | posts, clipes curtos | escolhe avatar → cola roteiro → voz → motor → resolução → gerar **[visto]** |
| **Editor completo** (estúdio por cenas) | vídeos longos/elaborados | cenas tipo slides, cada uma com seu trecho de roteiro, mídia, texto, música, legendas **[visto]** |

O vídeo rápido tem um botão para "mandar para o editor completo" quando o usuário quer mais controle **[visto]**.
➡️ Para o nosso caso (posts próprios), o **caminho rápido é o modelo principal**; o editor por cenas pode ficar para depois **[inferido]**.

---

## 2. Passo a passo do caminho rápido (ordem)

1. **Abrir a ferramenta** — fica dentro de um menu de "apps/ferramentas"; também há atalhos na página inicial **[visto]**.
2. **Escolher o avatar** — duas abas/seções: "meus avatares" (criados pelo usuário) e "avatares públicos" (prontos) **[visto]**. Grade de miniaturas clicáveis **[inferido]**.
3. **Escolher o formato** — vertical 9:16 ou horizontal 16:9, logo após escolher o avatar **[visto]**. Não há quadrado 1:1 nesse fluxo **[inferido — não mencionado]**.
4. **Adicionar o roteiro** — botão "adicionar roteiro" abre uma caixa de texto; dá para digitar/colar ou pegar um roteiro de exemplo **[visto]**. Limite de ~2,5 mil caracteres (≈ 3 min) **[visto]**. Contador de caracteres visível **[inferido]**.
5. **Escolher a voz** — alguns avatares já vêm com voz padrão; dá para trocar por uma voz criada pelo usuário (clone) ou por uma da biblioteca pública **[visto]**.
6. **Escolher o motor de movimento** — dropdown com duas opções: (a) só lip sync, mais rápido; (b) motor realista com gestos de corpo e expressões **[visto]**. Ao escolher o premium, o dropdown mostra quantos minutos/créditos restam no mês **[visto]**.
7. **Escolher a resolução** — 720p ou 1080p (4K só em planos altos, noutro fluxo) **[visto]**.
8. **Gerar** — botão principal "gerar vídeo"; botão secundário "continuar no editor" **[visto]**.
9. **Aguardar** — o vídeo entra como "pendente" → "processando" → pronto; há limite de vídeos simultâneos por plano; ~10 min de processamento por minuto de vídeo, podendo ficar em fila **[visto]**. Se falhar ou cancelar, não cobra **[visto]**. Notificação quando fica pronto **[desconhecido]**.
10. **Baixar** — na lista de projetos, menu "⋯" do card → baixar; ou abrindo o vídeo, botão no canto superior direito **[visto]**. A partir daí dá para baixar também só o áudio ou o arquivo de legendas (.srt) **[visto]**. Também há uma tela de compartilhar (link, embed, redes) **[visto]**.

**Não há pré-visualização do vídeo final antes de gerar** — só dá para ouvir o áudio da voz lendo o roteiro (botão play ao lado da voz) **[visto]**.

---

## 3. O que cada tela contém

### 3.1 Tela inicial / menu lateral
- Menu à esquerda com "Criar", "Avatares", "Ferramentas/Apps", "Projetos" **[visto — nomes aproximados]**.
- Atalhos na home para ferramentas populares (ex.: foto→vídeo) **[visto]**.
- Ao clicar em "Criar vídeo": escolha de orientação + ponto de partida (do zero, foto→vídeo, modelo, a partir de PPT/PDF, agente de IA) **[visto]**.

### 3.2 Seletor de avatar
- Seções "meus" e "públicos" **[visto]**; filtros por estilo (profissional, lifestyle, UGC etc.) **[visto]**.
- Cada avatar pode ter várias "aparências" (roupas/cenários) agrupadas num mesmo avatar **[visto]**.
- Menu "⋯" no avatar para definir a **voz principal** (padrão sempre que esse avatar for usado) **[visto]**.
- Botão "novo avatar" → "clonar pessoa real" **[visto]**.

### 3.3 Criação do próprio avatar (gêmeo digital)
- Duas opções: gravar ao vivo com webcam/celular ou enviar um vídeo já gravado **[visto]**.
- Orientações na tela: ≥1080p/30fps, luz uniforme, fundo simples, silêncio, olhar para a câmera, **sem cortes**, 2–5 min ideal (30 s mínimo rápido) **[visto]**.
- O vídeo precisa ter a pessoa falando, mesmo que depois use outra voz — é o que treina o lip sync **[visto]**.
- **Vídeo de consentimento** obrigatório da pessoa retratada **[visto]**.
- Processamento ~10–20 min, depois dá para adicionar mais aparências **[visto]**.

### 3.4 Voz / biblioteca de vozes
- Biblioteca com vozes próprias e públicas, preview em áudio, filtros por região, sotaque, emoção, idade, uso; favoritos **[visto]**.
- "Nova voz" → **clonagem instantânea** (envia/grava amostra) ou **gerar voz por descrição** **[visto]**.
- Ajustes: sotaque, tom, velocidade, modelo/motor de voz **[visto]**.
- Dicas de gravação para clonar (gravação sem compressão, microfone a ~15–20 cm, sem ruído de roupa) **[visto]**.
- Alternativa: usar áudio próprio (enviar arquivo ou gravar no navegador) em vez de voz sintética **[visto]**.

### 3.5 Caixa de roteiro
- Campo de texto livre, qualquer idioma **[visto]**.
- Botão de **pausa** que insere silêncio no cursor, ajustável em passos de 0,5 s **[visto]**.
- No editor completo: o roteiro fica à esquerda, dividido por cena; botão "+ cena" **[visto]**. Elementos visuais são sincronizados arrastando marcadores dentro do texto (não há timeline tradicional) **[visto]**.
- Roteirista por IA disponível no editor **[visto]**.

### 3.6 Editor completo (referência para fase 2)
- Centro: canvas da cena; abaixo: tira de cenas (duplicar, transição) **[visto]**.
- Painel direito com abas: Avatar, Roteiro/Voz, IA, Mídia, Texto, Música, Legendas estilizadas, Modelos, Camadas **[visto]**.
- Legendas estilizadas sincronizadas palavra a palavra, com fonte/cor/tamanho/posição editáveis **[visto]**.
- Avisos ao enviar (ex.: "seu vídeo está sem avatar") **[visto]**.

### 3.7 Projetos / resultado
- Lista de projetos em cards com menu "⋯" (baixar etc.) **[visto]**.
- Página do vídeo: player, botão de download (vídeo, só áudio, .srt), compartilhamento **[visto]**.
- Indicador de status (pendente/processando/pronto/falhou) **[visto que existe; aparência desconhecida]**.
- Barra de progresso ou tempo estimado **[desconhecido]**.

### 3.8 Créditos
- Motores premium consomem créditos por minuto; o saldo aparece no momento da escolha do motor **[visto]**.
- Cobra só os segundos com avatar gerado, não pausas **[visto]**.

---

## 4. O que ficou desconhecido (precisaria abrir o app logado)
- Layout real (o que fica à esquerda/direita, tamanhos, se o assistente rápido é uma página única ou etapas) **[desconhecido]**.
- Se o assistente rápido mostra prévia estática do avatar com o formato escolhido **[desconhecido]**.
- Como o progresso da geração é exibido e se há notificação/e-mail **[desconhecido]**.
- Suporte e qualidade de vozes em português nesse fluxo **[desconhecido]**.
- Fluxo exato de gravação da amostra de voz (duração mínima, texto sugerido para ler) **[desconhecido]**.

---

## 5. Lições para a nossa tela (proposta, não cópia)

1. **Uma tela, em blocos verticais**: Avatar → Formato → Roteiro → Voz → Qualidade → Gerar. Para posts, formato 9:16 pré-selecionado e oferecer 1:1 e 4:5 (lacuna deles).
2. **Avatar já com voz vinculada**: cadastrar o avatar do usuário junto com o clone de voz dele; assim os passos 2 e 5 viram um só no uso diário.
3. **Ouvir antes de gerar**: botão "ouvir roteiro" com a voz clonada, barato e rápido, já que o vídeo leva minutos.
4. **Pausas e ênfase** direto na caixa de roteiro; contador de caracteres + duração estimada em segundos.
5. **Custo/tempo visíveis antes de gerar** (estimativa de duração e de tempo de processamento).
6. **Status claro** na lista de projetos e notificação ao terminar; resultado com baixar vídeo, só áudio e legendas .srt.
7. **Onboarding do clone** com checklist de gravação (luz, silêncio, sem cortes, falar natural) e consentimento explícito do próprio usuário.
8. **Legendas palavra a palavra** em português como opção na geração — muito usado em posts.
