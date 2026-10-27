"""Halloween kids event graphic (1080x1350). Usage: python3 tools/make_halloween.py out.jpg"""
import sys, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H = 1080, 1350
F = lambda k, s: ImageFont.truetype({"b": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "r": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "s": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"}[k], s)
ORANGE=(255,140,26); PURPLE=(40,14,60); YEL=(255,214,64); CREAM=(255,244,225); GREEN=(120,200,70)
img = Image.new("RGB", (W, H), PURPLE).convert("RGBA")
g = Image.new("RGBA", (W, H)); ImageDraw.Draw(g).ellipse((40, 380, W-40, 1180), fill=(255, 120, 20, 110))
img = Image.alpha_composite(img, g.filter(ImageFilter.GaussianBlur(170)))
d = ImageDraw.Draw(img); rnd = random.Random(31)
for _ in range(60):  # stars
    x, y = rnd.randrange(W), rnd.randrange(H); r = rnd.choice([1, 2, 2, 3])
    d.ellipse((x-r, y-r, x+r, y+r), fill=(255, 240, 200, 150))
def bat(cx, cy, s):
    d.polygon([(cx, cy), (cx-60*s, cy-25*s), (cx-45*s, cy), (cx-70*s, cy+5*s), (cx-30*s, cy+12*s), (cx, cy+20*s),
               (cx+30*s, cy+12*s), (cx+70*s, cy+5*s), (cx+45*s, cy), (cx+60*s, cy-25*s)], fill=(15, 5, 25))
    d.ellipse((cx-12*s, cy-12*s, cx+12*s, cy+14*s), fill=(15, 5, 25))
bat(330, 575, 0.7); bat(760, 560, 0.55); bat(540, 1035, 0.5)
def ctext(y, text, font, fill, stroke=0, sc=(30,8,40)):
    w = d.textlength(text, font=font); d.text(((W-w)/2, y), text, font=font, fill=fill, stroke_width=stroke, stroke_fill=sc)
ctext(40, "THAMARA'S LECHON", F("s", 56), (240, 196, 98))
ctext(110, "& CARINDERIA  •  LAPINIGAN", F("r", 24), CREAM)
pill = "SABADO • OCT 31"; f = F("b", 30); w = d.textlength(pill, font=f)
d.rounded_rectangle(((W-w)/2-26, 158, (W+w)/2+26, 206), radius=24, fill=ORANGE); ctext(164, pill, f, PURPLE)
ctext(236, "TRICK OR TREAT", F("b", 104), ORANGE, 6)
ctext(352, "sa Thamara's!", F("b", 84), YEL, 6)
ctext(462, "Libre nga candy para sa mga bata!", F("b", 40), CREAM, 3)
# jack-o-lantern
cx, cy = 540, 760
for dx, c in ((-120, (230, 110, 15)), (120, (230, 110, 15)), (-60, (250, 135, 25)), (60, (250, 135, 25)), (0, (255, 150, 35))):
    d.ellipse((cx+dx-130, cy-150, cx+dx+130, cy+150), fill=c)
d.rounded_rectangle((cx-18, cy-200, cx+18, cy-140), radius=8, fill=(70, 120, 40))
d.polygon([(cx-120, cy-40), (cx-50, cy-40), (cx-85, cy-100)], fill=(60, 20, 10))
d.polygon([(cx+120, cy-40), (cx+50, cy-40), (cx+85, cy-100)], fill=(60, 20, 10))
d.polygon([(cx-20, cy+10), (cx+20, cy+10), (cx, cy-25)], fill=(60, 20, 10))
d.chord((cx-160, cy-20, cx+160, cy+120), 0, 180, fill=(60, 20, 10))
for k in (-90, -10, 70): d.rectangle((cx+k, cy+50, cx+k+28, cy+75), fill=(255, 150, 35))
# wrapped candies around
def candy(x, y, col, ang):
    a = math.radians(ang); ca, sa = math.cos(a), math.sin(a)
    def rot(px, py): return (x + px*ca - py*sa, y + px*sa + py*ca)
    d.polygon([rot(-55, -22), rot(-80, -35), rot(-80, 35), rot(-55, 22)], fill=col)
    d.polygon([rot(55, -22), rot(80, -35), rot(80, 35), rot(55, 22)], fill=col)
    d.ellipse((x-55, y-32, x+55, y+32), fill=col)
    d.line([rot(-30, -20), rot(30, 20)], fill=(255, 255, 255), width=6)
for x, y, col, a in [(170, 640, (230, 60, 90), 20), (900, 620, (80, 170, 240), -25), (150, 900, GREEN, -15),
                     (920, 890, (180, 90, 230), 30), (330, 1000, (255, 200, 40), 10), (760, 1010, (240, 90, 60), -10)]:
    candy(x, y, col, a)
# info box
d.rounded_rectangle((90, 1060, W-90, 1250), radius=28, fill=(25, 8, 35), outline=ORANGE, width=4)
ctext(1078, "Dad-a ang mga bata — naka-costume o dili!", F("b", 32), CREAM)
d.rounded_rectangle((170, 1130, W-170, 1220), radius=45, fill=YEL)
ctext(1146, "ADTO NA SA KARENDERIA", F("b", 44), PURPLE)
ctext(1275, "Samtang naa pa ang candy  •  ☎ (0951) 781 4902", F("b", 30), CREAM)
img.convert("RGB").save(sys.argv[1], quality=93); print(sys.argv[1])
