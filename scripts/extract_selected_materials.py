"""Re-extract the selected PNGs from saved wet-media fields; no fluid runtime."""
import argparse,json
from pathlib import Path
import numpy as np
from PIL import Image


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('output',type=Path)
    parser.add_argument('--fields',type=Path,default=Path(__file__).absolute().parent.parent/'materials/selected-wet-ink')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    metadata=json.loads((args.fields/'provenance.json').read_text('utf-8'))
    with np.load(args.fields/'selected-fields.npz') as data:
        deposit=data['deposit'];paper_h=data['paper_height']
    assert deposit.shape==paper_h.shape==tuple(metadata['pixels'])
    assert np.isfinite(deposit).all() and np.isfinite(paper_h).all() and deposit.min()>=0
    scale=metadata['alpha_curve']['density_scale']
    alpha=.74*np.exp(-1.6*deposit/max(scale,.01))
    rgba=np.full((*deposit.shape,4),255,dtype='u1');rgba[:,:,3]=np.round(alpha*255).astype('u1')
    Image.fromarray(rgba).save(args.output/'generated-wet-ink.png',dpi=(300,300))
    gy,gx=np.gradient(paper_h)
    shade=np.clip(249+(gx-gy)*65+(paper_h-.5)*5,232,255).astype('u1')
    Image.fromarray(np.repeat(shade[:,:,None],3,axis=2)).save(args.output/'generated-white-paper.png',dpi=(300,300))
    print(json.dumps({'output':str(args.output),'pixels':metadata['pixels'],'scope':'Exact field extraction, not a new fluid simulation.'}))


if __name__=='__main__':main()
