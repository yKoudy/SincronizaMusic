import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading, requests, os, re, time
try:
    import pygame
except Exception:
    pygame = None

APP_NAME = "Sincroniza Music"
ITUNES_SEARCH = "https://itunes.apple.com/search"
LRCLIB_SEARCH = "https://lrclib.net/api/search"
LRCLIB_GET = "https://lrclib.net/api/get"

BG = "#10131c"
PANEL = "#191e2b"
ACCENT = "#8b5cf6"
TEXT = "#f4f4f5"
MUTED = "#a1a1aa"

class SyncMusicApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1100x720")
        self.root.minsize(850, 580)
        self.root.configure(bg=BG)
        self.tracks = []
        self.current_track = None
        self.lyric_lines = []
        self.audio_path = None
        self.playing = False
        self.preview_url = None
        self.current_line = -1
        self._build_ui()
        if pygame:
            try:
                pygame.mixer.init()
            except Exception:
                pass
        self.root.after(150, self._tick)

    def _build_ui(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TEntry", padding=9)
        style.configure("TButton", padding=8, font=("Segoe UI", 10))
        style.configure("Treeview", rowheight=31, font=("Segoe UI", 10),
                        background=PANEL, foreground=TEXT, fieldbackground=PANEL)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        top = tk.Frame(self.root, bg=BG, padx=22, pady=18)
        top.pack(fill="x")
        tk.Label(top, text="♪  SINCRONIZA MUSIC", bg=BG, fg=TEXT,
                 font=("Segoe UI", 21, "bold")).pack(anchor="w")
        tk.Label(top, text="Pesquise uma música. O app busca letras sincronizadas e acompanha o áudio.",
                 bg=BG, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(3, 14))
        searchrow = tk.Frame(top, bg=BG)
        searchrow.pack(fill="x")
        self.query = tk.StringVar()
        entry = tk.Entry(searchrow, textvariable=self.query, font=("Segoe UI", 12),
                         bg=PANEL, fg=TEXT, insertbackground=TEXT, relief="flat")
        entry.pack(side="left", fill="x", expand=True, ipady=10, padx=(0, 8))
        entry.bind("<Return>", lambda e: self.search())
        tk.Button(searchrow, text="Pesquisar música", command=self.search, bg=ACCENT,
                  fg="white", activebackground="#7c3aed", activeforeground="white",
                  relief="flat", padx=16, pady=10).pack(side="left")
        tk.Button(searchrow, text="Abrir áudio do PC", command=self.open_audio,
                  bg="#30384b", fg=TEXT, relief="flat", padx=14, pady=10).pack(side="left", padx=(8,0))

        body = tk.Frame(self.root, bg=BG, padx=22)
        body.pack(fill="both", expand=True)
        left = tk.Frame(body, bg=PANEL, width=390)
        left.pack(side="left", fill="y", padx=(0, 14))
        left.pack_propagate(False)
        tk.Label(left, text="RESULTADOS", bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=14, pady=(14, 8))
        cols = ("title", "artist")
        self.result_tree = ttk.Treeview(left, columns=cols, show="headings", selectmode="browse")
        self.result_tree.heading("title", text="Música")
        self.result_tree.heading("artist", text="Artista")
        self.result_tree.column("title", width=210)
        self.result_tree.column("artist", width=140)
        self.result_tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.result_tree.bind("<<TreeviewSelect>>", self.select_track)
        self.result_tree.bind("<Double-1>", lambda e: self.load_selected())

        right = tk.Frame(body, bg=PANEL)
        right.pack(side="left", fill="both", expand=True)
        self.song_label = tk.Label(right, text="Escolha uma música", bg=PANEL, fg=TEXT,
                                   font=("Segoe UI", 16, "bold"), wraplength=560)
        self.song_label.pack(anchor="w", padx=20, pady=(17, 3))
        self.status = tk.Label(right, text="Pronto para pesquisar", bg=PANEL, fg=MUTED,
                               font=("Segoe UI", 9))
        self.status.pack(anchor="w", padx=20, pady=(0, 12))
        self.lyrics = tk.Text(right, bg="#131722", fg="#d4d4d8", insertbackground=TEXT,
                              font=("Segoe UI", 15), relief="flat", wrap="word",
                              padx=18, pady=16, spacing1=7, spacing3=7)
        self.lyrics.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        self.lyrics.tag_configure("active", foreground="#ffffff", background="#6d28d9",
                                  font=("Segoe UI", 16, "bold"), lmargin1=8, lmargin2=8)
        self.lyrics.tag_configure("normal", foreground="#a1a1aa")
        controls = tk.Frame(right, bg=PANEL)
        controls.pack(fill="x", padx=14, pady=(0, 14))
        self.play_btn = tk.Button(controls, text="▶  Reproduzir", command=self.toggle_play,
                                  bg=ACCENT, fg="white", relief="flat", padx=14, pady=9)
        self.play_btn.pack(side="left")
        tk.Button(controls, text="Buscar letra sincronizada", command=self.load_selected,
                  bg="#30384b", fg=TEXT, relief="flat", padx=12, pady=9).pack(side="left", padx=8)
        tk.Label(controls, text="Créditos: Dri GT3", bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 9)).pack(side="right")
        self.progress = ttk.Progressbar(right, mode="determinate", maximum=100)
        self.progress.pack(fill="x", padx=14, pady=(0, 14))

    def set_status(self, text):
        self.root.after(0, lambda: self.status.config(text=text))

    def search(self):
        q = self.query.get().strip()
        if not q:
            messagebox.showinfo(APP_NAME, "Digite o nome da música ou artista.")
            return
        self.status.config(text="Pesquisando catálogo…")
        threading.Thread(target=self._search_worker, args=(q,), daemon=True).start()

    def _search_worker(self, q):
        try:
            r = requests.get(ITUNES_SEARCH, params={"term": q, "entity": "song", "limit": 35}, timeout=12)
            r.raise_for_status()
            items = r.json().get("results", [])
            self.tracks = [{
                "title": x.get("trackName", "Título desconhecido"),
                "artist": x.get("artistName", "Artista desconhecido"),
                "album": x.get("collectionName", ""),
                "duration": x.get("trackTimeMillis", 0) / 1000,
                "preview": x.get("previewUrl"),
                "url": x.get("trackViewUrl"),
            } for x in items]
            self.root.after(0, self._show_results)
        except Exception as e:
            self.set_status("Falha na pesquisa. Verifique a conexão e tente novamente.")
            self.root.after(0, lambda: messagebox.showerror(APP_NAME, f"Não foi possível pesquisar músicas.\n\n{e}"))

    def _show_results(self):
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        for i, t in enumerate(self.tracks):
            self.result_tree.insert("", "end", iid=str(i), values=(t["title"], t["artist"]))
        self.status.config(text=f"{len(self.tracks)} resultado(s). Selecione uma música e carregue a letra.")
        if self.tracks:
            self.result_tree.selection_set("0")
            self.result_tree.focus("0")
            self._update_selected_label(self.tracks[0])

    def select_track(self, event=None):
        selection = self.result_tree.selection()
        if selection:
            idx = int(selection[0])
            if idx < len(self.tracks):
                self.current_track = self.tracks[idx]
                self._update_selected_label(self.current_track)

    def _update_selected_label(self, track):
        self.song_label.config(text=f'{track["title"]} — {track["artist"]}')
        self.current_track = track

    def load_selected(self):
        if not self.current_track:
            self.select_track()
        if not self.current_track:
            messagebox.showinfo(APP_NAME, "Pesquise e selecione uma música primeiro.")
            return
        t = self.current_track
        self.status.config(text="Procurando letra com marcações de tempo…")
        threading.Thread(target=self._lyrics_worker, args=(t,), daemon=True).start()

    def _lyrics_worker(self, track):
        try:
            params = {"track_name": track["title"], "artist_name": track["artist"]}
            r = requests.get(LRCLIB_SEARCH, params=params, timeout=12)
            r.raise_for_status()
            results = r.json()
            # Prefer synced lyrics. Try exact title/artist candidates first.
            results.sort(key=lambda x: 0 if x.get("syncedLyrics") else 1)
            chosen = next((x for x in results if x.get("syncedLyrics")), None)
            if not chosen:
                chosen = next((x for x in results if x.get("plainLyrics")), None)
            if not chosen:
                self.root.after(0, lambda: self._display_no_lyrics(track))
                return
            synced = chosen.get("syncedLyrics")
            plain = chosen.get("plainLyrics") or ""
            lines = self._parse_lrc(synced) if synced else []
            self.root.after(0, lambda: self._display_lyrics(track, lines, plain, bool(synced)))
        except Exception as e:
            self.root.after(0, lambda: self.status.config(text="Não foi possível consultar o serviço de letras."))
            self.root.after(0, lambda: messagebox.showerror(APP_NAME, f"Erro ao buscar letra sincronizada.\n\n{e}"))

    def _parse_lrc(self, content):
        lines = []
        for raw in content.splitlines():
            matches = re.findall(r"\[(\d{1,2}):(\d{2}(?:\.\d{1,3})?)\]", raw)
            lyric = re.sub(r"\[[^\]]+\]", "", raw).strip()
            for mm, ss in matches:
                try:
                    lines.append((int(mm) * 60 + float(ss), lyric))
                except ValueError:
                    pass
        lines.sort(key=lambda x: x[0])
        return lines

    def _display_no_lyrics(self, track):
        self.lyrics.delete("1.0", "end")
        self.lyric_lines = []
        self.status.config(text="Nenhuma letra encontrada para esta faixa.")
        self.lyrics.insert("end", "Não encontrei letra para esta música no serviço consultado.\n\n"
                          "Tente pesquisar pelo título + artista ou carregar outra faixa.\n"
                          "A sincronização automática depende de existir uma letra com timestamps no catálogo.")

    def _display_lyrics(self, track, lines, plain, synced):
        self.lyrics.delete("1.0", "end")
        self.lyric_lines = lines
        self.current_line = -1
        if synced and lines:
            for _, line in lines:
                self.lyrics.insert("end", (line or "♪") + "\n", "normal")
            self.status.config(text=f"Letra sincronizada carregada ({len(lines)} linhas). Reproduza o preview ou abra o áudio completo.")
        else:
            self.lyric_lines = []
            self.lyrics.insert("end", plain or "A letra não possui conteúdo de texto.")
            self.status.config(text="Letra encontrada, mas sem timestamps: não é possível sincronizar automaticamente.")
        self.lyrics.see("1.0")

    def open_audio(self):
        path = filedialog.askopenfilename(title="Escolher arquivo de áudio",
            filetypes=[("Arquivos de áudio", "*.mp3 *.wav *.ogg *.flac"), ("Todos os arquivos", "*.*")])
        if not path:
            return
        self.audio_path = path
        self.preview_url = None
        self.status.config(text=f"Áudio local: {os.path.basename(path)}")
        if self.current_track:
            self.load_selected()

    def toggle_play(self):
        if not pygame:
            messagebox.showerror(APP_NAME, "O player precisa da biblioteca pygame. Execute instalar.bat.")
            return
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()
                self.playing = False
                self.play_btn.config(text="▶  Reproduzir")
                return
            if self.audio_path:
                pygame.mixer.music.load(self.audio_path)
            elif self.current_track and self.current_track.get("preview"):
                if not self.preview_url:
                    self.status.config(text="Baixando prévia autorizada do catálogo…")
                    threading.Thread(target=self._download_preview, daemon=True).start()
                    return
                pygame.mixer.music.load(self.preview_url)
            else:
                messagebox.showinfo(APP_NAME, "Selecione uma música com prévia disponível ou abra um áudio do PC.")
                return
            pygame.mixer.music.play()
            self.playing = True
            self.play_btn.config(text="Ⅱ  Pausar")
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Não foi possível reproduzir o áudio.\n\n{e}")

    def _download_preview(self):
        try:
            import tempfile
            url = self.current_track.get("preview")
            r = requests.get(url, timeout=25)
            r.raise_for_status()
            path = os.path.join(tempfile.gettempdir(), "sincroniza_music_preview.mp3")
            with open(path, "wb") as f:
                f.write(r.content)
            self.preview_url = path
            self.root.after(0, self.toggle_play)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(APP_NAME, f"Falha ao obter a prévia.\n\n{e}"))

    def _tick(self):
        try:
            if pygame and pygame.mixer.get_init() and self.lyric_lines:
                pos = pygame.mixer.music.get_pos() / 1000.0
                # get_pos is relative to the current play segment; adequate for normal playback.
                active = -1
                for i, (stamp, _) in enumerate(self.lyric_lines):
                    if stamp <= pos:
                        active = i
                    else:
                        break
                if active != self.current_line and active >= 0:
                    self.current_line = active
                    self.lyrics.tag_remove("active", "1.0", "end")
                    line_no = active + 1
                    self.lyrics.tag_add("active", f"{line_no}.0", f"{line_no}.end")
                    self.lyrics.see(f"{line_no}.0")
                if pygame.mixer.music.get_busy():
                    self.playing = True
                    self.progress["value"] = min(100, pos / max(1, (self.current_track or {}).get("duration", 30)) * 100)
                else:
                    self.playing = False
                    self.play_btn.config(text="▶  Reproduzir")
        except Exception:
            pass
        self.root.after(150, self._tick)

    def on_close(self):
        try:
            if pygame:
                pygame.mixer.music.stop()
                pygame.mixer.quit()
        except Exception:
            pass
        self.root.destroy()

def main():
    root = tk.Tk()
    app = SyncMusicApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()

if __name__ == "__main__":
    main()
