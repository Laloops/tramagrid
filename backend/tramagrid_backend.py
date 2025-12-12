# filename: tramagrid_backend.py
import os
import json
import io
import base64
import uuid
import math
from PIL import Image, ImageDraw, ImageEnhance, ImageOps
from collections import defaultdict
from fastapi import FastAPI, UploadFile, File, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Tuple, List, Any

# ================= CONFIGURAÇÃO DE PERSISTÊNCIA =================
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Cache em memória
sessions: Dict[str, "TramaGridSession"] = {}

class TramaGridSession:
    def __init__(self):
        self.original: Optional[Image.Image] = None
        self.processed: Optional[Image.Image] = None
        self.quantized: Optional[Image.Image] = None
        self.palette: Dict[int, Tuple[int, int, int]] = {}
        self.custom_palette: Dict[int, Tuple[int, int, int]] = {}
        self.grid_image: Optional[Image.Image] = None
        self.history: List[Dict[str, Any]] = []
        
        # Parâmetros
        self.grid_width_cells: int = 130
        self.cell_size: int = 22
        self.highlighted_row: int = -1
        self.max_colors: int = 64
        self.brightness: float = 1.0
        self.contrast: float = 1.0
        self.saturation: float = 1.0
        self.gamma: float = 1.0
        self.posterize: int = 8
        self.gauge_stitches: int = 20
        self.gauge_rows: int = 20
        self.show_grid: bool = True

    def save_to_disk(self, session_id: str):
        """Salva o estado no disco (Anti-Amnésia)."""
        s_dir = os.path.join(DATA_DIR, session_id)
        os.makedirs(s_dir, exist_ok=True)
        
        # Salva params e paletas
        meta = {
            "params": {
                "grid_width_cells": self.grid_width_cells,
                "max_colors": self.max_colors,
                "brightness": self.brightness,
                "contrast": self.contrast,
                "saturation": self.saturation,
                "gamma": self.gamma,
                "posterize": self.posterize,
                "gauge_stitches": self.gauge_stitches,
                "gauge_rows": self.gauge_rows,
                "show_grid": self.show_grid,
                "highlighted_row": self.highlighted_row
            },
            "palette": {str(k): v for k, v in self.palette.items()},
            "custom_palette": {str(k): v for k, v in self.custom_palette.items()}
        }
        with open(os.path.join(s_dir, "meta.json"), "w") as f:
            json.dump(meta, f)
            
        # Salva imagens
        if self.original:
            self.original.save(os.path.join(s_dir, "original.png"))
        if self.quantized:
            self.quantized.save(os.path.join(s_dir, "quantized.png"))

    def load_from_disk(self, session_id: str) -> bool:
        """Tenta recuperar a sessão do disco."""
        s_dir = os.path.join(DATA_DIR, session_id)
        meta_path = os.path.join(s_dir, "meta.json")
        
        if not os.path.exists(meta_path):
            return False
            
        try:
            with open(meta_path, "r") as f:
                meta = json.load(f)
            
            # Restaura Params
            p = meta.get("params", {})
            for k, v in p.items():
                if hasattr(self, k): setattr(self, k, v)
            
            # Restaura Paletas
            self.palette = {int(k): tuple(v) for k, v in meta.get("palette", {}).items()}
            self.custom_palette = {int(k): tuple(v) for k, v in meta.get("custom_palette", {}).items()}
            
            # Restaura Imagens
            if os.path.exists(os.path.join(s_dir, "original.png")):
                self.original = Image.open(os.path.join(s_dir, "original.png")).convert("RGB")
            
            if os.path.exists(os.path.join(s_dir, "quantized.png")):
                self.quantized = Image.open(os.path.join(s_dir, "quantized.png")).convert("RGB")
                # Regenera o grid visual baseado na quantized recuperada
                self._draw_grid()
                
            return True
        except Exception as e:
            print(f"Erro ao recuperar sessão {session_id}: {e}")
            return False

    def _save_state(self):
        if not self.quantized: return
        if len(self.history) >= 20: self.history.pop(0)
        self.history.append({
            'quantized': self.quantized.copy(),
            'palette': self.palette.copy(),
            'custom_palette': self.custom_palette.copy()
        })

    def undo(self):
        if not self.history: return
        s = self.history.pop()
        self.quantized = s['quantized']
        self.palette = s['palette']
        self.custom_palette = s['custom_palette']
        self._draw_grid()

    def load_image(self, file_bytes: bytes) -> None:
        self.original = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        self.history = []

    def generate_grid(self) -> None:
        if not self.original: return
        img = self.original.copy()
        
        if self.posterize < 8:
            img = ImageOps.posterize(img, max(1, min(8, int(self.posterize))))
        if self.gamma != 1.0 and self.gamma > 0:
            inv_gamma = 1.0 / self.gamma
            table = [int(((i / 255.0) ** inv_gamma) * 255) for i in range(256)]
            img = img.point(table * 3)
        if self.saturation != 1.0: img = ImageEnhance.Color(img).enhance(self.saturation)
        if self.brightness != 1.0: img = ImageEnhance.Brightness(img).enhance(self.brightness)
        if self.contrast != 1.0: img = ImageEnhance.Contrast(img).enhance(self.contrast)

        ratio = self.gauge_stitches / max(1, self.gauge_rows)
        w, h = img.size
        new_w = max(10, self.grid_width_cells)
        new_h = int((h / w) * new_w * ratio)
        
        self.processed = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self.quantized = self.processed.quantize(colors=self.max_colors, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG)
        
        raw = self.quantized.getpalette()[:self.max_colors * 3]
        base = {}
        for i in range(self.max_colors):
            if i * 3 + 2 < len(raw): base[i] = (raw[i*3], raw[i*3+1], raw[i*3+2])
        
        self.palette = {i: self.custom_palette.get(i, cor) for i, cor in base.items()}
        self._draw_grid()

    def _draw_grid(self) -> None:
        if not self.quantized: return
        
        margin = 50
        wc, hc = self.quantized.size
        total_w = margin + wc * self.cell_size + 20
        total_h = margin + hc * self.cell_size + 20
        
        if not self.show_grid:
            base = Image.new("RGBA", (total_w, total_h), (255, 255, 255, 255))
            prev = self.quantized.resize((wc * self.cell_size, hc * self.cell_size), Image.Resampling.NEAREST)
            base.paste(prev, (margin, margin))
            self.grid_image = base.convert("RGB")
            return

        base = Image.new("RGBA", (total_w, total_h), (255, 255, 255, 255))
        draw = ImageDraw.Draw(base)

        for y in range(hc):
            for x in range(wc):
                idx = self.quantized.getpixel((x, y))
                color = self.palette.get(idx, (255, 255, 255))
                px, py = margin + x * self.cell_size, margin + y * self.cell_size
                draw.rectangle([px, py, px + self.cell_size, py + self.cell_size], fill=color)

        overlay = Image.new("RGBA", (total_w, total_h), (255, 255, 255, 0))
        d_ov = ImageDraw.Draw(overlay)
        
        # Linhas
        for y in range(hc + 1):
            py = margin + y * self.cell_size
            thk = (y % 10 == 0 or y == 0 or y == hc)
            d_ov.line([(margin, py), (margin + wc * self.cell_size, py)], fill=(255,255,255,180 if thk else 70), width=2 if thk else 1)
        for x in range(wc + 1):
            px = margin + x * self.cell_size
            thk = (x % 10 == 0 or x == 0 or x == wc)
            d_ov.line([(px, margin), (px, margin + hc * self.cell_size)], fill=(255,255,255,180 if thk else 70), width=2 if thk else 1)
            
        combined = Image.alpha_composite(base, overlay)
        d_comb = ImageDraw.Draw(combined)
        
        # Números
        for x in range(wc):
            if (x+1)%5==0 or x==0: d_comb.text((margin + x*self.cell_size + 11, 25), str(x+1), fill=(100,100,100), anchor="mm")
        for y in range(hc):
            if (y+1)%5==0 or y==0: d_comb.text((20, margin + y*self.cell_size + 11), str(y+1), fill=(100,100,100), anchor="mm")
            
        self.grid_image = combined.convert("RGB")

    def get_palette_info(self) -> List[Dict]:
        if not self.quantized: return []
        usage = defaultdict(int)
        w, h = self.quantized.size
        for y in range(h):
            for x in range(w):
                if self.quantized.getpixel((x, y)) in self.palette: usage[self.quantized.getpixel((x, y))] += 1
        return [{"index": i, "hex": f"#{r:02x}{g:02x}{b:02x}", "count": c} for i, c in sorted(usage.items(), key=lambda x: -x[1]) if i in self.palette]

    def paint_cell(self, x, y, idx):
        if not self.quantized or idx not in self.palette: return
        self._save_state()
        if 0 <= x < self.quantized.width and 0 <= y < self.quantized.height:
            self.quantized.putpixel((x, y), idx)
            self._draw_grid()

    def replace_color(self, idx, hex_val):
        if idx not in self.palette: return
        self._save_state()
        self.custom_palette[idx] = self.palette[idx] = (int(hex_val[1:3],16), int(hex_val[3:5],16), int(hex_val[5:7],16))
        self._draw_grid()

    def delete_color(self, idx):
        if idx not in self.palette: return
        self._save_state()
        c1 = self.palette[idx]
        best, min_d = None, float('inf')
        for i, c2 in self.palette.items():
            if i == idx: continue
            d = math.sqrt(sum((a-b)**2 for a,b in zip(c1,c2)))
            if d < min_d: min_d, best = d, i
        if best is not None:
            w, h = self.quantized.size
            for y in range(h):
                for x in range(w):
                    if self.quantized.getpixel((x,y)) == idx: self.quantized.putpixel((x,y), best)
            self.palette.pop(idx, None)
            self.custom_palette.pop(idx, None)
            self._draw_grid()

    def merge_colors(self, f, t):
        if not self.quantized or f not in self.palette or t not in self.palette: return
        self._save_state()
        w, h = self.quantized.size
        for y in range(h):
            for x in range(w):
                if self.quantized.getpixel((x,y)) == f: self.quantized.putpixel((x,y), t)
        self.palette.pop(f, None)
        self.custom_palette.pop(f, None)
        self._draw_grid()
        
    def get_pixel_index(self, x, y):
        if self.quantized and 0 <= x < self.quantized.width and 0 <= y < self.quantized.height:
            return int(self.quantized.getpixel((x,y)))
        return -1

    def replace_index_in_region(self, x, y, w, h, f, t):
        if not self.quantized: return
        self._save_state()
        iw, ih = self.quantized.size
        for py in range(max(0,y), min(ih, y+h)):
            for px in range(max(0,x), min(iw, x+w)):
                if self.quantized.getpixel((px,py)) == f: self.quantized.putpixel((px,py), t)
        self._draw_grid()

    def get_grid_base64(self) -> str:
        if not self.grid_image: return ""
        img = self.grid_image.copy()
        if self.highlighted_row >= 0:
            ov = Image.new("RGBA", img.size, (0,0,0,0))
            d = ImageDraw.Draw(ov)
            d.rectangle([0,0,img.width, img.height], fill=(0,0,0,100))
            py = 50 + (self.highlighted_row-1)*22
            d.rectangle([0,0,img.width, py], fill=(0,0,0,160))
            d.rectangle([0, py+22, img.width, img.height], fill=(0,0,0,160))
            img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    
    def suggest_clusters(self, threshold=50.0):
        # (Lógica simplificada para economizar linhas)
        if not self.palette: return []
        colors = list(self.palette.items())
        groups = []
        visited = set()
        for i in range(len(colors)):
            idx1, rgb1 = colors[i]
            if idx1 in visited: continue
            grp = [idx1]
            for j in range(i+1, len(colors)):
                idx2, rgb2 = colors[j]
                if idx2 in visited: continue
                # Distância euclidiana simples
                d = math.sqrt(sum((a-b)**2 for a,b in zip(rgb1,rgb2)))
                if d < threshold:
                    grp.append(idx2); visited.add(idx2)
            if len(grp) > 1: visited.add(idx1); groups.append(grp)
        return groups

