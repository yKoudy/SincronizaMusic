import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import threading, requests, os, re, time, json, webbrowser, tempfile
try:
    import pygame
except Exception:
    pygame = None
try:
    from PIL import Image, ImageTk, ImageFilter, ImageEnhance
except Exception:
    Image = ImageTk = ImageFilter = ImageEnhance = None

APP_NAME = "Sincroniza Music"
ITUNES_SEARCH = "https://itunes.apple.com/search"
LRCLIB_SEARCH = "https://lrclib.net/api/search"
CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".sincroniza_music.json")
DEFAULTS = {"mode": "dark", "accent": "#9b7bff", "wallpaper": "", "wallpaper_opacity": 0.22}
THEMES = {
    "dark": {"bg":"#0b0d14","panel":"#141824","panel2":"#1b2030","text":"#f4f5fb","muted":"#9aa3b8","line":"#2b3143","lyric":"#7f899f"},
    "light":{"bg":"#f3f5fb","panel":"#ffffff","panel2":"#e9edf6","text":"#202538","muted":"#69738a","line":"#d8deeb","lyric":"#727d93"}
}
SOCIALS = [
    ("Instagram  @oryankk.skt", "https://www.instagram.com/oryankk.skt/"),
    ("TikTok  @ryandefoutt", "https://www.tiktok.com/@ryandefoutt"),
]

class SyncMusicApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME + " — Dri GT3")
        self.root.geometry("1180x760")
        self.root.minsize(900, 620)
        self.tracks=[]; self.current_track=None; self.lyric_lines=[]; self.audio_path=None
        self.playing=False; self.preview_url=None; self.current_line=-1; self.wallpaper_image=None
        self.settings = self._load_settings()
        self.colors = THEMES.get(self.settings.get("mode"), THEMES["dark"])
        self.root.configure(bg=self.colors["bg"])
        self._build_ui()
        if pygame:
            try: pygame.mixer.init()
            except Exception: pass
        self._apply_wallpaper()
        self.root.after(180, self._tick)

    def _load_settings(self):
        cfg = DEFAULTS.copy()
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f: cfg.update(json.load(f))
        except Exception: pass
        return cfg

    def _save_settings(self):
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f: json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception: pass

    def _c(self, key): return self.colors[key]
    def _frame(self, parent, **kw): return tk.Frame(parent, bg=kw.pop("bg", self._c("panel")), **kw)
    def _label(self, parent, text, size=10, color=None, bold=False, **kw):
        return tk.Label(parent, text=text, bg=kw.pop("bg", self._c("panel")), fg=color or self._c("text"),
                        font=("Segoe UI", size, "bold" if bold else "normal"), **kw)
    def _button(self, parent, text, command, primary=False, **kw):
        bg = self.settings["accent"] if primary else self._c("panel2")
        fg = "#ffffff" if primary else self._c("text")
        return tk.Button(parent, text=text, command=command, bg=bg, fg=fg,
                         activebackground=bg, activeforeground=fg, relief="flat", bd=0,
                         cursor="hand2", font=("Segoe UI", 10, "bold" if primary else "normal"),
                         padx=14, pady=9, **kw)

    def _build_ui(self):
        self.root.configure(bg=self._c("bg"))
        self.style=ttk.Style()
        try: self.style.theme_use("clam")
        except Exception: pass
        self.style.configure("Treeview", rowheight=34, font=("Segoe UI",10), background=self._c("panel"),
            foreground=self._c("text"), fieldbackground=self._c("panel"), borderwidth=0)
        self.style.configure("Treeview.Heading", font=("Segoe UI",9,"bold"), background=self._c("panel2"),
            foreground=self._c("muted"), relief="flat")
        self.style.map("Treeview", background=[("selected", self.settings["accent"])], foreground=[("selected","#ffffff")])
        self.style.configure("Horizontal.TProgressbar", troughcolor=self._c("panel2"), background=self.settings["accent"], bordercolor=self._c("panel2"))
        self.shell=tk.Frame(self.root,bg=self._c("bg")); self.shell.pack(fill="both",expand=True)
        self.header=tk.Frame(self.shell,bg=self._c("bg"),padx=26,pady=18); self.header.pack(fill="x")
        brand=tk.Frame(self.header,bg=self._c("bg")); brand.pack(side="left")
        self._label(brand,"◈  SINCRONIZA",21,bold=True,bg=self._c("bg")).pack(side="left")
        self._label(brand," MUSIC",21,color=self.settings["accent"],bold=True,bg=self._c("bg")).pack(side="left")
        self._label(self.header,"MÚSICA • LETRAS • SEU CLIMA",9,color=self._c("muted"),bg=self._c("bg")).pack(side="left",padx=18,pady=(8,0))
        self._button(self.header,"⚙ Aparência",self.open_settings).pack(side="right",padx=(8,0))
        self._button(self.header,"♡ Sobre",self.show_thanks).pack(side="right")
        searchbar=tk.Frame(self.shell,bg=self._c("bg"),padx=26,pady=(0,16)); searchbar.pack(fill="x")
        self.query=tk.StringVar()
        self.search_entry=tk.Entry(searchbar,textvariable=self.query,font=("Segoe UI",12),bg=self._c("panel"),
            fg=self._c("text"),insertbackground=self._c("text"),relief="flat",bd=0)
        self.search_entry.pack(side="left",fill="x",expand=True,ipady=12,padx=(0,10))
        self.search_entry.insert(0,"  Pesquise por música ou artista…")
        self.search_entry.bind("<FocusIn>",self._clear_placeholder)
        self.search_entry.bind("<Return>",lambda e:self.search())
        self._button(searchbar,"⌕  Pesquisar",self.search,primary=True).pack(side="left")
        self._button(searchbar,"＋ Áudio local",self.open_audio).pack(side="left",padx=(8,0))

        self.content=tk.Frame(self.shell,bg=self._c("bg"),padx=26); self.content.pack(fill="both",expand=True)
        self.results_card=tk.Frame(self.content,bg=self._c("panel"),width=360); self.results_card.pack(side="left",fill="y",padx=(0,16)); self.results_card.pack_propagate(False)
        self._label(self.results_card,"  DESCOBRIR",10,color=self._c("muted"),bold=True).pack(anchor="w",padx=12,pady=(16,4))
        self._label(self.results_card,"Resultados da pesquisa",14,bold=True).pack(anchor="w",padx=16,pady=(0,10))
        cols=("title","artist")
        self.result_tree=ttk.Treeview(self.results_card,columns=cols,show="headings",selectmode="browse")
        self.result_tree.heading("title",text="FAIXA"); self.result_tree.heading("artist",text="ARTISTA")
        self.result_tree.column("title",width=205,stretch=True); self.result_tree.column("artist",width=130,stretch=True)
        self.result_tree.pack(fill="both",expand=True,padx=12,pady=(0,12))
        self.result_tree.bind("<<TreeviewSelect>>",self.select_track)
        self.result_tree.bind("<Double-1>",lambda e:self.load_selected())

        self.player_card=tk.Frame(self.content,bg=self._c("panel")); self.player_card.pack(side="left",fill="both",expand=True)
        self.song_head=tk.Frame(self.player_card,bg=self._c("panel"),padx=22,pady=18); self.song_head.pack(fill="x")
        self._label(self.song_head,"AGORA EM FOCO",9,color=self.settings["accent"],bold=True).pack(anchor="w")
        self.song_label=self._label(self.song_head,"Escolha uma música",19,bold=True,wraplength=590,justify="left")
        self.song_label.pack(anchor="w",pady=(7,3))
        self.status=self._label(self.song_head,"Pesquise uma faixa para começar sua sessão.",9,color=self._c("muted"))
        self.status.pack(anchor="w")
        self.lyric_wrap=tk.Frame(self.player_card,bg=self._c("panel2"),highlightbackground=self._c("line"),highlightthickness=1)
        self.lyric_wrap.pack(fill="both",expand=True,padx=16,pady=(0,14))
        self.lyrics=tk.Text(self.lyric_wrap,bg=self._c("panel2"),fg=self._c("lyric"),insertbackground=self._c("text"),
            font=("Segoe UI",17),relief="flat",wrap="word",padx=24,pady=24,spacing1=12,spacing3=12,
            borderwidth=0,highlightthickness=0)
        self.lyrics.pack(fill="both",expand=True,padx=4,pady=4)
        self.lyrics.tag_configure("active",foreground="#ffffff",background=self.settings["accent"],font=("Segoe UI",18,"bold"),lmargin1=12,lmargin2=12,spacing1=12,spacing3=12)
        self.lyrics.tag_configure("normal",foreground=self._c("lyric"))
        self.lyrics.tag_configure("future",foreground=self._c("muted"))
        self.lyrics.insert("end","♪\n\nSua música merece um momento só dela.\n\nPesquise uma faixa e carregue a letra sincronizada.","normal")
        controls=tk.Frame(self.player_card,bg=self._c("panel"),padx=16,pady=12); controls.pack(fill="x")
        self.play_btn=self._button(controls,"▶  Reproduzir",self.toggle_play,primary=True); self.play_btn.pack(side="left")
        self._button(controls,"♫  Buscar letra",self.load_selected).pack(side="left",padx=8)
        self._label(controls,"FEITO COM CUIDADO POR  DRI GT3",8,color=self._c("muted")).pack(side="right",pady=10)
        self.progress=ttk.Progressbar(self.player_card,mode="determinate",maximum=100)
        self.progress.pack(fill="x",padx=18,pady=(0,16))
        self.footer=tk.Frame(self.shell,bg=self._c("bg"),padx=28,pady=9); self.footer.pack(fill="x")
        self.footer_status=self._label(self.footer,"●  PRONTO PARA TOCAR",8,color=self._c("muted"),bg=self._c("bg")); self.footer_status.pack(side="left")
        self._label(self.footer,"Versão de desenvolvimento  •  Dri GT3",8,color=self._c("muted"),bg=self._c("bg")).pack(side="right")

    def _clear_placeholder(self,event=None):
        if self.query.get().strip()=="Pesquise por música ou artista…": self.query.set("")

    def set_status(self,text):
        self.root.after(0,lambda: self.status.config(text=text))

    def search(self):
        q=self.query.get().strip()
        if q in ("","Pesquise por música ou artista…"):
            messagebox.showinfo(APP_NAME,"Digite o nome de uma música ou artista."); return
        self.status.config(text="Buscando faixas…")
        threading.Thread(target=self._search_worker,args=(q,),daemon=True).start()

    def _search_worker(self,q):
        try:
            r=requests.get(ITUNES_SEARCH,params={"term":q,"entity":"song","limit":35},timeout=15); r.raise_for_status()
            self.tracks=[{"title":x.get("trackName","Título desconhecido"),"artist":x.get("artistName","Artista desconhecido"),
              "album":x.get("collectionName",""),"duration":x.get("trackTimeMillis",0)/1000,"preview":x.get("previewUrl"),"url":x.get("trackViewUrl")}
              for x in r.json().get("results",[])]
            self.root.after(0,self._show_results)
        except Exception as e:
            self.set_status("Falha na pesquisa. Verifique a conexão.")
            self.root.after(0,lambda:messagebox.showerror(APP_NAME,f"Não foi possível pesquisar músicas.\n\n{e}"))

    def _show_results(self):
        for item in self.result_tree.get_children(): self.result_tree.delete(item)
        for i,t in enumerate(self.tracks): self.result_tree.insert("","end",iid=str(i),values=(t["title"],t["artist"]))
        self.status.config(text=f"{len(self.tracks)} faixa(s) encontrada(s). Selecione uma para carregar a letra.")
        if self.tracks:
            self.result_tree.selection_set("0"); self.result_tree.focus("0"); self._update_selected_label(self.tracks[0])

    def select_track(self,event=None):
        sel=self.result_tree.selection()
        if sel and int(sel[0])<len(self.tracks): self._update_selected_label(self.tracks[int(sel[0])])

    def _update_selected_label(self,t):
        self.current_track=t; self.song_label.config(text=f'{t["title"]}  —  {t["artist"]}')

    def load_selected(self):
        if not self.current_track: self.select_track()
        if not self.current_track:
            messagebox.showinfo(APP_NAME,"Pesquise e selecione uma música primeiro."); return
        t=self.current_track; self.status.config(text="Procurando letra com marcações de tempo…")
        threading.Thread(target=self._lyrics_worker,args=(t,),daemon=True).start()

    def _lyrics_worker(self,t):
        try:
            r=requests.get(LRCLIB_SEARCH,params={"track_name":t["title"],"artist_name":t["artist"]},timeout=15); r.raise_for_status()
            results=r.json(); results.sort(key=lambda x:0 if x.get("syncedLyrics") else 1)
            chosen=next((x for x in results if x.get("syncedLyrics")),None)
            if not chosen: chosen=next((x for x in results if x.get("plainLyrics")),None)
            if not chosen: self.root.after(0,lambda:self._display_no_lyrics(t)); return
            synced=chosen.get("syncedLyrics"); plain=chosen.get("plainLyrics") or ""
            lines=self._parse_lrc(synced) if synced else []
            self.root.after(0,lambda:self._display_lyrics(t,lines,plain,bool(synced)))
        except Exception as e:
            self.root.after(0,lambda:self.status.config(text="Falha ao consultar o serviço de letras."))
            self.root.after(0,lambda:messagebox.showerror(APP_NAME,f"Erro ao buscar letras.\n\n{e}"))

    def _parse_lrc(self,content):
        out=[]
        for raw in content.splitlines():
            stamps=re.findall(r"\[(\d{1,2}):(\d{2}(?:\.\d{1,3})?)\]",raw); lyric=re.sub(r"\[[^\]]+\]","",raw).strip()
            for mm,ss in stamps:
                try: out.append((int(mm)*60+float(ss),lyric))
                except ValueError: pass
        return sorted(out,key=lambda x:x[0])

    def _display_no_lyrics(self,t):
        self.lyrics.delete("1.0","end"); self.lyric_lines=[]
        self.lyrics.insert("end","Ainda não encontramos essa letra.\n\nTente outro resultado ou abra um áudio do computador.\nA sincronização automática depende de uma letra com marcações de tempo disponíveis.","normal")
        self.status.config(text="Nenhuma letra encontrada para esta faixa.")

    def _display_lyrics(self,t,lines,plain,synced):
        self.lyrics.delete("1.0","end"); self.current_line=-1
        if synced and lines:
            self.lyric_lines=lines
            for _,line in lines: self.lyrics.insert("end",(line or "♪")+"\n","normal")
            self.status.config(text=f"Letra sincronizada carregada • {len(lines)} linhas")
        else:
            self.lyric_lines=[]
            self.lyrics.insert("end",plain or "A letra não possui conteúdo de texto.","normal")
            self.status.config(text="Letra sem timestamps: a sincronização automática não está disponível.")
        self.lyrics.see("1.0")

    def open_audio(self):
        path=filedialog.askopenfilename(title="Escolher áudio",filetypes=[("Áudio","*.mp3 *.wav *.ogg *.flac"),("Todos os arquivos","*.*")])
        if not path:return
        self.audio_path=path; self.preview_url=None; self.status.config(text=f"Áudio local: {os.path.basename(path)}")
        if self.current_track:self.load_selected()

    def toggle_play(self):
        if not pygame:
            messagebox.showerror(APP_NAME,"O player precisa da biblioteca pygame."); return
        try:
            if pygame.mixer.get_init() is None: pygame.mixer.init()
            if pygame.mixer.music.get_busy() and self.playing:
                pygame.mixer.music.pause(); self.playing=False; self.play_btn.config(text="▶  Reproduzir"); return
            if self.audio_path: pygame.mixer.music.unpause() if self.playing else pygame.mixer.music.load(self.audio_path)
            elif self.current_track and self.current_track.get("preview"):
                if not self.preview_url:
                    self.status.config(text="Preparando prévia do catálogo…"); threading.Thread(target=self._download_preview,daemon=True).start(); return
                pygame.mixer.music.load(self.preview_url)
            else:
                messagebox.showinfo(APP_NAME,"Escolha uma faixa com prévia disponível ou abra um áudio do computador."); return
            pygame.mixer.music.play(); self.playing=True; self.play_btn.config(text="Ⅱ  Pausar")
        except Exception as e: messagebox.showerror(APP_NAME,f"Não foi possível reproduzir o áudio.\n\n{e}")

    def _download_preview(self):
        try:
            url=self.current_track.get("preview"); r=requests.get(url,timeout=25); r.raise_for_status()
            path=os.path.join(tempfile.gettempdir(),"sincroniza_music_preview.mp3")
            with open(path,"wb") as f:f.write(r.content)
            self.preview_url=path; self.root.after(0,self.toggle_play)
        except Exception as e:self.root.after(0,lambda:messagebox.showerror(APP_NAME,f"Falha ao obter prévia.\n\n{e}"))

    def _tick(self):
        try:
            if pygame and pygame.mixer.get_init() and self.lyric_lines:
                pos=max(0,pygame.mixer.music.get_pos()/1000.0); active=-1
                for i,(stamp,_) in enumerate(self.lyric_lines):
                    if stamp<=pos:active=i
                    else:break
                if active!=self.current_line and active>=0:
                    self.current_line=active; self.lyrics.tag_remove("active","1.0","end")
                    self.lyrics.tag_remove("normal","1.0","end")
                    for i in range(len(self.lyric_lines)): self.lyrics.tag_add("future",f"{i+1}.0",f"{i+1}.end")
                    self.lyrics.tag_add("active",f"{active+1}.0",f"{active+1}.end")
                    self.lyrics.see(f"{active+1}.0")
                if pygame.mixer.music.get_busy():
                    dur=max(1,(self.current_track or {}).get("duration",30)); self.progress["value"]=min(100,pos/dur*100)
                else:
                    self.playing=False; self.play_btn.config(text="▶  Reproduzir")
        except Exception:pass
        self.root.after(180,self._tick)

    def open_settings(self):
        win=tk.Toplevel(self.root); win.title("Personalizar aparência"); win.geometry("480x470"); win.resizable(False,False)
        win.configure(bg=self._c("bg")); win.transient(self.root)
        self._label(win,"Seu espaço, seu estilo",19,bold=True,bg=self._c("bg")).pack(anchor="w",padx=24,pady=(22,3))
        self._label(win,"Personalize a aparência do Sincroniza Music.",10,color=self._c("muted"),bg=self._c("bg")).pack(anchor="w",padx=24,pady=(0,18))
        card=tk.Frame(win,bg=self._c("panel"),padx=18,pady=16); card.pack(fill="x",padx=20)
        self._label(card,"TEMA",9,color=self._c("muted"),bold=True).pack(anchor="w")
        row=tk.Frame(card,bg=self._c("panel")); row.pack(fill="x",pady=(8,16))
        self._button(row,"☾  Escuro",lambda:self.change_mode("dark",win)).pack(side="left",expand=True,fill="x",padx=(0,6))
        self._button(row,"☼  Claro",lambda:self.change_mode("light",win)).pack(side="left",expand=True,fill="x",padx=(6,0))
        self._label(card,"COR DE DESTAQUE",9,color=self._c("muted"),bold=True).pack(anchor="w")
        self._button(card,"▰  Escolher cor",lambda:self.choose_accent(win)).pack(anchor="w",pady=(8,16))
        self._label(card,"PAPEL DE PAREDE",9,color=self._c("muted"),bold=True).pack(anchor="w")
        self._button(card,"▧  Enviar imagem do computador",lambda:self.choose_wallpaper(win)).pack(anchor="w",pady=(8,6))
        self._button(win,"Restaurar aparência padrão",lambda:self.reset_appearance(win)).pack(anchor="w",padx=24,pady=16)
        self._label(win,"As preferências são salvas neste computador.",9,color=self._c("muted"),bg=self._c("bg")).pack(anchor="w",padx=24)

    def change_mode(self,mode,win=None):
        self.settings["mode"]=mode; self.colors=THEMES[mode]; self._save_settings()
        # Rebuild the interface with the new palette, preserving current search results and selection.
        old_tracks=self.tracks; old_current=self.current_track; old_lines=self.lyric_lines[:]
        self.shell.destroy(); self._build_ui(); self.tracks=old_tracks; self.current_track=old_current; self.lyric_lines=old_lines
        self._apply_wallpaper()
        if old_tracks:
            self._show_results()
            if old_current:
                try:
                    i=old_tracks.index(old_current); self.result_tree.selection_set(str(i)); self._update_selected_label(old_current)
                except Exception:pass
        if old_lines:self._display_lyrics(old_current,old_lines,"",True)
        if win and win.winfo_exists():win.destroy()

    def choose_accent(self,win=None):
        color=colorchooser.askcolor(color=self.settings["accent"],title="Escolher cor de destaque")[1]
        if color:
            self.settings["accent"]=color; self._save_settings(); self.change_mode(self.settings["mode"],win)

    def choose_wallpaper(self,win=None):
        path=filedialog.askopenfilename(title="Escolher papel de parede",filetypes=[("Imagens","*.png *.jpg *.jpeg *.webp *.bmp")])
        if path:
            if Image is None:
                messagebox.showerror(APP_NAME,"Instale Pillow para usar imagens como papel de parede.");return
            self.settings["wallpaper"]=path;self._save_settings();self._apply_wallpaper()
            if win and win.winfo_exists():win.destroy()

    def reset_appearance(self,win=None):
        self.settings=DEFAULTS.copy();self._save_settings();self.change_mode("dark",win)

    def _apply_wallpaper(self):
        path=self.settings.get("wallpaper")
        if not path or not os.path.isfile(path) or Image is None:return
        try:
            im=Image.open(path).convert("RGB")
            w=max(1,self.root.winfo_width());h=max(1,self.root.winfo_height())
            im.thumbnail((w,h)); im=im.filter(ImageFilter.GaussianBlur(3))
            overlay=Image.new("RGB",im.size,self._c("bg"))
            im=Image.blend(im,overlay,0.48)
            self.wallpaper_image=ImageTk.PhotoImage(im)
            if hasattr(self,"wallpaper_label"):self.wallpaper_label.destroy()
            self.wallpaper_label=tk.Label(self.shell,image=self.wallpaper_image,borderwidth=0)
            self.wallpaper_label.place(x=0,y=0,relwidth=1,relheight=1)
            self.wallpaper_label.lower()
            self.shell.tkraise()
        except Exception:pass

    def show_thanks(self):
        win=tk.Toplevel(self.root);win.title("Obrigado por testar");win.geometry("520x500");win.resizable(False,False)
        win.configure(bg=self._c("bg"));win.transient(self.root)
        self._label(win,"✦",32,color=self.settings["accent"],bold=True,bg=self._c("bg")).pack(pady=(22,0))
        self._label(win,"Obrigado por testar!",22,bold=True,bg=self._c("bg")).pack(pady=(2,8))
        self._label(win,"SINCRONIZA MUSIC  •  VERSÃO EM DESENVOLVIMENTO",8,color=self.settings["accent"],bold=True,bg=self._c("bg")).pack()
        card=tk.Frame(win,bg=self._c("panel"),padx=24,pady=20);card.pack(fill="x",padx=24,pady=22)
        msg=("Este projeto está em evolução. Obrigado por experimentar, descobrir os detalhes e ajudar a melhorar a experiência.\\n\\n"
             "Encontrou um erro ou tem uma ideia? Sua opinião ajuda o projeto a crescer.")
        self._label(card,msg,11,color=self._c("text"),wraplength=420,justify="center").pack(pady=(0,18))
        self._label(card,"CRIADO COM CARINHO POR",8,color=self._c("muted"),bold=True).pack()
        self._label(card,"Dri GT3",19,color=self.settings["accent"],bold=True).pack(pady=(2,12))
        for label,url in SOCIALS:
            self._button(card,label,lambda u=url:webbrowser.open(u)).pack(fill="x",pady=4)
        self._button(win,"Voltar para o aplicativo",win.destroy,primary=True).pack(pady=(0,18))

    def on_close(self):
        try:
            if pygame:pygame.mixer.music.stop();pygame.mixer.quit()
        except Exception:pass
        self.root.destroy()

def main():
    root=tk.Tk();app=SyncMusicApp(root);root.protocol("WM_DELETE_WINDOW",app.on_close);root.mainloop()

if __name__=="__main__":main()
