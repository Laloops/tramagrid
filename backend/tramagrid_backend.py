# filename: tramagrid_backend.py
from PIL import Image, ImageDraw, ImageEnhance
import math
from collections import defaultdict
import io
import base64
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Tuple, List

# Armazenamento em memória das sessões (em produção use Redis ou banco de dados)
sessions: Dict[str, "TramaGridSession"] = {}

class TramaGridSession:
    """Classe que contém todo o estado e lógica do conversor de imagem → grade de tricô/crochê"""
    def __init__(self):
        self.original: Optional[Image.Image] = None
        self.processed: Optional[Image.Image] = None
        self.quantized: Optional[Image.Image] = None
        self.palette: Dict[int, Tuple[int, int, int]] = {}  # paleta atual (índice → RGB)
        self.custom_palette: Dict[int, Tuple[int, int, int]] = {}  # alterações feitas pelo usuário
        self.grid_image: Optional[Image.Image] = None
        self.grid_width_cells: int = 130  # largura em “pontos” (células)
        self.cell_size: int = 22
        self.zoom: float = 1.0
        self.highlighted_row: int = -1
        self.max_colors: int = 64
        self.brightness: float = 1.0
        self.contrast: float = 1.0

    # ------------------------------------------------------------------
    # Carregamento e geração inicial
    # ------------------------------------------------------------------
    def load_image(self, file_bytes: bytes) -> None:
        self.original = Image.open(io.BytesIO(file_bytes)).convert("RGB")

    def generate_grid(self) -> None:
        if not self.original:
            raise ValueError("Nenhuma imagem carregada")
        img = self.original.copy()
        img = ImageEnhance.Brightness(img).enhance(self.brightness)
        img = ImageEnhance.Contrast(img).enhance(self.contrast)
        w, h = img.size
        new_w = self.grid_width_cells
        new_h = int(h * new_w / w)
        self.processed = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self.quantized = self.processed.quantize(
            colors=self.max_colors, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG
        )
        # Reconstrói a paleta a partir da quantização
        raw_palette = self.quantized.getpalette()[:self.max_colors * 3]
        base_palette = {}
        for i in range(self.max_colors):
            r, g, b = raw_palette[i*3:i*3+3]
            base_palette[i] = (r, g, b)
        # Mescla com as cores customizadas pelo usuário (elas prevalecem)
        self.palette = {i: self.custom_palette.get(i, cor) for i, cor in base_palette.items()}
        self._draw_grid()

    # ------------------------------------------------------------------
    # Desenho da grade com numeração e linhas de 10 em 10
    # ------------------------------------------------------------------
    def _draw_grid(self) -> None:
        if not self.quantized:
            return
        margin = 50
        w_cells, h_cells = self.quantized.size
        total_w = margin + w_cells * self.cell_size + 20
        total_h = margin + h_cells * self.cell_size + 20
        grid = Image.new("RGB", (total_w, total_h), "white")
        draw = ImageDraw.Draw(grid)
        # Quadrados + linhas finas
        for y in range(h_cells):
            for x in range(w_cells):
                idx = self.quantized.getpixel((x, y))
                color = self.palette.get(idx, (255, 255, 255))
                px = margin + x * self.cell_size
                py = margin + y * self.cell_size
                draw.rectangle([px, py, px + self.cell_size - 1, py + self.cell_size - 1], fill=color)
                if x < w_cells - 1:
                    draw.line([(px + self.cell_size - 1, py), (px + self.cell_size - 1, py + self.cell_size - 1)], fill=(200, 200, 200))
                if y < h_cells - 1:
                    draw.line([(px, py + self.cell_size - 1), (px + self.cell_size - 1, py + self.cell_size - 1)], fill=(200, 200, 200))
                if x % 10 == 0 and x > 0:
                    draw.line([(px - 1, py), (px - 1, py + self.cell_size)], fill="black", width=3)
                if y % 10 == 0 and y > 0:
                    draw.line([(px, py - 1), (px + self.cell_size, py - 1)], fill="black", width=3)
        # Numeração horizontal e vertical
        for x in range(w_cells):
            draw.text((margin + x * self.cell_size + 11, 25), str(x + 1), fill="#333", anchor="mm")
        for y in range(h_cells):
            draw.text((20, margin + y * self.cell_size + 11), str(y + 1), fill="#333", anchor="mm")
        self.grid_image = grid

    # ------------------------------------------------------------------
    # Informações da paleta (para o frontend)
    # ------------------------------------------------------------------
    def get_palette_info(self) -> List[Dict]:
        if not self.quantized:
            return []
        usage = defaultdict(int)
        w, h = self.quantized.size
        for y in range(h):
            for x in range(w):
                idx = self.quantized.getpixel((x, y))
                if idx in self.palette:
                    usage[idx] += 1
        result = []
        for idx, count in sorted(usage.items(), key=lambda item: -item[1]):
            r, g, b = self.palette[idx]
            result.append({
                "index": idx,
                "hex": f"#{r:02x}{g:02x}{b:02x}",
                "count": count
            })
        return result

    # ------------------------------------------------------------------
    # Alteração de cor individual
    # ------------------------------------------------------------------
    def replace_color(self, index: int, new_hex: str) -> None:
        if index not in self.palette:
            raise ValueError("Índice de cor inválido")
        r = int(new_hex[1:3], 16)
        g = int(new_hex[3:5], 16)
        b = int(new_hex[5:7], 16)
        new_rgb = (r, g, b)
        self.custom_palette[index] = new_rgb
        self.palette[index] = new_rgb
        self._draw_grid()

    # ------------------------------------------------------------------
    # Deleção e fusão de cor
    # ------------------------------------------------------------------
    @staticmethod
    def _color_distance(c1: Tuple[int, int, int], c2: Tuple[int, int, int]) -> float:
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))

    def _nearest_color_index(self, color: Tuple[int, int, int], ignore: Optional[int] = None) -> Optional[int]:
        best_idx = None
        best_dist = float('inf')
        for idx, c in self.palette.items():
            if idx == ignore:
                continue
            d = self._color_distance(color, c)
            if d < best_dist:
                best_dist = d
                best_idx = idx
        return best_idx

    def delete_color(self, index_to_remove: int) -> None:
        if index_to_remove not in self.palette:
            raise ValueError("Cor não existe na paleta")
        nearest = self._nearest_color_index(self.palette[index_to_remove], ignore=index_to_remove)
        if nearest is None:
            raise ValueError("Não há outra cor para mesclar")
        w, h = self.quantized.size
        for y in range(h):
            for x in range(w):
                if self.quantized.getpixel((x, y)) == index_to_remove:
                    self.quantized.putpixel((x, y), nearest)
        self.custom_palette.pop(index_to_remove, None)
        self.palette.pop(index_to_remove, None)
        self._reindex_palette()
        self._draw_grid()

    def _reindex_palette(self) -> None:
        old_indices = sorted(self.palette.keys())
        mapping = {old: new for new, old in enumerate(old_indices)}
        new_palette = {new: self.palette[old] for new, old in enumerate(old_indices)}
        # Remapeia pixels
        w, h = self.quantized.size
        for y in range(h):
            for x in range(w):
                old = self.quantized.getpixel((x, y))
                self.quantized.putpixel((x, y), mapping.get(old, 0))
        # Atualiza paleta customizada
        new_custom = {mapping.get(k, k): v for k, v in self.custom_palette.items() if k in mapping}
        self.palette = new_palette
        self.custom_palette = new_custom

    # ------------------------------------------------------------------
    # Simplificação híbrida de paleta
    # ------------------------------------------------------------------
    def simplify_palette(self, intensity: int) -> None:  # 0 = muito detalhe, 100 = muito simplificado
        if not self.palette:
            return
        max_dist = 300.0
        threshold = (intensity / 100.0) * max_dist
        # Agrupamento inicial por distância
        groups: List[List[Tuple[int, Tuple[int, int, int]]]] = []
        for idx, color in self.palette.items():
            placed = False
            for g in groups:
                if self._color_distance(color, g[0][1]) <= threshold:
                    g.append((idx, color))
                    placed = True
                    break
            if not placed:
                groups.append([(idx, color)])
        # Quantidade desejada de cores finais
        current_colors = len(self.palette)
        target = max(1, 1 + int(current_colors * (100 - intensity) / 100.0))
        # Mescla grupos pequenos até atingir o target
        if len(groups) > target:
            groups = sorted(groups, key=len)
            while len(groups) > target:
                small = groups.pop(0)
                avg = tuple(sum(c[i] for _, c in small) // len(small) for i in range(3))
                best_i = min(range(len(groups)), key=lambda i: self._color_distance(avg, groups[i][0][1]))
                groups[best_i].extend(small)
        # Cria nova paleta e mapeamento
        old_to_new = {}
        new_palette = {}
        for new_idx, group in enumerate(groups):
            avg = tuple(sum(c[i] for _, c in group) // len(group) for i in range(3))
            new_palette[new_idx] = avg
            for old_idx, _ in group:
                old_to_new[old_idx] = new_idx
        # Remapeia pixels
        w, h = self.quantized.size
        for y in range(h):
            for x in range(w):
                old = self.quantized.getpixel((x, y))
                new = old_to_new.get(old)
                if new is None:  # fallback
                    old_rgb = self.palette.get(old, (0, 0, 0))
                    new = min(new_palette.items(), key=lambda item: self._color_distance(old_rgb, item[1]))[0]
                self.quantized.putpixel((x, y), new)
        # Atualiza paleta customizada
        self.custom_palette = {old_to_new.get(k, k): v for k, v in self.custom_palette.items() if k in old_to_new}
        self.palette = new_palette
        self._draw_grid()

    def simplify_bw_smart(self) -> None:
        if not self.palette:
            return
        lums = [0.299*r + 0.587*g + 0.114*b for r, g, b in self.palette.values()]
        amplitude = max(lums) - min(lums) if lums else 0
        intensity = 8 if amplitude < 30 else 20 if amplitude < 80 else 35
        self.simplify_palette(intensity)

    # ------------------------------------------------------------------
    # Exportação da grade (base64 para o frontend)
    # ------------------------------------------------------------------
    def get_grid_base64(self) -> str:
        if not self.grid_image:
            raise ValueError("Grade ainda não gerada")
        img = self.grid_image.copy()
        # Destaque de linha (se houver)
        if self.highlighted_row >= 0:
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            m = 50
            draw.rectangle([m, m, m + self.grid_width_cells*self.cell_size - 1, m + self.quantized.height*self.cell_size - 1], fill=(0, 0, 0, 140))
            py = m + (self.highlighted_row - 1) * self.cell_size
            draw.rectangle([m, py, m + self.grid_width_cells*self.cell_size - 1, py + self.cell_size - 1], fill=(0, 0, 0, 0))
            img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        # Zoom
        if self.zoom != 1.0:
            new_size = (int(img.width * self.zoom), int(img.height * self.zoom))
            img = img.resize(new_size, Image.NEAREST)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()

    def save_grid_to_disk(self, filepath: str) -> None:
        if self.grid_image:
            self.grid_image.save(filepath, dpi=(300, 300))

# ============================== FASTAPI ==============================
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ajuste em produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Modelos de requisição -----------------
class SessionResponse(BaseModel):
    session_id: str

class ParamsUpdate(BaseModel):
    max_colors: Optional[int] = None
    grid_width_cells: Optional[int] = None
    brightness: Optional[float] = None
    contrast: Optional[float] = None
    zoom: Optional[float] = None
    highlighted_row: Optional[int] = None

class ColorReplace(BaseModel):
    index: int
    new_hex: str

class ColorDelete(BaseModel):
    index: int

class SimplifyRequest(BaseModel):
    intensity: int  # 0–100

# ----------------- Rotas -----------------
@app.post("/api/session", response_model=SessionResponse)
async def create_session():
    sid = str(uuid.uuid4())
    sessions[sid] = TramaGridSession()
    return {"session_id": sid}

@app.post("/api/upload/{session_id}")
async def upload_image(session_id: str, file: UploadFile = File(...)):
    if session_id not in sessions:
        raise HTTPException(404, "Sessão não encontrada")
    content = await file.read()
    sessions[session_id].load_image(content)
    return {"message": "Imagem carregada com sucesso"}

@app.post("/api/generate/{session_id}")
async def generate(session_id: str):
    if session_id not in sessions:
        raise HTTPException(404, "Sessão não encontrada")
    sessions[session_id].generate_grid()
    return {"message": "Grade gerada"}

@app.get("/api/palette/{session_id}")
async def palette(session_id: str):
    if session_id not in sessions:
        raise HTTPException(404, "Sessão não encontrada")
    return sessions[session_id].get_palette_info()

@app.post("/api/params/{session_id}")
async def update_params(session_id: str, data: ParamsUpdate):
    if session_id not in sessions:
        raise HTTPException(404, "Sessão não encontrada")
    s = sessions[session_id]
    if data.max_colors is not None:
        s.max_colors = data.max_colors
    if data.grid_width_cells is not None:
        s.grid_width_cells = data.grid_width_cells
    if data.brightness is not None:
        s.brightness = data.brightness
    if data.contrast is not None:
        s.contrast = data.contrast
    if data.zoom is not None:
        s.zoom = max(0.4, min(data.zoom, 8.0))
    if data.highlighted_row is not None:
        s.highlighted_row = data.highlighted_row
    return {"message": "Parâmetros atualizados"}

@app.post("/api/color/replace/{session_id}")
async def replace_color(session_id: str, payload: ColorReplace):
    if session_id not in sessions:
        raise HTTPException(404, "Sessão não encontrada")
    sessions[session_id].replace_color(payload.index, payload.new_hex)
    return {"message": "Cor substituída"}

@app.post("/api/color/delete/{session_id}")
async def delete_color(session_id: str, payload: ColorDelete):
    if session_id not in sessions:
        raise HTTPException(404, "Sessão não encontrada")
    sessions[session_id].delete_color(payload.index)
    return {"message": "Cor removida"}

@app.post("/api/simplify/{session_id}")
async def simplify(session_id: str, payload: SimplifyRequest):
    if session_id not in sessions:
        raise HTTPException(404, "Sessão não encontrada")
    sessions[session_id].simplify_palette(payload.intensity)
    return {"message": "Paleta simplificada"}

@app.post("/api/simplify-bw/{session_id}")
async def simplify_bw(session_id: str):
    if session_id not in sessions:
        raise HTTPException(404, "Sessão não encontrada")
    sessions[session_id].simplify_bw_smart()
    return {"message": "Simplificação preto & branco inteligente aplicada"}

@app.get("/api/grid/{session_id}")
async def get_grid(session_id: str):
    if session_id not in sessions:
        raise HTTPException(404, "Sessão não encontrada")
    b64 = sessions[session_id].get_grid_base64()
    return {"image_base64": b64}

# ------------------------------------------------------------------
# Nova rota para calcular o row correto a partir do clique do usuário
# ------------------------------------------------------------------
class ClickData(BaseModel):
    click_y: float   # coordenada Y do clique dentro da imagem (já com zoom aplicado)
    zoom: float      # zoom atual no frontend


# Executar com: uvicorn tramagrid_backend:app --reload