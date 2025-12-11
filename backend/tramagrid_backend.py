# filename: tramagrid_backend.py
from PIL import Image, ImageDraw, ImageEnhance, ImageOps
import math
from collections import defaultdict
import io
import base64
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Tuple, List, Any

# Armazenamento em memória (reinicia com o servidor)
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
        self.gamma: float = 1.0
        self.posterize: int = 8
        
        # Parâmetros
        self.grid_width_cells: int = 130
        self.cell_size: int = 22
        self.zoom: float = 1.0
        self.highlighted_row: int = -1
        self.max_colors: int = 64
        self.brightness: float = 1.0
        self.contrast: float = 1.0
        self.saturation: float = 1.0
        self.gamma: float = 1.0
        self.posterize: int = 8  # 1 a 8
        self.gauge_stitches: int = 20 # Pontos em 10cm (largura)
        self.gauge_rows: int = 20     # Carreiras em 10cm (altura)
        self.show_grid: bool = True   # Controle para esconder a grade

    def _save_state(self):
        """Salva imagem, paletas E PARÂMETROS no histórico."""
        if not self.quantized: return
        if len(self.history) >= 20: self.history.pop(0)
        
        # Cria um snapshot completo do estado atual
        state = {
            'quantized': self.quantized.copy(),
            'palette': self.palette.copy(),
            'custom_palette': self.custom_palette.copy(),
            'params': {
                'grid_width_cells': self.grid_width_cells,
                'max_colors': self.max_colors,
                'brightness': self.brightness,
                'contrast': self.contrast,
                'saturation': self.saturation,
                'gamma': self.gamma,
                'posterize': self.posterize,
                'gauge_stitches': self.gauge_stitches,
                'gauge_rows': self.gauge_rows,
                'show_grid': self.show_grid,
                'highlighted_row': self.highlighted_row
            }
        }
        self.history.append(state)

    def undo(self):
        """Reverte para o estado anterior (imagem + parâmetros)."""
        if not self.history: return
        state = self.history.pop()
        
        # Restaura imagens e cores
        self.quantized = state['quantized']
        self.palette = state['palette']
        self.custom_palette = state['custom_palette']
        
        # Restaura parâmetros (usando .get para segurança)
        p = state.get('params', {})
        self.grid_width_cells = p.get('grid_width_cells', self.grid_width_cells)
        self.max_colors = p.get('max_colors', self.max_colors)
        self.brightness = p.get('brightness', self.brightness)
        self.contrast = p.get('contrast', self.contrast)
        self.saturation = p.get('saturation', self.saturation)
        self.gamma = p.get('gamma', self.gamma)
        self.posterize = p.get('posterize', self.posterize)
        self.gauge_stitches = p.get('gauge_stitches', self.gauge_stitches)
        self.gauge_rows = p.get('gauge_rows', self.gauge_rows)
        self.show_grid = p.get('show_grid', self.show_grid)
        self.highlighted_row = p.get('highlighted_row', self.highlighted_row)
        
        self._draw_grid()

    def load_image(self, file_bytes: bytes) -> None:
        self.original = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        self.history = []

    def generate_grid(self) -> None:
        if not self.original: return
        
        img = self.original.copy()
        
        # 1. Posterização
        if self.posterize < 8:
            bits = max(1, min(8, int(self.posterize)))
            img = ImageOps.posterize(img, bits)

        # 2. Gama (Sombras)
        if self.gamma != 1.0 and self.gamma > 0:
            inv_gamma = 1.0 / self.gamma
            # Tabela de correção de gama (deve ser inteiros)
            table = [int(((i / 255.0) ** inv_gamma) * 255) for i in range(256)]
            img = img.point(table * 3)

        # 3. Saturação
        if self.saturation != 1.0:
            img = ImageEnhance.Color(img).enhance(self.saturation)

        # 4. Brilho e Contraste
        if self.brightness != 1.0:
            img = ImageEnhance.Brightness(img).enhance(self.brightness)
        if self.contrast != 1.0:
            img = ImageEnhance.Contrast(img).enhance(self.contrast)

        # --- CÁLCULO DO GAUGE (NOVO) ---
        # Razão = (Pontos por cm) / (Carreiras por cm)
        # Se tenho 20 pontos e 10 carreiras em 10cm, o ponto é largo (ratio = 2.0)
        # Precisamos ajustar a altura da imagem proporcionalmente.
        pixel_aspect_ratio = self.gauge_stitches / max(1, self.gauge_rows)
        
        w, h = img.size
        new_w = max(10, self.grid_width_cells)
        
        # Ajusta a altura baseada na proporção da imagem original E na proporção do ponto
        new_h = int((h / w) * new_w * pixel_aspect_ratio)
        
        self.processed = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        self.quantized = self.processed.quantize(
            colors=self.max_colors, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG
        )
        
        raw_palette = self.quantized.getpalette()[:self.max_colors * 3]
        base_palette = {}
        for i in range(self.max_colors):
            if i * 3 + 2 < len(raw_palette):
                r, g, b = raw_palette[i*3:i*3+3]
                base_palette[i] = (r, g, b)
        
        self.palette = {i: self.custom_palette.get(i, cor) for i, cor in base_palette.items()}
        self._draw_grid()

    def _draw_grid(self) -> None:
        if not self.quantized: return
        
        # Se o usuário desligou a grade, geramos apenas a imagem limpa ampliada
        if not self.show_grid:
            # Apenas amplia a imagem pixelada para o tamanho de visualização
            margin = 50
            w_cells, h_cells = self.quantized.size
            total_w = margin + w_cells * self.cell_size + 20
            total_h = margin + h_cells * self.cell_size + 20
            
            # Cria fundo branco
            base = Image.new("RGBA", (total_w, total_h), (255, 255, 255, 255))
            # Cola a imagem redimensionada (sem linhas)
            preview = self.quantized.resize((w_cells * self.cell_size, h_cells * self.cell_size), Image.Resampling.NEAREST)
            base.paste(preview, (margin, margin))
            self.grid_image = base.convert("RGB")
            return

        margin = 50
        w_cells, h_cells = self.quantized.size
        total_w = margin + w_cells * self.cell_size + 20
        total_h = margin + h_cells * self.cell_size + 20
        
        # 1. Criar Imagem Base (Branca)
        base = Image.new("RGBA", (total_w, total_h), (255, 255, 255, 255))
        draw_base = ImageDraw.Draw(base)

        # 2. Desenhar os Pixels Coloridos
        for y in range(h_cells):
            for x in range(w_cells):
                idx = self.quantized.getpixel((x, y))
                color = self.palette.get(idx, (255, 255, 255))
                # Desenha o retângulo sólido na base
                px = margin + x * self.cell_size
                py = margin + y * self.cell_size
                draw_base.rectangle([px, py, px + self.cell_size, py + self.cell_size], fill=color)

        # 3. Criar Camada de Sobreposição (Transparente) para as Linhas
        overlay = Image.new("RGBA", (total_w, total_h), (255, 255, 255, 0))
        draw_overlay = ImageDraw.Draw(overlay)

        # Configuração das Linhas (RGBA: r, g, b, alpha)
        # Alpha 80 = ~30% de opacidade (bem suave)
        line_color_thin = (255, 255, 255, 70)   
        line_color_thick = (255, 255, 255, 180) # Mais forte para marcações de 10 em 10
        text_color = (100, 100, 100, 255)

        # Desenhar Linhas Horizontais
        for y in range(h_cells + 1):
            py = margin + y * self.cell_size
            is_thick = (y % 10 == 0) or (y == 0) or (y == h_cells)
            fill = line_color_thick if is_thick else line_color_thin
            width = 2 if is_thick else 1
            draw_overlay.line([(margin, py), (margin + w_cells * self.cell_size, py)], fill=fill, width=width)

        # Desenhar Linhas Verticais
        for x in range(w_cells + 1):
            px = margin + x * self.cell_size
            is_thick = (x % 10 == 0) or (x == 0) or (x == w_cells)
            fill = line_color_thick if is_thick else line_color_thin
            width = 2 if is_thick else 1
            draw_overlay.line([(px, margin), (px, margin + h_cells * self.cell_size)], fill=fill, width=width)
        
        # 4. Fundir a Camada de Linhas sobre a Base
        combined = Image.alpha_composite(base, overlay)
        draw_combined = ImageDraw.Draw(combined)

        # Numeração (Desenhamos por cima de tudo, sólido)
        for x in range(w_cells):
            if (x + 1) % 5 == 0 or x == 0:
                 draw_combined.text((margin + x * self.cell_size + 11, 25), str(x + 1), fill=text_color, anchor="mm")
        for y in range(h_cells):
            if (y + 1) % 5 == 0 or y == 0:
                draw_combined.text((20, margin + y * self.cell_size + 11), str(y + 1), fill=text_color, anchor="mm")
                
        self.grid_image = combined.convert("RGB")

    def get_palette_info(self) -> List[Dict]:
        if not self.quantized: return []
        usage = defaultdict(int)
        w, h = self.quantized.size
        for y in range(h):
            for x in range(w):
                idx = self.quantized.getpixel((x, y))
                if idx in self.palette: usage[idx] += 1
        result = []
        for idx, count in sorted(usage.items(), key=lambda item: -item[1]):
            r, g, b = self.palette[idx]
            result.append({"index": idx, "hex": f"#{r:02x}{g:02x}{b:02x}", "count": count})
        return result

    def replace_color(self, index: int, new_hex: str) -> None:
        if index not in self.palette: return
        self._save_state()
        r = int(new_hex[1:3], 16)
        g = int(new_hex[3:5], 16)
        b = int(new_hex[5:7], 16)
        self.custom_palette[index] = (r, g, b)
        self.palette[index] = (r, g, b)
        self._draw_grid()

    def delete_color(self, index_to_remove: int) -> None:
        if index_to_remove not in self.palette: return
        self._save_state()
        c1 = self.palette[index_to_remove]
        best_idx = None
        min_dist = float('inf')
        for idx, c2 in self.palette.items():
            if idx == index_to_remove: continue
            dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))
            if dist < min_dist: min_dist = dist; best_idx = idx
        if best_idx is None: return
        w, h = self.quantized.size
        for y in range(h):
            for x in range(w):
                if self.quantized.getpixel((x, y)) == index_to_remove:
                    self.quantized.putpixel((x, y), best_idx)
        self.custom_palette.pop(index_to_remove, None)
        self.palette.pop(index_to_remove, None)
        self._draw_grid()

    def paint_cell(self, x: int, y: int, color_index: int) -> None:
        if not self.quantized: return
        if color_index not in self.palette: return
        self._save_state()
        w, h = self.quantized.size
        if 0 <= x < w and 0 <= y < h:
            self.quantized.putpixel((x, y), color_index)
            self._draw_grid()

    def merge_colors(self, from_index: int, to_index: int) -> None:
        if not self.quantized: return
        if from_index not in self.palette or to_index not in self.palette: return
        if from_index == to_index: return
        self._save_state()
        w, h = self.quantized.size
        for y in range(h):
            for x in range(w):
                if self.quantized.getpixel((x, y)) == from_index:
                    self.quantized.putpixel((x, y), to_index)
        self.custom_palette.pop(from_index, None)
        self.palette.pop(from_index, None)
        self._draw_grid()

    def get_pixel_index(self, x: int, y: int) -> int:
        if not self.quantized: return -1
        w, h = self.quantized.size
        if 0 <= x < w and 0 <= y < h:
            return int(self.quantized.getpixel((x, y)))
        return -1

    def suggest_clusters(self, threshold: float = 50.0) -> List[List[int]]:
        """Identifica grupos de cores visivelmente similares."""
        if not self.palette: return []
        colors = list(self.palette.items())
        groups = []
        visited = set()

        def color_distance(c1, c2):
            # Fórmula Redmean (aproximação da percepção humana)
            r1, g1, b1 = c1
            r2, g2, b2 = c2
            rmean = (r1 + r2) // 2
            r = int(r1) - int(r2)
            g = int(g1) - int(g2)
            b = int(b1) - int(b2)
            return math.sqrt((((512+rmean)*r*r)>>8) + 4*g*g + (((767-rmean)*b*b)>>8))

        for i in range(len(colors)):
            idx1, rgb1 = colors[i]
            if idx1 in visited: continue
            current_group = [idx1]
            for j in range(i + 1, len(colors)):
                idx2, rgb2 = colors[j]
                if idx2 in visited: continue
                dist = color_distance(rgb1, rgb2)
                if dist < threshold:
                    current_group.append(idx2)
                    visited.add(idx2)
            if len(current_group) > 1:
                visited.add(idx1)
                groups.append(current_group)
        return groups

    def replace_index_in_region(self, x: int, y: int, w: int, h: int, from_index: int, to_index: int) -> None:
        """Substitui cor A por B apenas dentro de uma área retangular."""
        if not self.quantized: return
        # Validações básicas
        if from_index not in self.palette or to_index not in self.palette: return
        if from_index == to_index: return
        
        self._save_state()
        
        img_w, img_h = self.quantized.size
        
        # Garante que o retângulo está dentro da imagem
        start_x = max(0, x)
        start_y = max(0, y)
        end_x = min(img_w, x + w)
        end_y = min(img_h, y + h)
        
        # Varre apenas a área selecionada (muito mais rápido que a imagem toda)
        for py in range(start_y, end_y):
            for px in range(start_x, end_x):
                # Se o pixel for da cor 'from_index', muda para 'to_index'
                if self.quantized.getpixel((px, py)) == from_index:
                    self.quantized.putpixel((px, py), to_index)
        
        self._draw_grid()


    def get_grid_base64(self) -> str:
        if not self.grid_image: return ""
        img = self.grid_image.copy()
        if self.highlighted_row >= 0:
            # Destaque de linha: escurece o que não é a linha
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            m = 50
            # Desenha tudo escuro
            draw.rectangle([0, 0, img.width, img.height], fill=(0, 0, 0, 100))
            # "Limpa" a área da linha (recorte)
            py = m + (self.highlighted_row - 1) * self.cell_size
            # Truque: desenhar dois retangulos escuros (cima e baixo) deixa o meio claro
            draw.rectangle([0, 0, img.width, py], fill=(0,0,0,160)) 
            draw.rectangle([0, py + self.cell_size, img.width, img.height], fill=(0,0,0,160)) 
            
            img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()

