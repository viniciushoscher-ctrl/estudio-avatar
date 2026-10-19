# Estúdio de Avatar (100% GitHub, sem pagar)

Gera um vídeo seu falando um roteiro, com a sua voz e a boca sincronizada, rodando no
**GitHub Actions** (gratuito). Sem ElevenLabs, HeyGen, Modal ou Google.

Este repositório é **público e só tem o motor**. O seu vídeo de treino, os seus roteiros e os
vídeos gerados ficam num segundo repositório **privado**, para o seu rosto e a sua voz não
ficarem expostos.

## Como funciona

| Etapa | Modelo | Licença |
|---|---|---|
| Voz clonada a partir de 12 s da sua gravação | [Chatterbox Multilingual](https://github.com/resemble-ai/chatterbox) | MIT |
| Boca sincronizada com o áudio | [Wav2Lip](https://github.com/Rudrabha/Wav2Lip) | só uso pessoal e pesquisa |
| Recortes e junção | ffmpeg | |

**Limites desta versão (o GitHub grátis não tem GPU):**
- Tudo roda na CPU. A boca fica menos nítida que a do HeyGen, e é mais lenta.
- Wav2Lip **não pode ser usado comercialmente**. Serve para os seus posts; para vender o app
  depois, troque por um modelo com licença comercial (ex.: LatentSync, que precisa de GPU).
- Os tempos de execução ainda não foram medidos.

## Preparar (uma vez)

1. **Repositório privado de dados:** crie um repositório **privado** chamado
   `estudio-avatar-dados` (pode estar vazio).
2. **Vídeo de treino:** grave 1 a 3 min olhando para a câmera, lugar silencioso, boa luz, o
   mesmo microfone dos posts. **No final, fique 10 s com a boca fechada** olhando para a câmera:
   é esse trecho que vira a imagem base (a boca é redesenhada por cima). No repositório de
   dados: *Releases > Draft a new release*, tag `treino`, anexe o vídeo e publique.
3. **Chave de acesso:** em *GitHub > Settings (da sua conta) > Developer settings > Personal
   access tokens > Fine-grained tokens > Generate new token*:
   - *Repository access:* **Only select repositories** > `estudio-avatar-dados`
   - *Permissions > Repository permissions:* **Contents: Read and write**
   - Copie o token gerado.
4. **Guardar a chave:** neste repositório, *Settings > Secrets and variables > Actions >
   New repository secret*. Nome: `DADOS_TOKEN`. Valor: o token copiado.

## Gerar

*Actions > Gerar vídeo > Run workflow*:

1. Primeiro rode com **etapa = voz** e `video_treino` = `treino/nome-do-arquivo.mov`. Em
   minutos sai o `voz-N.mp3`. Compare com a sua voz. Se não ficar parecida, mude `inicio_voz`
   (segundo onde começa uma fala limpa) e rode de novo.
2. Depois rode com **etapa = video**. O resultado vai para *Releases > resultados* do seu
   repositório **privado** (`video-N.mp4`).

Roteiros: coloque em `roteiros/` do repositório privado (ex.: `roteiros/post-1.txt`) e digite
esse caminho no campo `roteiro`. Se o arquivo não existir lá, vale o de teste deste repositório.

Para só conferir a instalação, rode com `video_treino = sintetico` (não usa seus dados).

## Privacidade

- Aqui só há código. O que é seu fica no repositório privado.
- Os registros (logs) das execuções deste repositório são públicos: o motor não imprime seu
  texto nem seus arquivos, só contagens e nomes de arquivos.
- Nunca use o seu rosto nem a sua voz em `sintetico` ou em arquivos deste repositório.

## Custo

Repositório público tem Actions gratuito e sem limite de minutos (máquina de 4 CPUs e 16 GB).
Cada execução tem limite de 6 horas.

## Testar sem baixar modelos

```bash
python motor/gerar.py --treino meu.mp4 --roteiro roteiros/teste-15s.txt --saida saida --simular
```

(voz vira um tom e a boca não mexe; serve para conferir recortes e junção.)

## Arquivos

- `.github/workflows/gerar-video.yml`: o fluxo
- `motor/gerar.py`: recorta, fala, sincroniza e junta
- `motor/voz.py`: Chatterbox · `motor/patch_wav2lip.py`: ajustes do Wav2Lip às bibliotecas atuais
- `roteiros/teste-15s.txt`: roteiro de teste
