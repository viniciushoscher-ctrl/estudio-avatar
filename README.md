# Estúdio de Avatar (100% GitHub, sem pagar)

Gera um vídeo seu falando um roteiro, com a sua voz e a boca sincronizada, rodando no
**GitHub Actions** (gratuito). Sem ElevenLabs, HeyGen, Modal ou Google.

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
- Os tempos de execução abaixo ainda não foram medidos.

## Preparar (uma vez)

1. Crie um repositório **privado** no GitHub (ex.: `estudio-avatar`) e envie estes arquivos.
   Privado, porque o vídeo gerado mostra o seu rosto.
2. Grave o vídeo de treino (1 a 3 min): olhando para a câmera, lugar silencioso, boa luz,
   o mesmo microfone dos posts. **No final, fique 10 s com a boca fechada**, olhando para a
   câmera: é esse trecho que vira a imagem base (a boca é redesenhada por cima).
3. No repositório: *Releases > Draft a new release*, tag `treino`, anexe o vídeo e publique
   (pode marcar como pré-lançamento). Vídeos até 2 GB cabem.

## Gerar

*Actions > Gerar vídeo > Run workflow*:

1. Primeiro rode com **etapa = voz**. Em minutos você baixa o `voz.mp3` e compara com a sua voz.
   Se não ficar parecida, mude `inicio_voz` (segundo onde começa uma fala limpa) e rode de novo.
2. Depois rode com **etapa = video**. O resultado sai em *Artifacts > resultado* (fica 7 dias).

Campos: `video_treino` = `treino/nome-do-arquivo.mov`; `roteiro` = arquivo em `roteiros/`
(edite pelo próprio GitHub); `inicio_video` = segundo onde começam os 10 s de boca fechada.

## Custo

Repositório privado no plano grátis tem uma cota mensal de minutos do Actions (confira o valor em
*Settings > Billing*). Máquina de repositório privado: 2 CPUs e 8 GB; de repositório público:
4 CPUs e 16 GB e minutos ilimitados, mas o resultado ficaria público. Se faltar memória na
voz, a saída é tornar o repositório público e **não** usar o seu rosto real nele.

## Testar sem baixar modelos

```bash
python motor/gerar.py --treino meu.mp4 --roteiro roteiros/teste-15s.txt --saida saida --simular
```

(voz vira um tom e a boca não mexe; serve para conferir recortes e junção.)

## Arquivos

- `.github/workflows/gerar-video.yml`: o fluxo
- `motor/gerar.py`: recorta, fala, sincroniza e junta
- `motor/voz.py`: Chatterbox · `motor/patch_wav2lip.py`: ajustes do Wav2Lip às bibliotecas atuais
- `roteiros/`: seus roteiros
