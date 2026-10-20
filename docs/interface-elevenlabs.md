# Interface ElevenLabs — mapa da clonagem de voz e do texto para fala

Data: 2026-10-20. Descrito com palavras nossas; nada de código, imagem, ícone, texto ou marca foi copiado.

## Fontes e limites
- REA v6.7.0 (`inspect-web-page`) na página pública de texto para fala.
- Guias públicos do produto: clone instantâneo, texto para fala, biblioteca de vozes, criação de voz por descrição e trocador de voz.
- O app (`/app`) pede login logo de cara. Não fiz login, então o layout interno do app está como **[desconhecido]** e o fluxo vem da documentação deles.

Tags: **[visto]** = vi na página ou está dito na documentação · **[inferido]** = conclusão minha · **[desconhecido]**.

## 1. Clone instantâneo de voz (passo a passo)
1. Menu lateral **Vozes → botão "+"**, que abre um modal com três tipos: clone instantâneo, clone profissional e criação por descrição **[visto]**.
2. **Enviar ou gravar áudio** seguindo as instruções da tela. Dá para usar várias amostras **[visto]**. O recomendado é **pelo menos 1 minuto**, com voz consistente, volume equilibrado e o mesmo estilo de fala que você vai querer na saída **[visto]**.
3. **Detalhes:** nome, rótulos (idioma, tom etc.) e uma confirmação de que você tem direito e consentimento para clonar aquela voz. Depois, salvar **[visto]**.
4. **Usar:** em "Minhas vozes" → "usar voz" **[visto]**.
- Indicador de quanto áudio já foi enviado **[inferido]**.
- Remoção de ruído de fundo existe no trocador de voz **[visto]**; se existe também no clone, não sei **[desconhecido]**.

## 2. Texto para fala
- Fluxo: texto na caixa grande → escolher a voz → ajustes (opcional) → Gerar **[visto]**.
- **Ordem de impacto no resultado:** voz > modelo > ajustes **[visto]**.
- **Modelos:** família padrão (mais qualidade) e família rápida (baixa latência), em versões multilíngues **[visto]**.
- **Ajustes:** velocidade, estabilidade, semelhança, exagero de estilo e reforço do falante **[visto]**.
- **Pausas e marcações:** aceitam tags de pausa, de emoção e de pronúncia **[visto]**.
- Download em MP3, com WAV/FLAC dependendo do plano **[visto]**. Histórico das gerações **[inferido]**.
- Custo em caracteres, exibido antes de gerar **[visto]**.

## 3. Biblioteca de vozes
- Abas Minhas vozes / Explorar; busca por nome, palavra ou até por um áudio enviado **[visto]**.
- Filtros: idioma, sotaque, categoria de uso (conversa, narração, redes sociais, educação, anúncio…), gênero, idade e qualidade **[visto]**.
- Ações em cada voz: ouvir, usar, salvar e coleções **[visto]**.

## 4. Criar voz por descrição
- Você escreve um prompt descrevendo idioma, gênero, idade, tom e ritmo, mais um texto de prévia → recebe **3 opções** → escolhe uma e salva **[visto]**.

## 5. Trocador de voz
- Envia ou grava um áudio (até 5 min) → escolhe a voz de destino → gera. O resultado mantém o ritmo, a emoção e o sotaque de quem gravou. Tem a opção "remover ruído de fundo" **[visto]**.

## 6. Como entrou no nosso estúdio (junção com o fluxo do HeyGen)
- Novo item **Voz** no menu lateral, com as seções Texto para fala, Minhas vozes e Trocador de voz.
- **Clone instantâneo** com várias amostras (gravar ou enviar), medidor até 1 minuto, rótulos, remoção de ruído e consentimento. Ao salvar, a voz já fica ligada ao seu avatar.
- **Criar por descrição** com 3 opções de prévia.
- **Texto para fala** com voz, modelo, os 4 ajustes deslizantes, reforço, "salvar como padrão da voz", histórico e o botão "Usar no vídeo", que manda o texto e a voz para o roteiro do avatar.
- **Trocador de voz:** gravar ou enviar o áudio, escolher a voz de destino e converter.
- Ponto único `engine` no código (`cloneVoice`, `tts`, `changeVoice`, `lipSync`) onde os serviços reais vão ser ligados.
