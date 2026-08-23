import io
import json
import os
from pathlib import Path
import shutil
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import re
import unicodedata
import urllib.request

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None

try:
    from validator import validate_portfolio_data
except ImportError:
    validate_portfolio_data = None

try:
    from build import run_build
except ImportError:
    run_build = None

IMAGE_CACHE = {}
IMAGE_KEYS = {"icon", "thumbnail", "image", "images", "photo", "avatar", "profilephoto", "logo"}
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg")
TARGET_IMAGE_DIR = Path.cwd() / "assets" / "imagens" / "ThumbProjetos"


def slugify_folder_name(name: str) -> str:
    """Gera um nome de pasta seguro em formato slug a partir do título do projeto."""
    if not name or not isinstance(name, str):
        return "projeto"
    name_clean = name.split("(")[0].strip()
    normalized = unicodedata.normalize("NFKD", name_clean).encode("ASCII", "ignore").decode("ASCII")
    slug = re.sub(r"[^a-zA-Z0-9_\-]+", "-", normalized).strip("-").lower()
    return slug or "projeto"


def get_project_folder_from_context(data_dict: dict) -> str:
    """Retorna o nome da subpasta do projeto baseado nos caminhos existentes ou título."""
    if not isinstance(data_dict, dict):
        return ""

    thumb = data_dict.get("thumbnail", "")
    if thumb and isinstance(thumb, str) and "ThumbProjetos/" in thumb:
        parts = thumb.split("ThumbProjetos/")[-1].replace("\\", "/").split("/")
        if len(parts) > 1 and parts[0]:
            return parts[0]

    images = data_dict.get("images", [])
    if isinstance(images, list) and images:
        for img in images:
            if isinstance(img, str) and "ThumbProjetos/" in img:
                parts = img.split("ThumbProjetos/")[-1].replace("\\", "/").split("/")
                if len(parts) > 1 and parts[0]:
                    return parts[0]

    title = data_dict.get("title", "")
    if title:
        return slugify_folder_name(title)

    return ""


def import_image_files(multiple=False, subfolder=None):
    """
    Abre o diálogo nativo do SO para escolher arquivo(s) de imagem,
    copia automaticamente para assets/imagens/ThumbProjetos/<subfolder>/ (se subfolder informada)
    ou assets/imagens/ThumbProjetos/ e retorna lista de caminhos relativos.
    """
    if subfolder:
        target_dir = TARGET_IMAGE_DIR / subfolder
        rel_prefix = f"./assets/imagens/ThumbProjetos/{subfolder}"
    else:
        target_dir = TARGET_IMAGE_DIR
        rel_prefix = "./assets/imagens/ThumbProjetos"

    target_dir.mkdir(parents=True, exist_ok=True)
    filetypes = [
        ("Imagens", "*.png *.jpg *.jpeg *.webp *.gif *.svg"),
        ("Todos os arquivos", "*.*")
    ]
    if multiple:
        files = filedialog.askopenfilenames(title="Selecionar Imagens para o Projeto", filetypes=filetypes)
        if not files: return []
        selected_files = files
    else:
        file = filedialog.askopenfilename(title="Selecionar Imagem para o Projeto", filetypes=filetypes)
        if not file: return []
        selected_files = [file]

    rel_paths = []
    for src in selected_files:
        src_path = Path(src)
        if not src_path.exists(): continue
        dst_path = target_dir / src_path.name
        try:
            shutil.copy2(src_path, dst_path)
            rel_path = f"{rel_prefix}/{src_path.name}"
            rel_paths.append(rel_path)
        except Exception as e:
            messagebox.showerror("Erro ao Copiar Imagem", f"Não foi possível copiar '{src_path.name}':\n{e}")
    return rel_paths


def is_image_field(key_name, val=None):
    key_name_lower = str(key_name).lower()
    if any(k in key_name_lower for k in IMAGE_KEYS):
        return True
    if isinstance(val, str):
        val_lower = val.lower().split("?")[0]
        if any(val_lower.endswith(ext) for ext in IMAGE_EXTENSIONS):
            return True
    return False


PIL_CACHE = {}
PHOTO_CACHE = {}


