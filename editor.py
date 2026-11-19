from atualizador import verificar as verificar_atualizacoes
import os, sys, json, subprocess, threading, queue, tempfile, shutil, urllib.request, tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

ROOT=Path(__file__).resolve().parent
class Editor:
 def __init__(self,root):
  self.root=root;root.title('JAPA FF EDITOR 7.0 | IA LOCAL');root.geometry('1080x730');root.configure(bg='#151820')
  self.video='';self.music='';self.duration=0;self.segments=[];self.q=queue.Queue();self.image=None;self.preview_id=0;self.busy=False
  self.ffmpeg=shutil.which('ffmpeg');self.ffprobe=shutil.which('ffprobe')
  top=tk.Frame(root,bg='#151820');top.pack(fill='x',padx=12,pady=8)
  tk.Label(top,text='JAPA FF EDITOR 7.0',font=('Segoe UI',19,'bold'),fg='#e9bd55',bg='#151820').pack(side='left')
  for name,fn in [('Abrir vídeo',self.open_video),('Adicionar música',self.open_music),('Detectar cenas',self.detect_scenes),('Legendas IA',self.subtitles),('Ollama',self.ollama),('Exportar',self.export),('Atualizações',verificar_atualizacoes)]:
   tk.Button(top,text=name,command=fn,bg='#d3a43b',fg='black',relief='flat',padx=9).pack(side='left',padx=4)
  body=tk.PanedWindow(root,orient='horizontal',bg='#151820',sashwidth=6);body.pack(fill='both',expand=True,padx=12)
  left=tk.Frame(body,bg='#202633');body.add(left,width=690)
  self.canvas=tk.Label(left,text='Abra um vídeo para ver a prévia',bg='#080a10',fg='white',font=('Segoe UI',14));self.canvas.pack(fill='both',expand=True,padx=8,pady=8)
  controls=tk.Frame(left,bg='#202633');controls.pack(fill='x',padx=8,pady=4)
  tk.Button(controls,text='◀ -5 s',command=lambda:self.seek(-5)).pack(side='left')
  tk.Button(controls,text='+5 s ▶',command=lambda:self.seek(5)).pack(side='left')
  self.pos=tk.DoubleVar(value=0);self.slider=ttk.Scale(controls,from_=0,to=1,variable=self.pos,command=self.on_seek);self.slider.pack(side='left',fill='x',expand=True,padx=10)
  self.time=tk.Label(controls,text='00:00 / 00:00',fg='white',bg='#202633');self.time.pack(side='right')
  opts=tk.Frame(left,bg='#202633');opts.pack(fill='x',padx=8,pady=6)
  tk.Label(opts,text='Formato',bg='#202633',fg='white').pack(side='left')
  self.format=tk.StringVar(value='Short vertical 9:16');ttk.Combobox(opts,textvariable=self.format,values=['Short vertical 9:16','YouTube horizontal 16:9'],state='readonly',width=23).pack(side='left',padx=5)
  self.quality=tk.BooleanVar(value=True);tk.Checkbutton(opts,text='Melhorar nitidez e cores',variable=self.quality,bg='#202633',fg='white',selectcolor='#202633').pack(side='left')
  self.captions=tk.BooleanVar(value=False);tk.Checkbutton(opts,text='Incluir legendas SRT',variable=self.captions,bg='#202633',fg='white',selectcolor='#202633').pack(side='left')
  right=tk.Frame(body,bg='#202633');body.add(right,width=340)
  tk.Label(right,text='TRECHOS (revise antes de exportar)',bg='#202633',fg='#e9bd55',font=('Segoe UI',11,'bold')).pack(pady=10)
  self.listbox=tk.Listbox(right,bg='#121723',fg='white',selectbackground='#8c6b28',height=19);self.listbox.pack(fill='both',expand=True,padx=9)
  self.listbox.bind('<<ListboxSelect>>',self.pick)
  actions=tk.Frame(right,bg='#202633');actions.pack(pady=8)
  for name,fn in [('Marcar capa',self.mark_capa),('Marcar morte',self.mark_death),('Excluir trecho',self.delete_segment)]:tk.Button(actions,text=name,command=fn).pack(side='left',padx=2)
  add=tk.Frame(right,bg='#202633');add.pack(pady=5)
  tk.Label(add,text='Início (s)',fg='white',bg='#202633').pack(side='left');self.start=tk.Entry(add,width=7);self.start.pack(side='left',padx=2)
  tk.Label(add,text='Fim (s)',fg='white',bg='#202633').pack(side='left');self.end=tk.Entry(add,width=7);self.end.pack(side='left',padx=2)
  tk.Button(right,text='Adicionar trecho manual',command=self.add_segment).pack(pady=5)
  tk.Label(right,text='Detecção automática = mudanças de cena.\nCapas/mortes precisam de confirmação manual.',fg='#c6cad4',bg='#202633',justify='center').pack(pady=8)
  self.status=tk.StringVar(value='Pronto. Instale FFmpeg e abra um vídeo.');tk.Label(root,textvariable=self.status,anchor='w',bg='#10131a',fg='#e9bd55').pack(fill='x',padx=12,pady=7)
  self.root.after(100,self.poll)
 def poll(self):
  try:
   while True:
    fn,args=self.q.get_nowait();fn(*args)
  except queue.Empty:pass
  self.root.after(100,self.poll)
 def ui(self,fn,*args):self.q.put((fn,args))
 def run_bg(self,fn):
  if self.busy:return messagebox.showinfo('Aguarde','Outra tarefa está em andamento.')
  self.busy=True
  def wrap():
   try:fn()
   except Exception as e:self.ui(messagebox.showerror,'Erro',str(e))
   finally:self.ui(self.done)
  threading.Thread(target=wrap,daemon=True).start()
 def done(self):self.busy=False
 def check(self):
  if not self.ffmpeg or not self.ffprobe:messagebox.showerror('FFmpeg ausente','Instale FFmpeg com INSTALAR_FFMPEG.bat e reinicie o aplicativo.');return False
  return True
 def cmd(self,args):return subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 def open_video(self):
  if not self.check():return
  p=filedialog.askopenfilename(filetypes=[('Vídeos','*.mp4 *.mkv *.mov *.avi *.webm'),('Todos','*.*')]);
  if not p:return
  r=self.cmd([self.ffprobe,'-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',p])
  try:self.duration=float(r.stdout.strip())
  except:messagebox.showerror('Vídeo inválido',r.stderr or 'Não foi possível ler a duração.');return
  self.video=p;self.segments=[];self.refresh();self.slider.configure(to=max(1,self.duration));self.pos.set(0);self.show_frame(0);self.status.set('Vídeo carregado: '+Path(p).name)
 def show_frame(self,t):
  if not self.video:return
  self.preview_id+=1;token=self.preview_id
  def worker():
   with tempfile.TemporaryDirectory() as d:
    p=os.path.join(d,'frame.png')
    r=self.cmd([self.ffmpeg,'-hide_banner','-loglevel','error','-ss',str(max(0,t)),'-i',self.video,'-frames:v','1','-vf','scale=640:360:force_original_aspect_ratio=decrease', '-y',p])
    if r.returncode or not os.path.exists(p):return
    try:
     from PIL import Image,ImageTk
     im=Image.open(p).copy();self.ui(self.set_frame,im,token,t)
    except ImportError:self.ui(self.status.set,'Instale Pillow: INSTALAR.bat')
  threading.Thread(target=worker,daemon=True).start()
 def set_frame(self,im,token,t):
  if token!=self.preview_id:return
  from PIL import ImageTk
  self.image=ImageTk.PhotoImage(im);self.canvas.configure(image=self.image,text='');self.time.configure(text=f'{int(t//60):02d}:{int(t%60):02d} / {int(self.duration//60):02d}:{int(self.duration%60):02d}')
 def on_seek(self,v):
  if not self.video:return
  if hasattr(self,'seek_job'):self.root.after_cancel(self.seek_job)
  self.seek_job=self.root.after(250,lambda:self.show_frame(float(self.pos.get())))
 def seek(self,dt):self.pos.set(max(0,min(self.duration,self.pos.get()+dt)));self.show_frame(self.pos.get())
 def open_music(self):
  p=filedialog.askopenfilename(filetypes=[('Áudio','*.mp3 *.wav *.m4a *.aac'),('Todos','*.*')]);
  if p:self.music=p;self.status.set('Música: '+Path(p).name)
 def refresh(self):
  self.listbox.delete(0,'end')
  for a,b,label in self.segments:self.listbox.insert('end',f'{a:.1f}s — {b:.1f}s | {label}')
 def add_segment(self):
  try:a=float(self.start.get());b=float(self.end.get());assert 0<=a<b<=self.duration
  except:return messagebox.showerror('Trecho inválido','Digite início e fim em segundos, dentro da duração do vídeo.')
  self.segments.append((a,b,'Revisar'));self.segments.sort();self.refresh()
 def selected(self):
  s=self.listbox.curselection();return s[0] if s else None
 def pick(self,e=None):
  i=self.selected()
  if i is not None:self.pos.set(self.segments[i][0]);self.show_frame(self.segments[i][0])
 def mark(self,label):
  i=self.selected()
  if i is None:return
  a,b,_=self.segments[i];self.segments[i]=(a,b,label);self.refresh();self.listbox.selection_set(i)
 def mark_capa(self):self.mark('CAPA / incluir')
 def mark_death(self):self.mark('MORTE / excluir')
 def delete_segment(self):
  i=self.selected()
  if i is not None:self.segments.pop(i);self.refresh()
 def detect_scenes(self):
  if not self.video:return messagebox.showinfo('Vídeo','Abra um vídeo primeiro.')
  def work():
   self.ui(self.status.set,'Detectando mudanças de cena...')
   r=self.cmd([self.ffmpeg,'-hide_banner','-i',self.video,'-vf',"select='gt(scene,0.38)',showinfo",'-an','-f','null','-'])
   import re
   times=[float(x) for x in re.findall(r'pts_time:([\d.]+)',r.stderr)];times=[t for t in times if 1<t<self.duration-1]
   # Sample up to 40 scene boundaries, each candidate 5 sec long
   items=[]
   for t in times[:40]:
    a=max(0,t-2);b=min(self.duration,t+3)
    if b>a:items.append((a,b,'Cena detectada / revisar'))
   if not items:items=[(a,min(a+8,self.duration),'Trecho / revisar') for a in range(0,int(self.duration),max(8,int(self.duration/15)))][:20]
   self.ui(self.set_segments,items)
  self.run_bg(work)
 def set_segments(self,items):self.segments=items;self.refresh();self.status.set(f'{len(items)} trechos sugeridos. Marque mortes para excluir e capas para manter.')
 def subtitles(self):
  if not self.video:return
  def work():
   self.ui(self.status.set,'Gerando legendas localmente... pode demorar.')
   try:import whisper
   except ImportError:raise RuntimeError('Whisper não instalado. Execute INSTALAR_IA_LEGENDAS.bat.')
   model=whisper.load_model('tiny');result=model.transcribe(self.video,language='pt',fp16=False)
   path=str(Path(self.video).with_suffix('.srt'))
   def fmt(s):
    h=int(s//3600);m=int(s//60)%60;sec=int(s)%60;ms=int((s-int(s))*1000);return f'{h:02}:{m:02}:{sec:02},{ms:03}'
   with open(path,'w',encoding='utf-8') as f:
    for i,x in enumerate(result['segments'],1):f.write(f"{i}\n{fmt(x['start'])} --> {fmt(x['end'])}\n{x['text'].strip()}\n\n")
   self.ui(self.status.set,'Legendas salvas: '+path)
  self.run_bg(work)
 def ollama(self):
  def work():
   self.ui(self.status.set,'Consultando Ollama local...')
   prompt='Você é editor de Free Fire. Dê 3 dicas curtas de edição de highlights e 3 títulos curtos para Shorts em português. Não afirme ter assistido ao vídeo.'
   payload=json.dumps({'model':'gemma3:1b','prompt':prompt,'stream':False}).encode()
   try:
    req=urllib.request.Request('http://127.0.0.1:11434/api/generate',data=payload,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=120) as resp:answer=json.load(resp).get('response','Sem resposta')
   except Exception as e:raise RuntimeError('Ollama não está pronto. Instale Ollama e execute: ollama pull gemma3:1b\n'+str(e))
   self.ui(self.show_ai,answer)
  self.run_bg(work)
 def show_ai(self,answer):
  w=tk.Toplevel(self.root);w.title('Sugestões da IA local');w.geometry('650x450');t=tk.Text(w,wrap='word');t.pack(fill='both',expand=True);t.insert('1.0',answer)
 def export(self):
  if not self.video or not self.check():return
  clips=[(a,b) for a,b,label in self.segments if 'MORTE' not in label]
  if not clips:return messagebox.showwarning('Sem trechos','Adicione ou detecte trechos e marque os que deseja manter.')
  dest=filedialog.asksaveasfilename(defaultextension='.mp4',filetypes=[('MP4','*.mp4')],initialfile='JAPA_FF_SHORT.mp4')
  if not dest:return
  def work():
   self.ui(self.status.set,'Exportando... aguarde.')
   with tempfile.TemporaryDirectory() as td:
    paths=[]
    vertical=self.format.get().startswith('Short')
    if vertical:scale='scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920'
    else:scale='scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2'
    filters=scale+(',eq=contrast=1.06:saturation=1.12,unsharp=3:3:0.5' if self.quality.get() else '')+',setsar=1'
    # Render clips to identical codecs to concatenate safely
    for i,(a,b) in enumerate(clips):
     p=os.path.join(td,f'clip{i:03}.mp4');args=[self.ffmpeg,'-hide_banner','-loglevel','error','-y','-ss',str(a),'-t',str(b-a),'-i',self.video,'-vf',filters,'-r','30','-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-an',p]
     r=self.cmd(args)
     if r.returncode:raise RuntimeError('Erro ao renderizar trecho: '+r.stderr[-1000:])
     paths.append(p)
    concat=os.path.join(td,'concat.txt')
    with open(concat,'w',encoding='utf-8') as f:
     for p in paths:f.write("file '"+p.replace('\\','/')+"'\n")
    joined=os.path.join(td,'joined.mp4');r=self.cmd([self.ffmpeg,'-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',concat,'-c','copy',joined])
    if r.returncode:raise RuntimeError(r.stderr[-1000:])
    # Add original source audio from each segment, when present; music optional instead
    audio=self.music
    if audio:
     args=[self.ffmpeg,'-hide_banner','-loglevel','error','-y','-i',joined,'-stream_loop','-1','-i',audio,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','160k','-shortest']
    else:
     # Build matching audio segments with silence fallback if source has no audio
     aud=[]
     probe=self.cmd([self.ffprobe,'-v','error','-select_streams','a','-show_entries','stream=index','-of','csv=p=0',self.video]);has_audio=bool(probe.stdout.strip())
     for i,(a,b) in enumerate(clips):
      p=os.path.join(td,f'a{i:03}.m4a')
      if has_audio:args=[self.ffmpeg,'-hide_banner','-loglevel','error','-y','-ss',str(a),'-t',str(b-a),'-i',self.video,'-vn','-c:a','aac',p]
      else:args=[self.ffmpeg,'-hide_banner','-loglevel','error','-y','-f','lavfi','-i','anullsrc=r=44100:cl=stereo','-t',str(b-a),'-c:a','aac',p]
      r=self.cmd(args)
      if r.returncode:raise RuntimeError(r.stderr[-1000:])
      aud.append(p)
     alist=os.path.join(td,'audio.txt')
     with open(alist,'w') as f:
      for p in aud:f.write("file '"+p.replace('\\','/')+"'\n")
     aout=os.path.join(td,'audio.m4a');r=self.cmd([self.ffmpeg,'-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',alist,'-c','copy',aout]);
     if r.returncode:raise RuntimeError(r.stderr[-1000:])
     args=[self.ffmpeg,'-hide_banner','-loglevel','error','-y','-i',joined,'-i',aout,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-shortest']
    srt=str(Path(self.video).with_suffix('.srt'))
    if self.captions.get() and os.path.exists(srt):
     # Embed as selectable subtitle track, not burned in
     args+=['-i',srt,'-map','2:s:0','-c:s','mov_text']
    args+=[dest];r=self.cmd(args)
    if r.returncode:raise RuntimeError('Erro ao exportar: '+r.stderr[-1200:])
   self.ui(self.status.set,'Exportado: '+dest);self.ui(messagebox.showinfo,'Exportação concluída','Arquivo salvo em:\n'+dest)
  self.run_bg(work)
if __name__=='__main__':
 root=tk.Tk();Editor(root);root.mainloop()
