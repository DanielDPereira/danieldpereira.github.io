import json
import tkinter as tk
from tkinter import ttk, messagebox
import os
import shutil

try:
    from validator import validate_portfolio_data
except ImportError:
    validate_portfolio_data = None

try:
    from build import run_build
except ImportError:
    run_build = None

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
                  command=lambda: self.add_top_list_item(section_key, refresh_listbox)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        
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

    def add_top_list_item(self, section_key, refresh_callback):
        template = TEMPLATES.get(section_key, {"title": "Novo Item"}).copy()
        self.data[section_key].append(template)
        refresh_callback()

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
                    tk.Label(row, text="(Um item\npor linha)", font=("Segoe UI", 8), fg="#778ca3", bg=BG_COLOR).pack(side=tk.LEFT, padx=(0,5))
                    txt = tk.Text(row, height=4, width=50, font=("Segoe UI", 10), relief="flat", 
                                  highlightthickness=1, highlightbackground=BORDER_COLOR, highlightcolor=FOCUS_COLOR)
                    txt.insert(tk.END, "\n".join(value))
                    txt.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
                    
                    def update_string_list(event, k=key, w=txt, d=data_dict):
                        lines = w.get("1.0", tk.END).split('\n')
                        d[k] = [line.strip() for line in lines if line.strip() != ""]
                    txt.bind("<KeyRelease>", update_string_list)
                    
            elif isinstance(value, bool):
                var = tk.BooleanVar(value=value)
                # O style de Checkbutton varia no ttk, usando tk puro com cor de fundo para consistência
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

    def render_nested_dicts(self, parent, key, list_data, refresh_callback):
        # Substitui o LabelFrame datado por um Frame limpo estilo Card
        container = tk.Frame(parent, bg=BG_COLOR)
        container.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Título da sub-seção
        tk.Label(container, text=f"Gerenciar {key.title()}", bg=BG_COLOR, fg="#4b6584", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0,5))
        
        for i, item_dict in enumerate(list_data):
            # Card Item
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