import sys, json, re, numpy as np, librosa, torch
from speechbrain.inference.speaker import EncoderClassifier
enc = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", savedir="/tmp/w2/ecapa", run_opts={"device":"cpu"})
def emb(y): 
    with torch.no_grad(): e = enc.encode_batch(torch.tensor(y)[None]).squeeze().numpy()
    return e/np.linalg.norm(e)
def feats(y, sr=16000, words=None):
    f0,_,_ = librosa.pyin(y, fmin=70, fmax=260, sr=sr, frame_length=1024)
    f0 = f0[~np.isnan(f0)]
    cen = librosa.feature.spectral_centroid(y=y, sr=sr)[0]; rms = librosa.feature.rms(y=y)[0]
    voiced = rms > 0.1*rms.max()
    dur = voiced.sum()*512/sr
    return dict(hz=round(float(np.median(f0)),1) if len(f0) else 0, cen=round(float(np.median(cen[voiced])),0), wps=round(words/max(dur,.5),2) if words else None)
ref,_ = librosa.load(sys.argv[1], sr=16000); R = emb(ref); fr = feats(ref)
print("REF", fr)
out=[]
for item in json.load(open(sys.argv[2])):
    y,_ = librosa.load(item["f"], sr=16000, offset=item.get("o",0), duration=item.get("d"))
    s = float(emb(y) @ R); f = feats(y, words=item.get("w"))
    out.append(dict(id=item["id"], sim=round(s,3), **f))
    print(out[-1], flush=True)
json.dump(dict(ref=fr, itens=out), open(sys.argv[3],"w"), indent=1)
