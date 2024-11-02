from PIL import Image, ImageDraw

# 创建一个新的RGBA图像（支持透明度）
size = 40
image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(image)

# 绘制主体球形
draw.ellipse([2, 2, size-2, size-2], fill=(255, 64, 129))  # 粉色填充

# 绘制高光
draw.ellipse([8, 8, 20, 20], fill=(255, 128, 171, 204))  # 浅粉色，半透明
draw.ellipse([6, 6, 14, 14], fill=(255, 255, 255, 230))  # 白色高光，半透明

# 保存图片
image.save('images/ball.png') 