# ==================== ROTAS API ====================
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === AQUI ESTÁ A CORREÇÃO: Função Segura ===
def get_session_or_load(sid: str) -> TramaGridSession:
    # 1. Tenta memória
    if sid in sessions: return sessions[sid]
    
    # 2. Tenta Disco
    s = TramaGridSession()
    if s.load_from_disk(sid):
        sessions[sid] = s
        print(f"✅ Sessão {sid} restaurada do disco.")
        return s
    
    # 3. Falha
    print(f"❌ Sessão {sid} não encontrada.")
    raise HTTPException(404, "Sessão não encontrada.")

# Modelos Pydantic
class ParamsUpdate(BaseModel):
    max_colors: int|None=None; grid_width_cells: int|None=None; brightness: float|None=None
    contrast: float|None=None; saturation: float|None=None; gamma: float|None=None
    posterize: int|None=None; highlighted_row: int|None=None; gauge_stitches: int|None=None
    gauge_rows: int|None=None; show_grid: bool|None=None
class Paint(BaseModel): x: int; y: int; color_index: int
class Pixel(BaseModel): x: int; y: int
class ColRep(BaseModel): index: int; new_hex: str
class ColDel(BaseModel): index: int
class Merge(BaseModel): from_index: int; to_index: int
class RegRep(BaseModel): x: int; y: int; w: int; h: int; from_index: int; to_index: int