# ==================== ROTAS API ====================
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ParamsUpdate(BaseModel):
    max_colors: Optional[int] = None
    grid_width_cells: Optional[int] = None
    brightness: Optional[float] = None
    contrast: Optional[float] = None
    saturation: Optional[float] = None
    gamma: Optional[float] = None
    posterize: Optional[int] = None
    highlighted_row: Optional[int] = None
    # NOVOS
    gauge_stitches: Optional[int] = None
    gauge_rows: Optional[int] = None
    show_grid: Optional[bool] = None
    
class RegionReplaceRequest(BaseModel):
    x: int
    y: int
    w: int
    h: int
    from_index: int
    to_index: int

class ColorReplace(BaseModel):
    index: int
    new_hex: str

class ColorDelete(BaseModel):
    index: int

class PaintRequest(BaseModel):
    x: int
    y: int
    color_index: int

class PixelQuery(BaseModel):
    x: int
    y: int

class MergeRequest(BaseModel):
    from_index: int
    to_index: int

@app.post("/api/session")
async def create_session():
    sid = str(uuid.uuid4())
    sessions[sid] = TramaGridSession()
    return {"session_id": sid}

@app.post("/api/upload/{session_id}")
async def upload_image(session_id: str, file: UploadFile = File(...)):
    if session_id not in sessions: raise HTTPException(404, "Sessão expirada.")
    content = await file.read()
    sessions[session_id].load_image(content)
    return {"message": "Imagem carregada"}

