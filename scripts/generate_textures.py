"""Create original periodic watercolor/paper textures; never reads reference images."""
import json
from pathlib import Path
import numpy as np
from PIL import Image


def noise(rng, size, scale):
    values = rng.normal(size=(size,size))
    frequencies = np.fft.fftfreq(size)
    radius = frequencies[:,None]**2 + frequencies[None,:]**2
    field = np.fft.ifft2(np.fft.fft2(values)*np.exp(-radius*scale**2)).real
    return (field-field.mean())/(field.std()+1e-12)


def main():
    root = Path(__file__).absolute().parent.parent
    out = root / "src/inkmap_arcpy/assets"
    rng,size = np.random.default_rng(20261008),512
    cloud = noise(rng,size,48)*0.65 + noise(rng,size,17)*0.30 + noise(rng,size,4)*0.09
    pools = np.clip((cloud+1.4)/3.8,0,1)
    granules = np.clip(noise(rng,size,2.5),-2,2)*6
    alpha = np.clip(pools*172 + granules,0,190).astype(np.uint8)
    wash = np.full((size,size,4),255,dtype=np.uint8)
    wash[:,:,3] = alpha
    Image.fromarray(wash,"RGBA").save(out/"generated-wash.png")
    grain = noise(rng,size,2)*1.6 + noise(rng,size,12)*1.3 + noise(rng,size,55)*0.65
    fibers = np.sin(np.arange(size)[None,:]*2*np.pi*81/size)*0.6
    base = np.array([248,246,239],dtype=float)
    paper = np.clip(base+grain[:,:,None]+fibers[:,:,None],0,255).astype(np.uint8)
    Image.fromarray(paper,"RGB").save(out/"generated-paper.jpeg",quality=95,subsampling=0)
    print(json.dumps({"seed":20261008,"size":size,"method":"Periodic spectral noise; entirely original; MIT"}))


if __name__ == "__main__":
    main()