@app.post("/api/session")
def create_sess():
    sid = str(uuid.uuid4()); sessions[sid] = TramaGridSession(); sessions[sid].save_to_disk(sid)
    return {"session_id": sid}

@app.post("/api/upload/{sid}")
async def up(sid: str, file: UploadFile = File(...)):
    s = get_session_or_load(sid) # <--- USA A FUNÇÃO SEGURA
    s.load_image(await file.read()); s.generate_grid(); s.save_to_disk(sid)
    return {"ok": True}

@app.post("/api/generate/{sid}")
def gen(sid: str): s = get_session_or_load(sid); s.generate_grid(); s.save_to_disk(sid); return {"ok": True}

@app.get("/api/grid/{sid}")
def get_grid_endpoint(sid: str):
    s = get_session_or_load(sid) # <--- AGORA RECUPERA DO DISCO SE PRECISAR
    return {"image_base64": s.get_grid_base64()}

@app.get("/api/palette/{sid}")
def pal(sid: str): return get_session_or_load(sid).get_palette_info()

@app.post("/api/params/{sid}")
def par(sid: str, d: ParamsUpdate):
    s = get_session_or_load(sid); s._save_state()
    for k,v in d.dict(exclude_unset=True).items(): setattr(s, k, v)
    if d.show_grid is not None: s._draw_grid()
    s.save_to_disk(sid)
    return {"ok": True}