@app.post("/api/generate/{session_id}")
async def generate(session_id: str):
    if session_id not in sessions: raise HTTPException(404, "Sessão expirada.")
    sessions[session_id].generate_grid()
    return {"message": "Grade gerada"}

@app.get("/api/palette/{session_id}")
async def palette(session_id: str):
    if session_id not in sessions: return []
    return sessions[session_id].get_palette_info()

@app.post("/api/params/{session_id}")
async def update_params(session_id: str, data: ParamsUpdate):
    if session_id not in sessions: raise HTTPException(404, "Sessão expirada.")
    s = sessions[session_id]
    s._save_state()
    if data.max_colors is not None: s.max_colors = data.max_colors
    if data.grid_width_cells is not None: s.grid_width_cells = data.grid_width_cells
    if data.brightness is not None: s.brightness = data.brightness
    if data.contrast is not None: s.contrast = data.contrast
    if data.saturation is not None: s.saturation = data.saturation
    if data.gamma is not None: s.gamma = data.gamma
    if data.posterize is not None: s.posterize = data.posterize
    if data.highlighted_row is not None: s.highlighted_row = data.highlighted_row
    if data.posterize is not None: s.posterize = data.posterize
    if data.highlighted_row is not None: s.highlighted_row = data.highlighted_row
    # NOVOS
    if data.gauge_stitches is not None: s.gauge_stitches = data.gauge_stitches
    if data.gauge_rows is not None: s.gauge_rows = data.gauge_rows
    if data.show_grid is not None: 
        s.show_grid = data.show_grid
        s._draw_grid() # Se mudou a visibilidade, redesenha
    return {"message": "Parâmetros atualizados"}

