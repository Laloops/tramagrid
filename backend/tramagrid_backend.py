# filename: tramagrid_backend.py
import os
import json
import io
import base64
import uuid
import math
import stripe 
from dotenv import load_dotenv
from pathlib import Path # <--- Importante para achar o caminho certo
from PIL import Image, ImageDraw, ImageEnhance, ImageOps
from collections import defaultdict
from fastapi import FastAPI, UploadFile, File, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Tuple, List, Any
from supabase import create_client, Client 

# ================= CONFIGURAÇÃO DE AMBIENTE (ROBUSTA) =================
# Força o Python a procurar o .env na mesma pasta deste arquivo
env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path)

# Debug para você ver no terminal se carregou
if env_path.exists():
    print(f"✅ Arquivo .env carregado de: {env_path}")
else:
    print(f"❌ AVISO: Arquivo .env não encontrado em: {env_path}")

# ================= CONFIGURAÇÃO DE CHAVES =================
stripe.api_key = os.getenv("STRIPE_API_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

try:
    if SUPABASE_URL and SUPABASE_SERVICE_KEY:
        supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print("✅ Supabase Admin conectado!")
    else:
        print("⚠️ Variáveis do Supabase faltando no .env")
        supabase_admin = None
except Exception as e:
    print(f"⚠️ Erro ao conectar Supabase: {e}")
    supabase_admin = None

# ================= LÓGICA DE PROCESSAMENTO (SESSÃO) =================
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
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
        s_dir = os.path.join(DATA_DIR, session_id)
        os.makedirs(s_dir, exist_ok=True)
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
        with open(os.path.join(s_dir, "meta.json"), "w") as f: json.dump(meta, f)
        if self.original: self.original.save(os.path.join(s_dir, "original.png"))
        if self.quantized: self.quantized.save(os.path.join(s_dir, "quantized.png"))

    def load_from_disk(self, session_id: str) -> bool:
        s_dir = os.path.join(DATA_DIR, session_id)
        meta_path = os.path.join(s_dir, "meta.json")
        if not os.path.exists(meta_path): return False
        try:
            with open(meta_path, "r") as f: meta = json.load(f)
            p = meta.get("params", {})
            for k, v in p.items(): 
                if hasattr(self, k): setattr(self, k, v)
            self.palette = {int(k): tuple(v) for k, v in meta.get("palette", {}).items()}
            self.custom_palette = {int(k): tuple(v) for k, v in meta.get("custom_palette", {}).items()}
            if os.path.exists(os.path.join(s_dir, "original.png")):
                self.original = Image.open(os.path.join(s_dir, "original.png")).convert("RGB")
            if os.path.exists(os.path.join(s_dir, "quantized.png")):
                self.quantized = Image.open(os.path.join(s_dir, "quantized.png")).convert("RGB")
                self._draw_grid()
            return True
        except: return False

    def _save_state(self):
        if not self.quantized: return
        if len(self.history) >= 20: self.history.pop(0)
        self.history.append({'quantized': self.quantized.copy(), 'palette': self.palette.copy(), 'custom_palette': self.custom_palette.copy()})

    def undo(self):
        if not self.history: return
        s = self.history.pop()
        self.quantized = s['quantized']; self.palette = s['palette']; self.custom_palette = s['custom_palette']
        self._draw_grid()

    def load_image(self, file_bytes: bytes) -> None:
        self.original = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        self.history = []

    def generate_grid(self) -> None:
        if not self.original: return
        img = self.original.copy()
        if self.posterize < 8: img = ImageOps.posterize(img, max(1, min(8, int(self.posterize))))
        if self.gamma != 1.0: img = img.point([int(((i/255.0)**(1.0/self.gamma))*255) for i in range(256)]*3)
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
        base = {i: (raw[i*3], raw[i*3+1], raw[i*3+2]) for i in range(self.max_colors) if i*3+2 < len(raw)}
        self.palette = {i: self.custom_palette.get(i, c) for i, c in base.items()}
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
                color = self.palette.get(self.quantized.getpixel((x, y)), (255, 255, 255))
                px, py = margin + x * self.cell_size, margin + y * self.cell_size
                draw.rectangle([px, py, px + self.cell_size, py + self.cell_size], fill=color)

        overlay = Image.new("RGBA", (total_w, total_h), (255, 255, 255, 0))
        d_ov = ImageDraw.Draw(overlay)
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
        self._save_state()
        self.custom_palette[idx] = self.palette[idx] = (int(hex_val[1:3],16), int(hex_val[3:5],16), int(hex_val[5:7],16))
        self._draw_grid()

    def delete_color(self, idx):
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
            self.palette.pop(idx, None); self.custom_palette.pop(idx, None); self._draw_grid()

    def merge_colors(self, f, t):
        self._save_state()
        w, h = self.quantized.size
        for y in range(h):
            for x in range(w):
                if self.quantized.getpixel((x,y)) == f: self.quantized.putpixel((x,y), t)
        self.palette.pop(f, None); self.custom_palette.pop(f, None); self._draw_grid()
        
    def get_pixel_index(self, x, y): return int(self.quantized.getpixel((x,y))) if self.quantized and 0<=x<self.quantized.width and 0<=y<self.quantized.height else -1

    def replace_index_in_region(self, x, y, w, h, f, t):
        if not self.quantized: return
        self._save_state()
        for py in range(max(0,y), min(self.quantized.height, y+h)):
            for px in range(max(0,x), min(self.quantized.width, x+w)):
                if self.quantized.getpixel((px,py)) == f: self.quantized.putpixel((px,py), t)
        self._draw_grid()

    def get_grid_base64(self) -> str:
        if not self.grid_image: return ""
        img = self.grid_image.copy()
        if self.highlighted_row >= 0:
            ov = Image.new("RGBA", img.size, (0,0,0,0)); d = ImageDraw.Draw(ov)
            d.rectangle([0,0,img.width, img.height], fill=(0,0,0,100))
            py = 50 + (self.highlighted_row-1)*self.cell_size
            d.rectangle([0,0,img.width, py], fill=(0,0,0,160))
            d.rectangle([0, py+self.cell_size, img.width, img.height], fill=(0,0,0,160))
            img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
        buf = io.BytesIO(); img.save(buf, "PNG"); return base64.b64encode(buf.getvalue()).decode()
    
    def suggest_clusters(self, threshold=50.0):
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
                if math.sqrt(sum((a-b)**2 for a,b in zip(rgb1,rgb2))) < threshold:
                    grp.append(idx2); visited.add(idx2)
            if len(grp) > 1: visited.add(idx1); groups.append(grp)
        return groups

# ==================== ROTAS API ====================
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def get_session_or_load(sid: str) -> TramaGridSession:
    if sid in sessions: return sessions[sid]
    s = TramaGridSession()
    if s.load_from_disk(sid): sessions[sid] = s; return s
    raise HTTPException(404, "Sessão não encontrada.")

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
class CheckoutSession(BaseModel): quantity: int; user_id: str
class UserRequest(BaseModel): user_id: str # <--- IMPORTANTE PARA O V2.0

@app.post("/api/session")
def create_sess(): sid = str(uuid.uuid4()); sessions[sid] = TramaGridSession(); sessions[sid].save_to_disk(sid); return {"session_id": sid}

@app.post("/api/upload/{sid}")
async def up(sid: str, file: UploadFile = File(...)):
    s = get_session_or_load(sid); s.load_image(await file.read()); s.generate_grid(); s.save_to_disk(sid); return {"ok": True}

@app.post("/api/generate/{sid}")
def gen(sid: str): s = get_session_or_load(sid); s.generate_grid(); s.save_to_disk(sid); return {"ok": True}

@app.get("/api/grid/{sid}")
def grd(sid: str): return {"image_base64": get_session_or_load(sid).get_grid_base64()}

@app.get("/api/palette/{sid}")
def pal(sid: str): return get_session_or_load(sid).get_palette_info()

@app.post("/api/params/{sid}")
def par(sid: str, d: ParamsUpdate):
    s = get_session_or_load(sid); s._save_state()
    for k,v in d.dict(exclude_unset=True).items(): setattr(s, k, v)
    if d.show_grid is not None: s._draw_grid()
    s.save_to_disk(sid); return {"ok": True}

@app.get("/api/params/{sid}")
def gpar(sid: str): s = get_session_or_load(sid); return {k: getattr(s, k) for k in ["max_colors","grid_width_cells","brightness","contrast","saturation","gamma","posterize","gauge_stitches","gauge_rows","show_grid","highlighted_row"]}

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

@app.get("/api/original/{sid}")
def ori(sid: str):
    s = get_session_or_load(sid)
    if not s.original: raise HTTPException(404, "Original não encontrada")
    buf = io.BytesIO(); s.original.save(buf, "PNG"); return {"image_base64": base64.b64encode(buf.getvalue()).decode()}

# === NOVA ROTA DE SEGURANÇA: CONSUMIR CRÉDITOS ===
@app.post("/api/consume-credit")
def consume_credit(data: UserRequest):
    if not supabase_admin: raise HTTPException(500, "Supabase Admin não configurado.")
    
    # 1. Buscar Perfil (Seguro)
    res = supabase_admin.table('profiles').select('*').eq('id', data.user_id).single().execute()
    profile = res.data
    if not profile: raise HTTPException(404, "Perfil não encontrado.")

    # 2. Verificar Saldo
    has_free = not profile.get('free_generation_used', False)
    credits = profile.get('credits', 0)

    if not has_free and credits <= 0:
        raise HTTPException(402, "Saldo insuficiente.") # 402 = Payment Required

    # 3. Descontar
    update_data = {}
    if has_free:
        print(f"🎁 {data.user_id} usando geração grátis.")
        update_data = {'free_generation_used': True}
    else:
        print(f"💎 {data.user_id} gastando crédito.")
        update_data = {'credits': credits - 1}

    supabase_admin.table('profiles').update(update_data).eq('id', data.user_id).execute()
    return {"ok": True}

# === PAGAMENTOS (STRIPE) ===
@app.post("/api/create-checkout-session")
async def create_checkout_session(data: CheckoutSession):
    try:
        # Preços em centavos (ex: 500 = R$ 5,00)
        unit_amount = 500 # Default fallback
        
        if data.quantity == 2: unit_amount = 495
        elif data.quantity == 10: unit_amount = 299 # 2990 / 10
        elif data.quantity == 50: unit_amount = 179 # 8990 / 50

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'brl',
                    'product_data': {'name': f'{data.quantity} Créditos TramaGrid'},
                    'unit_amount': unit_amount,
                },
                'quantity': data.quantity,
            }],
            mode='payment',
            success_url='http://localhost:5173/buy-credits?success=true',
            cancel_url='http://localhost:5173/buy-credits?canceled=true',
            client_reference_id=data.user_id,
            metadata={'credits': data.quantity}
        )
        return {"url": checkout_session.url}
    except Exception as e:
        print(f"Stripe Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/webhook")
async def webhook_received(request: Request):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except:
        raise HTTPException(400, "Webhook Error")

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session.get('client_reference_id')
        credits_to_add = int(session.get('metadata', {}).get('credits', 0))
        if user_id and credits_to_add > 0 and supabase_admin:
            print(f"💰 Pagamento confirmado: +{credits_to_add} para {user_id}")
            res = supabase_admin.table('profiles').select('credits').eq('id', user_id).single().execute()
            current = res.data['credits'] if res.data else 0
            supabase_admin.table('profiles').update({'credits': current + credits_to_add}).eq('id', user_id).execute()
    return {"status": "success"}