# Sincroniza Music

Aplicativo desktop para Windows, com interface em português, pesquisa de faixas e letras sincronizadas.

**Créditos do projeto:** Dri GT3  
**Tecnologias:** Python 3.11+, Tkinter, Requests, Pygame  
**Fontes online:** Apple iTunes Search API (catálogo e prévias) e LRCLIB (letras e timestamps).

## Como instalar
1. Instale Python 3.11 ou superior em https://www.python.org/downloads/ e marque **Add Python to PATH**.
2. Extraia a pasta do ZIP para um local no computador.
3. Dê dois cliques em `instalar.bat`.
4. Depois, dê dois cliques em `iniciar.bat`.

## Como usar
1. Digite nome da música ou artista e clique em **Pesquisar música**.
2. Selecione uma faixa na lista.
3. Clique em **Buscar letra sincronizada**.
4. Clique em **Reproduzir** para tocar a prévia disponível; ou em **Abrir áudio do PC** para escolher um arquivo local.
5. Se houver letra com timestamps no LRCLIB, a linha atual acompanha o tempo do player.

## Criar executável
No Windows com Python instalado, execute `criar_exe.bat`. O executável será criado em `dist\Sincroniza Music\Sincroniza Music.exe`. Para distribuição, mantenha os arquivos da pasta de saída juntos.

## Limitações importantes
- A sincronização real depende de encontrar uma versão **com timestamps** (campo `syncedLyrics`) para a gravação certa. Se o catálogo só tiver letra sem tempos, o app informa isso em vez de fingir sincronização.
- A busca de músicas usa o catálogo público do iTunes; a prévia pode ser curta (normalmente cerca de 30 segundos) e nem todas as faixas têm prévia.
- Para tocar a música completa, abra um arquivo de áudio local que você tenha direito de usar. O app não baixa músicas completas de serviços de streaming.
- A disponibilidade dos serviços externos pode mudar; é necessária conexão com a internet para pesquisar.
- Projeto não oficial, sem vínculo com Apple ou LRCLIB.

## Gerar EXE automaticamente no Windows (sem executar scripts localmente)
O projeto inclui `.github/workflows/build-windows.yml`. Se você enviar a pasta do projeto para um repositório GitHub, abra **Actions → Build Windows EXE → Run workflow**. Ao terminar, baixe o artefato `Sincroniza-Music-Windows` na execução. O ZIP contém o executável e os arquivos que ele precisa. O GitHub exige uma conta e que você crie/envie o repositório; este projeto não pode criar isso na sua conta sem autorização.