@app.post("/api/color/replace/{session_id}")
async def replace_color_endpoint(session_id: str, payload: ColorReplace):
    if session_id not in sessions: raise HTTPException(404)
    sessions[session_id].replace_color(payload.index, payload.new_hex)
    return {"message": "Cor substituída"}

@app.post("/api/color/delete/{session_id}")
async def delete_color_endpoint(session_id: str, payload: ColorDelete):
    if session_id not in sessions: raise HTTPException(404)
    sessions[session_id].delete_color(payload.index)
    return {"message": "Cor removida"}

@app.post("/api/paint/{session_id}")
async def paint_cell_endpoint(session_id: str, payload: PaintRequest):
    if session_id not in sessions: raise HTTPException(404)
    sessions[session_id].paint_cell(payload.x, payload.y, payload.color_index)
    return {"message": "Pixel pintado"}

@app.post("/api/merge/{session_id}")
async def merge_colors_endpoint(session_id: str, payload: MergeRequest):
    if session_id not in sessions: raise HTTPException(404)
    sessions[session_id].merge_colors(payload.from_index, payload.to_index)
    return {"message": "Cores mescladas"}

@app.post("/api/query-pixel/{session_id}")
async def query_pixel_endpoint(session_id: str, payload: PixelQuery):
    if session_id not in sessions: raise HTTPException(404)
    idx = sessions[session_id].get_pixel_index(payload.x, payload.y)
    return {"index": idx}

