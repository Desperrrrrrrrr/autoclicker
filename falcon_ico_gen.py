from PIL import Image, ImageDraw, ImageFont

# Размер иконки
size = (256, 256)
img = Image.new('RGBA', size, (255, 255, 255, 0))

# Используем стандартный emoji-шрифт Windows
try:
    font = ImageFont.truetype('seguiemj.ttf', 200)
except OSError:
    font = ImageFont.load_default()

# Рисуем эмодзи по центру
draw = ImageDraw.Draw(img)
text = '🦅'
bbox = draw.textbbox((0, 0), text, font=font)
w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
draw.text(((size[0]-w)//2, (size[1]-h)//2), text, font=font, fill=(0,0,0,255))

# Сохраняем как .ico
img.save('falcon.ico', format='ICO')
print('falcon.ico создан!') 