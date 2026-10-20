"""Build an edited narrated screen walkthrough from actual app captures.
Requires ffmpeg with flite, ffprobe, Pillow; optional artifact tooling only.
"""
from pathlib import Path
import subprocess,json,textwrap
from PIL import Image,ImageDraw,ImageFont
from demo_content import SCENES
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs';TEMP=ROOT/'video_build';TEMP.mkdir(exist_ok=True)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',26)
small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',19)
chapters=[];time=0;script=['# GlucoTwin: narrated screen walkthrough\n\nEdited captures from the running app. Synthetic speech. Pauses allow screen inspection. All data synthetic.\n']
for i,(title,frame,action,narration) in enumerate(SCENES,1):
    image=Image.open(D/'demo_frames'/f'{frame}.png').convert('RGB')
    # Reserve a title bar and caption panel without cropping the actual app.
    canvas=Image.new('RGB',(1600,1200),'#102f42');image.thumbnail((1440,1000));canvas.paste(image,((1600-image.width)//2,76))
    draw=ImageDraw.Draw(canvas);draw.text((80,22),f'{i:02d} / {len(SCENES)}    {title}',font=font,fill='white')
    draw.text((80,1090),action,font=font,fill='#92ded5')
    draw.text((80,1145),'EDITED APP CAPTURES  |  SYNTHESIZED NARRATION  |  ALL PATIENT DATA SYNTHETIC',font=small,fill='#c6d8e1')
    png=TEMP/f'{i:02d}.png';canvas.save(png)
    txt=TEMP/f'{i:02d}.txt';txt.write_text(narration)
    wav=TEMP/f'{i:02d}.wav'
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi','-i',f'flite=textfile={txt}:voice=slt','-af','atempo=0.88','-ar','24000',str(wav)],check=True)
    duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(wav)]))
    total=max(60,int(duration)+5)
    mp4=TEMP/f'{i:02d}.mp4'
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-loop','1','-framerate','1','-i',str(png),'-i',str(wav),'-t',str(total),'-vf','format=yuv420p','-c:v','libx264','-preset','ultrafast','-tune','stillimage','-r','2','-c:a','aac','-b:a','64k','-af','apad',str(mp4)],check=True)
    chapters.append(dict(title=title,start_seconds=time,duration_seconds=total));script.append(f'## {time//60:02d}:{time%60:02d} - {title}\n\n**Screen action:** {action}\n\n{narration}\n\nPause to inspect the displayed evidence before continuing.\n');time+=total
    print(f'Chapter {i}/{len(SCENES)} rendered ({total}s)',flush=True)
concat=TEMP/'concat.txt';concat.write_text(''.join(f"file '{TEMP/f'{i:02d}.mp4'}'\n" for i in range(1,len(SCENES)+1)))
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy','-movflags','+faststart',str(D/'GLUCOTWIN_DEMO.mp4')],check=True)
(D/'DEMO_SCRIPT.md').write_text('\n'.join(script));(D/'DEMO_CHAPTERS.json').write_text(json.dumps(dict(duration_seconds=time,chapters=chapters),indent=2))
print('Total walkthrough duration:',time)