@app.post("/api/undo/{session_id}")
async def undo_endpoint(session_id: str):
    if session_id not in sessions: raise HTTPException(404)
    sessions[session_id].undo()
    return {"message": "Desfeito"}

@app.get("/api/clusters/{session_id}")
async def get_clusters(session_id: str):
    if session_id not in sessions: return []
    return {"clusters": sessions[session_id].suggest_clusters(threshold=50.0)}

@app.get("/api/grid/{session_id}")
async def get_grid(session_id: str):
    if session_id not in sessions: raise HTTPException(404)
    b64 = sessions[session_id].get_grid_base64()
    return {"image_base64": b64}

@app.get("/api/params/{session_id}")
async def get_params(session_id: str):
    if session_id not in sessions: return {}
    s = sessions[session_id]
    return {
        "max_colors": s.max_colors,
        "grid_width_cells": s.grid_width_cells,
        "brightness": s.brightness,
        "contrast": s.contrast,
        "saturation": s.saturation,
        "gamma": s.gamma,
        "posterize": s.posterize,
        "gauge_stitches": s.gauge_stitches,
        "gauge_rows": s.gauge_rows,
        "show_grid": s.show_grid,
        "highlighted_row": s.highlighted_row
    }

@app.post("/api/region/replace/{session_id}")
async def region_replace_endpoint(session_id: str, payload: RegionReplaceRequest):
    if session_id not in sessions: raise HTTPException(404)
    sessions[session_id].replace_index_in_region(
        payload.x, payload.y, payload.w, payload.h,
        payload.from_index, payload.to_index
    )
    return {"message": "Cor substituída na região"}