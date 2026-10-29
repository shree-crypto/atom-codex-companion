from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent/'review'
if __name__=='__main__':
    sheet=Image.new('RGB',(1800,980),'#f4f2ed'); draw=ImageDraw.Draw(sheet)
    font=ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf',32)
    small=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',24)
    draw.text((55,35),'V1 / ORANGE + BLACK — THREE FACE OPTIONS',font=font,fill='#202a31')
    for i,(name,label) in enumerate((('assembled','A · Classic'),('soft','B · Softer corners'),('slim','C · Slimmer bezel'))):
        picture=Image.open(ROOT/f'iteration-05-{name}-orange.png').convert('RGB')
        picture=picture.crop((100,270,1300,1240)); picture.thumbnail((570,700))
        sheet.paste(picture,(i*600+(600-picture.width)//2,155))
        draw.text((i*600+75,815),label,font=font,fill='#202a31')
    draw.text((55,925),'Same board fit and snap locations · real CAD variants · nominal prototypes',font=small,fill='#66737a')
    output=ROOT/'orange-design-comparison.png'; sheet.save(output); print(output)
