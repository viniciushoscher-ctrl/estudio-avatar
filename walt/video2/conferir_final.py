import json,re,sys,difflib,numpy as np,librosa,torch
from faster_whisper import WhisperModel
from speechbrain.inference.speaker import EncoderClassifier
wav,lj=sys.argv[1],sys.argv[2]
L=json.load(open(lj)); y,_=librosa.load(wav,sr=16000)
# 1) transcrição inteira x roteiro
m=WhisperModel('base.en',device='cpu',compute_type='int8')
h=' '.join(s.text for s in m.transcribe(y,beam_size=5)[0])
norm=lambda s: re.sub(r'[^a-z0-9 ]','',s.lower().replace('-',' ')).split()
ref=' '.join(l['txt'] for l in L['legendas'])
a,b=norm(ref),norm(h); sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
e=sum(max(i2-i1,j2-j1) for op,i1,i2,j1,j2 in sm.get_opcodes() if op!='equal')
print(f'TRANSCRIÇÃO: {len(a)} palavras no roteiro, {e} diferenças ({100*e/len(a):.1f}%)')
for op,i1,i2,j1,j2 in sm.get_opcodes():
    if op!='equal': print('  ',op,' '.join(a[i1:i2]),'->',' '.join(b[j1:j2]))
# 2) voz trecho a trecho contra o centro das falas aprovadas
enc=EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb",savedir="/tmp/w2/ecapa",run_opts={"device":"cpu"})
C=np.load('/tmp/w2/centro.npy'); walt={(round(w['ini'],1)) for w in L['walt']}
res=[]
for l in L['legendas']:
    seg=y[max(0,int((l['ini']-.25)*16000)):int((l['fim']+.25)*16000)]
    with torch.no_grad(): e_=enc.encode_batch(torch.tensor(seg)[None]).squeeze().numpy()
    e_/=np.linalg.norm(e_); f0,_,_=librosa.pyin(seg,fmin=70,fmax=260,sr=16000,frame_length=1024); f0=f0[~np.isnan(f0)]
    res.append((l['ini'],float(e_@C),float(np.median(f0)) if len(f0) else 0,l['txt'][:40]))
s=np.array([r[1] for r in res]); hz=np.array([r[2] for r in res if r[2]])
print(f'VOZ: {len(res)} trechos, semelhança min {s.min():.2f} p10 {np.percentile(s,10):.2f} mediana {np.median(s):.2f}; tom mediana {np.median(hz):.0f} Hz (p10 {np.percentile(hz,10):.0f}, p90 {np.percentile(hz,90):.0f})')
for r in res:
    if r[1]<0.62: print(f'   baixo {r[0]//60:.0f}:{r[0]%60:04.1f} {r[1]:.2f} {r[2]:.0f}Hz {r[3]}')
json.dump(res,open(lj.replace('linha.json','voz_trechos.json'),'w'))