def load_pil_image(img_source: str, max_size=(200, 130)):
    if not Image:
        return None, "PIL indisponível"
    if not img_source or not isinstance(img_source, str):
        return None, "Caminho inválido"

    img_source = img_source.strip()
    cache_key = (img_source, max_size)
    if cache_key in PIL_CACHE:
        return PIL_CACHE[cache_key], None

    try:
        if img_source.startswith("http://") or img_source.startswith("https://"):
            req = urllib.request.Request(img_source, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = resp.read()
            raw_img = Image.open(io.BytesIO(data))
        else:
            local_path = Path(img_source)
            if not local_path.exists():
                local_path = Path.cwd() / img_source.lstrip("./")
            if not local_path.exists():
                return None, f"Não encontrado: {img_source}"
            raw_img = Image.open(local_path)

        if raw_img.mode in ("P", "1", "CMYK"):
            raw_img = raw_img.convert("RGBA")

        img_copy = raw_img.copy()
        img_copy.thumbnail(max_size, Image.Resampling.LANCZOS)
        PIL_CACHE[cache_key] = img_copy
        return img_copy, None
    except Exception as e:
        return None, str(e)


def update_image_preview(label_widget, img_source, max_size=(200, 130)):
    if not label_widget or not label_widget.winfo_exists():
        return
    if not img_source or not str(img_source).strip():
        label_widget.config(text="🖼️ Sem imagem", image="", width=0, height=0)
        label_widget.image = None
        return

    img_source = img_source.strip()
    cache_key = (img_source, max_size)

    if cache_key in PHOTO_CACHE:
        photo = PHOTO_CACHE[cache_key]
        label_widget.config(image=photo, text="", width=0, height=0)
        label_widget.image = photo
        return

    label_widget.config(text="⌛ Carregando...", image="")

    def _loader():
        pil_img, err = load_pil_image(img_source, max_size=max_size)

        def _apply():
            try:
                if not label_widget.winfo_exists():
                    return
                if pil_img and ImageTk:
                    if cache_key not in PHOTO_CACHE:
                        PHOTO_CACHE[cache_key] = ImageTk.PhotoImage(pil_img)
                    photo = PHOTO_CACHE[cache_key]
                    label_widget.config(image=photo, text="", width=0, height=0)
                    label_widget.image = photo
                else:
                    err_msg = str(err)
                    short_err = err_msg[:25] + "..." if len(err_msg) > 25 else err_msg
                    label_widget.config(text=f"🖼️ [{short_err}]", image="", width=0, height=0)
                    label_widget.image = None
            except Exception as e:
                print(f"[ERRO_IMAGE_PREVIEW] {e}")

        try:
            if label_widget.winfo_exists():
                label_widget.after(0, _apply)
        except Exception as e:
            print(f"[ERRO_IMAGE_PREVIEW] {e}")

    threading.Thread(target=_loader, daemon=True).start()


def update_multi_image_gallery(gallery_frame, image_list, max_size=(180, 115)):
    """Limpa e recria os contêineres de pré-visualização para cada uma das N imagens da lista."""
    for child in gallery_frame.winfo_children():
        child.destroy()

    if not image_list:
        lbl_empty = tk.Label(
            gallery_frame,
            text="🖼️ Nenhuma imagem na galeria",
            bg=CARD_BG,
            fg="#778ca3",
            font=("Segoe UI", 8),
            relief="solid",
            bd=1,
            padx=8,
            pady=4,
        )
        lbl_empty.pack(side=tk.LEFT, padx=2, pady=2)
        return

    for idx, img_src in enumerate(image_list):
        if not img_src:
            continue
        card = tk.Frame(
            gallery_frame,
            bg=CARD_BG,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
            padx=4,
            pady=4,
        )
        card.pack(side=tk.LEFT, padx=4, pady=2)

        lbl_title = tk.Label(
            card,
            text=f"Imagem {idx + 1}",
            font=("Segoe UI", 8, "bold"),
            fg="#4b6584",
            bg=CARD_BG,
        )
        lbl_title.pack(anchor="w", pady=(0, 2))

        lbl_img = tk.Label(
            card,
            text="⌛ Carregando...",
            bg=CARD_BG,
            fg="#778ca3",
            font=("Segoe UI", 8),
            padx=2,
            pady=2,
        )
        lbl_img.pack()

        update_image_preview(lbl_img, img_src, max_size=max_size)

# Chaves conhecidas que armazenam listas de dicionários (Objetos complexos)
LISTS_OF_DICTS = {"socials", "cta", "stats", "links", "education", "experiences", "certificates", "skills", "projects"}

# Modelos vazios para quando o usuário clicar em "Adicionar Novo" em uma lista vazia
TEMPLATES = {
    "socials": {"label": "", "icon": "", "url": ""},
    "cta": {"label": "", "url": "", "type": ""},
    "stats": {"value": "", "label": ""},
    "links": {"label": "", "url": ""},
    "education": {"institution": "", "degree": "", "period": "", "type": "", "issuer": "", "description": ""},
    "experiences": {"title": "", "company": "", "companyUrl": "", "type": "", "period": "", "location": "", "description": "", "achievements": [], "technologies": []},
    "certificates": {"title": "", "url": ""},
    "skills": {"name": "", "icon": "", "alt": "", "category": ""},
    "projects": {"title": "", "description": "", "longDescription": "", "category": "", "year": "", "status": "", "thumbnail": "", "images": [], "technologies": [], "links": []}
}

# Cores da Paleta Moderna
BG_COLOR = "#f4f6f9"        # Fundo principal claro
CARD_BG = "#ffffff"         # Fundo de itens/cards
BORDER_COLOR = "#ced4da"    # Bordas inativas
FOCUS_COLOR = "#3498db"     # Bordas ativas/selecionadas
TEXT_COLOR = "#2d3436"      # Cor do texto principal
TOP_BAR_BG = "#1e272e"      # Barra superior escura

class ScrollableFrame(ttk.Frame):
    """Componente customizado para criar áreas com barra de rolagem vertical (Scroll)."""
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        # Configurando o fundo do canvas para combinar com o app
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0, bg=BG_COLOR)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        
        # Frame interno com background claro
        self.inner_frame = tk.Frame(self.canvas, bg=BG_COLOR)

        self.inner_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.bind_mouse_wheel()

    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def bind_mouse_wheel(self):
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.canvas.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))


class PortfolioCRUDApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerenciador de Portfólio JSON")
        self.root.geometry("1100x750")
        self.root.configure(bg=BG_COLOR)
        
        # Configurar Estilos Modernos do TTK
        self.style = ttk.Style()
        self.style.theme_use('clam') # Tema mais limpo e flat
        self.style.configure("TNotebook", background=BG_COLOR, borderwidth=0)
        self.style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[15, 5], background="#e1e5ea", foreground=TEXT_COLOR)
        self.style.map("TNotebook.Tab", background=[("selected", CARD_BG)], foreground=[("selected", FOCUS_COLOR)])
        
        self.filepath = "portfolio-data.json"
        self.data = {}
        self.current_selections = {}
        
        self.load_data()
        self.build_main_ui()

    def load_data(self):
        if not os.path.exists(self.filepath):
            messagebox.showwarning("Aviso", f"Arquivo {self.filepath} não encontrado. Um novo será criado.")
            self.data = {}
            return

        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao ler o arquivo JSON:\n{e}")
            self.data = {}

    def save_data(self):
        if validate_portfolio_data:
            errors = validate_portfolio_data(self.data)
            if errors:
                err_msg = "\n".join(errors[:5])
                if len(errors) > 5:
                    err_msg += f"\n...e mais {len(errors) - 5} erro(s)."
                if not messagebox.askyesno("Aviso de Validação", f"O JSON possui inconsistências:\n\n{err_msg}\n\nDeseja salvar mesmo assim?"):
                    return

        try:
            if os.path.exists(self.filepath):
                shutil.copy(self.filepath, self.filepath + ".backup")

            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
            
            build_status = ""
            if run_build:
                try:
                    if run_build(self.filepath, "index.html"):
                        build_status = "\n\n⚡ Build estático gerado com sucesso!"
                    else:
                        build_status = "\n\n⚠️ O build estático retornou erros."
                except Exception as be:
                    build_status = f"\n\n⚠️ Erro ao executar o build: {be}"

            messagebox.showinfo("Sucesso", f"Dados salvos com sucesso e backup criado!{build_status}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar:\n{e}")

    def trigger_build(self):
        if not run_build:
            messagebox.showerror("Erro", "Módulo build.py não encontrado.")
            return
        try:
            if run_build(self.filepath, "index.html"):
                messagebox.showinfo("Sucesso", "Build estático (HTML, SEO, Sitemap) gerado com sucesso!")
            else:
                messagebox.showerror("Erro", "O build estático falhou. Verifique os dados no JSON.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao executar build:\n{e}")

    def build_main_ui(self):
        # Barra superior (Header)
        top_frame = tk.Frame(self.root, bg=TOP_BAR_BG, pady=15, padx=20)
        top_frame.pack(fill=tk.X)
        
        lbl_title = tk.Label(top_frame, text="Painel de Edição de Portfólio", fg="white", bg=TOP_BAR_BG, font=("Segoe UI", 16, "bold"))
        lbl_title.pack(side=tk.LEFT)

        btn_save = tk.Button(top_frame, text="💾 Salvar no JSON", bg="#20bf6b", fg="white", font=("Segoe UI", 10, "bold"), 
                             relief="flat", cursor="hand2", padx=15, pady=6, activebackground="#26de81", activeforeground="white", command=self.save_data)
        btn_save.pack(side=tk.RIGHT)

        btn_build = tk.Button(top_frame, text="⚡ Gerar Build", bg="#3867d6", fg="white", font=("Segoe UI", 10, "bold"), 
                              relief="flat", cursor="hand2", padx=15, pady=6, activebackground="#4b7bec", activeforeground="white", command=self.trigger_build)
        btn_build.pack(side=tk.RIGHT, padx=(0, 10))

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        for section_key, section_data in self.data.items():
            tab = tk.Frame(self.notebook, bg=BG_COLOR)
            self.notebook.add(tab, text=section_key.replace('_', ' ').title())
            
            if isinstance(section_data, dict):
                self.build_dict_tab(tab, section_key, section_data)
            elif isinstance(section_data, list):
                self.build_list_tab(tab, section_key, section_data)

    def build_dict_tab(self, parent, section_key, section_data):
        scroll_frame = ScrollableFrame(parent)
        scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        def refresh_ui():
            for w in scroll_frame.inner_frame.winfo_children(): w.destroy()
            # Adiciona um titulo na aba
            tk.Label(scroll_frame.inner_frame, text=f"Editando {section_key.title()}", font=("Segoe UI", 14, "bold"), 
                     bg=BG_COLOR, fg=TEXT_COLOR, pady=10).pack(anchor="w", padx=10)
            self.render_form(scroll_frame.inner_frame, section_data, refresh_ui)

        refresh_ui()

    def build_list_tab(self, parent, section_key, section_list):
        paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, pady=10)

        left_frame = tk.Frame(paned, bg=BG_COLOR)
        paned.add(left_frame, weight=1)

        # Listbox Estilizado
        listbox = tk.Listbox(left_frame, font=("Segoe UI", 11), exportselection=False, bg=CARD_BG, fg=TEXT_COLOR,
                             selectbackground=FOCUS_COLOR, selectforeground="white", relief="flat", 
                             highlightthickness=1, highlightcolor=BORDER_COLOR, highlightbackground=BORDER_COLOR, activestyle="none")
        listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        right_frame = ScrollableFrame(paned)
        paned.add(right_frame, weight=3)

        def refresh_listbox():
            listbox.delete(0, tk.END)
            for index, item in enumerate(self.data[section_key]):
                display_name = item.get('title', item.get('name', item.get('institution', f"Item {index + 1}")))
                listbox.insert(tk.END, f"  {display_name}") # Espaço extra para padding visual

        def refresh_right_frame():
            for w in right_frame.inner_frame.winfo_children(): w.destroy()
            idx = self.current_selections.get(section_key, None)
            if idx is not None and idx < len(self.data[section_key]):
                tk.Label(right_frame.inner_frame, text="Detalhes do Item", font=("Segoe UI", 14, "bold"), 
                         bg=BG_COLOR, fg=TEXT_COLOR, pady=10).pack(anchor="w", padx=10)
                self.render_form(right_frame.inner_frame, self.data[section_key][idx], refresh_right_frame)
                
        def on_select(event):
            selection = listbox.curselection()
            if selection:
                self.current_selections[section_key] = selection[0]
                refresh_right_frame()

        listbox.bind("<<ListboxSelect>>", on_select)
        refresh_listbox()

        # Botões da Listbox
        btn_frame1 = tk.Frame(left_frame, bg=BG_COLOR)
        btn_frame1.pack(fill=tk.X, pady=(0, 4))
        
        tk.Button(btn_frame1, text="➕ Novo", bg=FOCUS_COLOR, fg="white", relief="flat", cursor="hand2", font=("Segoe UI", 10, "bold"),
                  activebackground="#2980b9", activeforeground="white", pady=5,
                  command=lambda: self.add_top_list_item(section_key, listbox, refresh_listbox, refresh_right_frame)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        
        tk.Button(btn_frame1, text="🗑️ Excluir", bg="#eb3b5a", fg="white", relief="flat", cursor="hand2", font=("Segoe UI", 10, "bold"),
                  activebackground="#fc5c65", activeforeground="white", pady=5,
                  command=lambda: self.delete_top_list_item(section_key, listbox, refresh_listbox, right_frame.inner_frame)).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))

        btn_frame2 = tk.Frame(left_frame, bg=BG_COLOR)
        btn_frame2.pack(fill=tk.X)

        tk.Button(btn_frame2, text="⬆️ Mover Cima", bg="#4b6584", fg="white", relief="flat", cursor="hand2", font=("Segoe UI", 9, "bold"),
                  activebackground="#5f27cd", activeforeground="white", pady=4,
                  command=lambda: self.move_top_list_item_up(section_key, listbox, refresh_listbox)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        tk.Button(btn_frame2, text="⬇️ Mover Baixo", bg="#4b6584", fg="white", relief="flat", cursor="hand2", font=("Segoe UI", 9, "bold"),
                  activebackground="#5f27cd", activeforeground="white", pady=4,
                  command=lambda: self.move_top_list_item_down(section_key, listbox, refresh_listbox)).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))

    def move_top_list_item_up(self, section_key, listbox, refresh_callback):
        selection = listbox.curselection()
        if not selection: return
        idx = selection[0]
        if idx <= 0: return
        items = self.data[section_key]
        items[idx], items[idx - 1] = items[idx - 1], items[idx]
        self.current_selections[section_key] = idx - 1
        refresh_callback()
        listbox.selection_clear(0, tk.END)
        listbox.selection_set(idx - 1)
        listbox.see(idx - 1)
        listbox.event_generate("<<ListboxSelect>>")

    def move_top_list_item_down(self, section_key, listbox, refresh_callback):
        selection = listbox.curselection()
        if not selection: return
        idx = selection[0]
        items = self.data[section_key]
        if idx >= len(items) - 1: return
        items[idx], items[idx + 1] = items[idx + 1], items[idx]
        self.current_selections[section_key] = idx + 1
        refresh_callback()
        listbox.selection_clear(0, tk.END)
        listbox.selection_set(idx + 1)
        listbox.see(idx + 1)
        listbox.event_generate("<<ListboxSelect>>")

    def add_top_list_item(self, section_key, listbox=None, refresh_listbox_cb=None, refresh_right_cb=None):
        template = TEMPLATES.get(section_key, {"title": "Novo Item"}).copy()
        self.data[section_key].insert(0, template)
        self.current_selections[section_key] = 0
        if refresh_listbox_cb:
            refresh_listbox_cb()
        if listbox:
            listbox.selection_clear(0, tk.END)
            listbox.selection_set(0)
            listbox.see(0)
        if refresh_right_cb:
            refresh_right_cb()

    def delete_top_list_item(self, section_key, listbox, refresh_callback, right_inner_frame):
        selection = listbox.curselection()
        if not selection: return
        if messagebox.askyesno("Confirmar", "Tem certeza que deseja excluir este item principal?"):
            del self.data[section_key][selection[0]]
            self.current_selections[section_key] = None
            refresh_callback()
            for w in right_inner_frame.winfo_children(): w.destroy()

    def render_form(self, container, data_dict, refresh_callback):
        for key, value in data_dict.items():
            row = tk.Frame(container, bg=BG_COLOR, pady=5)
            row.pack(fill=tk.X, padx=10)
            
            lbl = tk.Label(row, text=key.replace("_", " ").title()+":", width=18, anchor='ne', 
                           font=("Segoe UI", 10, "bold"), bg=BG_COLOR, fg="#4b6584", pady=5)
            lbl.pack(side=tk.LEFT, fill=tk.Y)
            
            if isinstance(value, list):
                if key in LISTS_OF_DICTS:
                    self.render_nested_dicts(row, key, value, refresh_callback)
                else:
                    if is_image_field(key, value):
                        gallery_container = tk.Frame(row, bg=BG_COLOR)
                        gallery_container.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

                        txt_frame = tk.Frame(gallery_container, bg=BG_COLOR)
                        txt_frame.pack(fill=tk.X, expand=True)

                        tk.Label(txt_frame, text="(Uma imagem por linha)", font=("Segoe UI", 8), fg="#778ca3", bg=BG_COLOR).pack(side=tk.LEFT, padx=(0,5))

                        txt = tk.Text(txt_frame, height=4, width=45, font=("Segoe UI", 10), relief="flat", 
                                      highlightthickness=1, highlightbackground=BORDER_COLOR, highlightcolor=FOCUS_COLOR)
                        txt.insert(tk.END, "\n".join(value) if isinstance(value, list) else "")
                        txt.pack(side=tk.LEFT, fill=tk.X, expand=True)

                        gallery_frame = tk.Frame(gallery_container, bg=BG_COLOR)
                        gallery_frame.pack(fill=tk.X, expand=True, pady=(5, 0))

                        def upload_multi_images(k=key, w=txt, d=data_dict, gframe=gallery_frame):
                            subfolder = get_project_folder_from_context(d)
                            new_paths = import_image_files(multiple=True, subfolder=subfolder)
                            if new_paths:
                                cur = [l.strip() for l in w.get("1.0", tk.END).split('\n') if l.strip()]
                                for p in new_paths:
                                    if p not in cur:
                                        cur.append(p)
                                w.delete("1.0", tk.END)
                                w.insert(tk.END, "\n".join(cur))
                                d[k] = cur
                                update_multi_image_gallery(gframe, cur)

                        btn_upload_multi = tk.Button(txt_frame, text="📁 Importar do PC...", bg="#34495e", fg="white",
                                                     font=("Segoe UI", 8, "bold"), relief="flat", cursor="hand2",
                                                     activebackground="#2c3e50", activeforeground="white", padx=8, pady=3,
                                                     command=upload_multi_images)
                        btn_upload_multi.pack(side=tk.RIGHT, padx=(5, 0))

                        def update_string_list_with_gallery(event, k=key, w=txt, d=data_dict, gframe=gallery_frame):
                            lines = [l.strip() for l in w.get("1.0", tk.END).split('\n') if l.strip()]
                            d[k] = lines
                            update_multi_image_gallery(gframe, lines)

                        txt.bind("<KeyRelease>", update_string_list_with_gallery)
                        update_multi_image_gallery(gallery_frame, value if isinstance(value, list) else [])
                    else:
                        tk.Label(row, text="(Um item\npor linha)", font=("Segoe UI", 8), fg="#778ca3", bg=BG_COLOR).pack(side=tk.LEFT, padx=(0,5))
                        txt = tk.Text(row, height=4, width=50, font=("Segoe UI", 10), relief="flat", 
                                      highlightthickness=1, highlightbackground=BORDER_COLOR, highlightcolor=FOCUS_COLOR)
                        txt.insert(tk.END, "\n".join(value))
                        txt.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

                        def update_string_list(event, k=key, w=txt, d=data_dict):
                            lines = [l.strip() for l in w.get("1.0", tk.END).split('\n') if l.strip()]
                            d[k] = lines
                        txt.bind("<KeyRelease>", update_string_list)
                    
            elif isinstance(value, bool):
                var = tk.BooleanVar(value=value)
                chk = tk.Checkbutton(row, variable=var, bg=BG_COLOR, activebackground=BG_COLOR, cursor="hand2")
                chk.pack(side=tk.LEFT, padx=5)
                def update_bool(*args, k=key, v=var, d=data_dict):
                    d[k] = v.get()
                var.trace_add("write", update_bool)
                
            else:
                val_str = str(value)
                if len(val_str) > 60 or key in ["description", "longDescription", "paragraphs"]:
                    txt = tk.Text(row, height=4, width=50, font=("Segoe UI", 10), relief="flat", 
                                  highlightthickness=1, highlightbackground=BORDER_COLOR, highlightcolor=FOCUS_COLOR)
                    txt.insert(tk.END, val_str)
                    txt.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
                    
                    def update_txt(event, k=key, w=txt, d=data_dict, orig=value):
                        new_val = w.get("1.0", tk.END).strip()
                        if isinstance(orig, int):
                            try: new_val = int(new_val)
                            except: pass
                        d[k] = new_val
                    txt.bind("<KeyRelease>", update_txt)
                else:
                    var = tk.StringVar(value=val_str)
                    ent = tk.Entry(row, textvariable=var, width=50, font=("Segoe UI", 10), relief="flat", 
                                   highlightthickness=1, highlightbackground=BORDER_COLOR, highlightcolor=FOCUS_COLOR)
                    ent.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, ipady=4)
                    
                    def update_ent(*args, k=key, v=var, d=data_dict, orig=value):
                        new_val = v.get()
                        if isinstance(orig, int):
                            try: new_val = int(new_val)
                            except: pass
                        d[k] = new_val
                    var.trace_add("write", update_ent)

                    if is_image_field(key, val_str):
                        pbox = tk.Label(row, text="🖼️ Imagem", bg=CARD_BG, fg="#778ca3", font=("Segoe UI", 8), relief="solid", bd=1, padx=6, pady=6)
                        pbox.pack(side=tk.RIGHT, padx=(10, 0))

                        def upload_single_image(*args, k=key, vref=var, d=data_dict):
                            subfolder = get_project_folder_from_context(d)
                            new_paths = import_image_files(multiple=False, subfolder=subfolder)
                            if new_paths:
                                vref.set(new_paths[0])
                                d[k] = new_paths[0]

                        btn_upload_single = tk.Button(row, text="📁 Importar...", bg="#34495e", fg="white",
                                                      font=("Segoe UI", 8, "bold"), relief="flat", cursor="hand2",
                                                      activebackground="#2c3e50", activeforeground="white", padx=8, pady=3,
                                                      command=upload_single_image)
                        btn_upload_single.pack(side=tk.RIGHT, padx=(5, 0))

                        def update_entry_preview(*args, v=var, preview=pbox):
                            update_image_preview(preview, v.get())

                        var.trace_add("write", update_entry_preview)
                        update_image_preview(pbox, val_str)

    def render_nested_dicts(self, parent, key, list_data, refresh_callback):
        container = tk.Frame(parent, bg=BG_COLOR)
        container.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        tk.Label(container, text=f"Gerenciar {key.title()}", bg=BG_COLOR, fg="#4b6584", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0,5))
        
        for i, item_dict in enumerate(list_data):
            item_frame = tk.Frame(container, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1, pady=8, padx=8)
            item_frame.pack(fill=tk.X, pady=4)
            
            inputs_frame = tk.Frame(item_frame, bg=CARD_BG)
            inputs_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
            for k, v in item_dict.items():
                row = tk.Frame(inputs_frame, bg=CARD_BG)
                row.pack(fill=tk.X, pady=3)
                
                tk.Label(row, text=k.title()+":", bg=CARD_BG, width=10, anchor="w", font=("Segoe UI", 9)).pack(side=tk.LEFT)
                var = tk.StringVar(value=str(v))
                ent = tk.Entry(row, textvariable=var, font=("Segoe UI", 9), relief="flat", 
                               highlightthickness=1, highlightbackground=BORDER_COLOR, highlightcolor=FOCUS_COLOR)
                ent.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
                
                def update_val(*args, item_ref=item_dict, key_ref=k, var_ref=var):
                    item_ref[key_ref] = var_ref.get()
                var.trace_add("write", update_val)

                if is_image_field(k, str(v)):
                    pbox = tk.Label(row, text="🖼️", bg=CARD_BG, fg="#778ca3", font=("Segoe UI", 8), relief="solid", bd=1, padx=4, pady=4)
                    pbox.pack(side=tk.RIGHT, padx=(5, 0))

                    def upload_nested_image(*args, kref=k, vref=var, itemref=item_dict):
                        subfolder = get_project_folder_from_context(itemref)
                        new_paths = import_image_files(multiple=False, subfolder=subfolder)
                        if new_paths:
                            vref.set(new_paths[0])
                            itemref[kref] = new_paths[0]

                    btn_upload_nested = tk.Button(row, text="📁", bg="#34495e", fg="white", font=("Segoe UI", 8, "bold"),
                                                  relief="flat", cursor="hand2", activebackground="#2c3e50", activeforeground="white",
                                                  padx=4, pady=2, command=upload_nested_image)
                    btn_upload_nested.pack(side=tk.RIGHT, padx=(3, 0))

                    def update_nested_preview(*args, vref=var, preview=pbox):
                        update_image_preview(preview, vref.get())
                    var.trace_add("write", update_nested_preview)
                    update_image_preview(pbox, str(v))
            
            actions_frame = tk.Frame(item_frame, bg=CARD_BG)
            actions_frame.pack(side=tk.RIGHT, padx=(5, 0))

            btn_up = tk.Button(actions_frame, text="▲", bg="#4b6584", fg="white", font=("Segoe UI", 8, "bold"),
                               relief="flat", cursor="hand2", activebackground="#5f27cd", activeforeground="white",
                               command=lambda idx=i: self.move_nested_item(list_data, idx, -1, refresh_callback))
            btn_up.pack(side=tk.LEFT, padx=1)

            btn_down = tk.Button(actions_frame, text="▼", bg="#4b6584", fg="white", font=("Segoe UI", 8, "bold"),
                                 relief="flat", cursor="hand2", activebackground="#5f27cd", activeforeground="white",
                                 command=lambda idx=i: self.move_nested_item(list_data, idx, 1, refresh_callback))
            btn_down.pack(side=tk.LEFT, padx=1)

            btn_del = tk.Button(actions_frame, text="✖", bg="#eb3b5a", fg="white", font=("Segoe UI", 8, "bold"),
                                relief="flat", cursor="hand2", activebackground="#fc5c65", activeforeground="white",
                                command=lambda idx=i: self.delete_nested_item(list_data, idx, refresh_callback))
            btn_del.pack(side=tk.LEFT, padx=1)
            
        btn_add = tk.Button(container, text=f"➕ Adicionar {key}", bg="#20bf6b", fg="white", relief="flat", cursor="hand2", 
                            font=("Segoe UI", 9, "bold"), activebackground="#26de81", activeforeground="white", pady=4,
                            command=lambda: self.add_nested_item(key, list_data, refresh_callback))
        btn_add.pack(anchor="w", pady=5)

    def move_nested_item(self, list_data, idx, direction, refresh_callback):
        new_idx = idx + direction
        if 0 <= new_idx < len(list_data):
            list_data[idx], list_data[new_idx] = list_data[new_idx], list_data[idx]
            refresh_callback()

    def delete_nested_item(self, list_data, idx, refresh_callback):
        if messagebox.askyesno("Confirmar", "Remover este sub-item?"):
            del list_data[idx]
            refresh_callback()

    def add_nested_item(self, key, list_data, refresh_callback):
        template = TEMPLATES.get(key, {"chave": ""}).copy()
        list_data.append(template)
        refresh_callback()


if __name__ == "__main__":
    root = tk.Tk()
    app = PortfolioCRUDApp(root)
    root.mainloop()