@app.get("/api/params/{sid}")
def get_par(sid: str):
    s = get_session_or_load(sid)
    # Retorna dict com os params
    return {k: getattr(s, k) for k in ["max_colors","grid_width_cells","brightness","contrast","saturation","gamma","posterize","gauge_stitches","gauge_rows","show_grid","highlighted_row"]}

@app.post("/api/paint/{sid}")
def pnt(sid: str, d: Paint): get_session_or_load(sid).paint_cell(d.x, d.y, d.color_index); get_session_or_load(sid).save_to_disk(sid); return {"ok":True}

@app.post("/api/query-pixel/{sid}")
def qpx(sid: str, d: Pixel): return {"index": get_session_or_load(sid).get_pixel_index(d.x, d.y)}

@app.post("/api/color/replace/{sid}")
def cr(sid: str, d: ColRep): s=get_session_or_load(sid); s.replace_color(d.index, d.new_hex); s.save_to_disk(sid); return {"ok":True}

@app.post("/api/color/delete/{sid}")
def cd(sid: str, d: ColDel): s=get_session_or_load(sid); s.delete_color(d.index); s.save_to_disk(sid); return {"ok":True}

@app.post("/api/merge/{sid}")
def mg(sid: str, d: Merge): s=get_session_or_load(sid); s.merge_colors(d.from_index, d.to_index); s.save_to_disk(sid); return {"ok":True}

@app.post("/api/region/replace/{sid}")
def rr(sid: str, d: RegRep): s=get_session_or_load(sid); s.replace_index_in_region(d.x,d.y,d.w,d.h,d.from_index,d.to_index); s.save_to_disk(sid); return {"ok":True}

@app.post("/api/undo/{sid}")
def und(sid: str): s=get_session_or_load(sid); s.undo(); s.save_to_disk(sid); return {"ok":True}

@app.get("/api/clusters/{sid}")
def clu(sid: str): return {"clusters": get_session_or_load(sid).suggest_clusters()}

# Rota para imagem ORIGINAL (se precisar no futuro)
@app.get("/api/original/{sid}")
def get_original(sid: str):
    s = get_session_or_load(sid)
    if not s.original: raise HTTPException(404, "Original não encontrada")
    buf = io.BytesIO(); s.original.save(buf, "PNG")
    return {"image_base64": base64.b64encode(buf.getvalue()).decode()}