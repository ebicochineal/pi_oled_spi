#! /usr/bin/env python3
import os
import sys
import math
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306
from PIL import Image, ImageDraw, ImageFont

class Vector3:
    @staticmethod
    def Add(vec1, vec2):
        return [vec1[0] + vec2[0], vec1[1] + vec2[1], vec1[2] + vec2[2]]

    @staticmethod
    def Sub(vec1, vec2):
        return [vec1[0] - vec2[0], vec1[1] - vec2[1], vec1[2] - vec2[2]]

    @staticmethod
    def Mul(vec, m):
        return [vec[0] * m, vec[1] * m, vec[2] * m]

    @staticmethod
    def Div(vec, d):
        return [vec[0] / float(d), vec[1] / float(d), vec[2] / float(d)]

    @staticmethod
    def Dot(vec1, vec2):
        return vec1[0] * vec2[0] + vec1[1] * vec2[1] + vec1[2] * vec2[2]

    @staticmethod
    def Cross(vec1, vec2):
        return vec1[1] * vec2[2] - vec1[2] * vec2[1],vec1[2] * vec2[0] - vec1[0] * vec2[2],vec1[0] * vec2[1] - vec1[1] * vec2[0]

    @staticmethod
    def Normalize(vec):
        if math.sqrt(vec[0] * vec[0] + vec[1] * vec[1] + vec[2] * vec[2]) != 0:
            return [vec[0] / float(math.sqrt(vec[0] * vec[0] + vec[1] * vec[1] + vec[2] * vec[2])),vec[1] / float(math.sqrt(vec[0] * vec[0] + vec[1] * vec[1] + vec[2] * vec[2])),vec[2] / float(math.sqrt(vec[0] * vec[0] + vec[1] * vec[1] + vec[2] * vec[2]))]
        return [0.0, 0.0, 0.0]

    @staticmethod
    def Reflect(vec, nor):
        return Vector3.Add(Vector3.Mul(nor , 2 * (-vec[0] * nor[0] + -vec[1] * nor[1] + -vec[2] * nor[2])),vec)

class Object3D:
    def __init__(self, vertex, index):
        self.position = [0, 0, 0]
        self.rotation = [0, 0, 0]
        self.scale = [1, 1, 1]
        self.vertex = vertex
        self.index = index
    
    @staticmethod
    def Load(filepath):
        objfile = open(filepath)
        v = []
        i = []
        for d in objfile.readlines():
            if d.startswith('v '):
                v4 = d.replace('\n', '').split(' ')
                v.append([float(v4[1]), float(v4[2]), float(v4[3])])
            if d.startswith('f '):
                v4 = d.replace('\n', '').split(' ')
                i.append([int(v4[1])-1, int(v4[2])-1, int(v4[3])-1])
        objfile.close()
        return Object3D(v, i)

class Matrix:
    @staticmethod
    def matmul14proj(v, m):
        r = [0, 0, 0, 0]
        for k in range(4):
            for o in range(4):
                r[k] += v[o] * m[o][k]
        if r[3] > 0:
            return [r[0] / float(r[3]), r[1] / float(r[3]), r[2] / float(r[3])]
        else:
            return [r[0], r[1], r[2]]
    
    @staticmethod
    def matmul14(v, m):
        r = [0, 0, 0, 0]
        for k in range(4):
            for o in range(4):
                r[k] += v[o] * m[o][k]
        return r

    @staticmethod
    def matmul44(v, m):
        r = ([0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0])
        for i in range(4):
            for k in range(4):
                for o in range(4):
                    r[i][k] += v[i][o] * m[o][k]
        return r
    
    @staticmethod
    def world_matrix(rot, pos, move):
        r = ([1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1])
        r = Matrix.matmul44(r, rot)
        r = Matrix.matmul44(r, pos)
        r = Matrix.matmul44(r, move)
        return r
    
    @staticmethod
    def MatrixPerspectiveFovRH(cvx, cvy):
        aspect =  float(cvx)/float(cvy)
        fov = math.radians(45)
        near = 4.0
        far = 40.0
        sy = 1.0/math.tan(fov * 0.5)
        sx = sy / aspect
        sz = far / (near - far)
        return [sx,0.0,0.0,0.0], [0.0,sy,0.0,0.0], [0.0,0.0,sz,-1.0], [0.0,0.0,sz * near,0.0]

class App:
    def __init__(self, filepath):
        self.cvx = 128
        self.cvy = 64
        self.move_x = 0
        self.move_z = 0
        self.rot_y = 0
        hcvx = self.cvx // 2
        hcvy = self.cvy // 2
        self.obj = Object3D.Load(filepath)
        self.vb = None
        proj = Matrix.MatrixPerspectiveFovRH(self.cvx, self.cvy)
        screen = [hcvx, 0, 0, 0], [0, -hcvy, 0, 0], [0, 0, 1, 0], [hcvx, hcvy, 0, 1]
        self.projscreen = Matrix.matmul44(Matrix.matmul44(([1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]), proj), screen)
        self.getch = None
        self.cls = None
        if 'win' in sys.platform and 'darwin' != sys.platform:
            self.getch = self.getch_win
            self.cls = 'cls'
        else:
            self.getch = self.getch_unix
            self.cls = 'clear'
        
        RST = 24
        DC = 23
        SPI_PORT = 0
        SPI_DEVICE = 0
        self.disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST, dc=DC, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=8000000))
        self.disp.begin()
        self.disp.clear()
        self.disp.display()
        
        self.image = Image.new('1', (self.cvx, self.cvy))
        self.draw = ImageDraw.Draw(self.image)
        self.font = ImageFont.load_default()
    
    def __del__(self):
        self.disp.clear()
        self.disp.display()
        os.system(self.cls)
    
    def getch_unix(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        return ch
    def getch_win(self):
        import msvcrt
        try:
            return msvcrt.getch().decode('utf8')
        except:
            return '' 
    
    def draw_wire(self):
        self.draw.rectangle((0, 0, self.cvx, self.cvy), outline=0, fill=0)
        for v0, v1, v2 in self.obj.index:
            vec1 = Vector3.Sub(self.vb[v1], self.vb[v0])
            vec2 = Vector3.Sub(self.vb[v2], self.vb[v1])
            c = Vector3.Cross(vec1, vec2)
            if c[2] > 0 : continue
            
            w0x, w0y, w0z = self.vb[v0]
            w1x, w1y, w1z = self.vb[v1]
            w2x, w2y, w2z = self.vb[v2]
            
            if 0 < w0z < 1 or 0 < w1z < 1 or 0 < w2z < 1:
                if 0 < w0x < self.cvx or 0 < w1x < self.cvx or 0 < w2x < self.cvx:
                    if 0 < w0y < self.cvy or 0 < w1y < self.cvy or 0 < w2y < self.cvy:
                        self.draw.line((w0x, w0y, w1x, w1y), fill = 1)
                        self.draw.line((w1x, w1y, w2x, w2y), fill = 1)
                        self.draw.line((w2x, w2y, w0x, w0y), fill = 1)
        self.disp.image(self.image)
        self.disp.display()
    
    def loop(self):
        while 1:
            move = [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [self.move_x * 0.2, 0, self.move_z * 0.2, 1]
            pos = [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, -2, -16, 1]
            rot = [math.cos(math.radians(self.rot_y)), 0, math.sin(math.radians(self.rot_y)), 0], [0, 1, 0, 0], [-math.sin(math.radians(self.rot_y)), 0, math.cos(math.radians(self.rot_y)), 0], [0, 0, 0, 1]
            mat = Matrix.world_matrix(rot, pos, move)

            self.vb = [Matrix.matmul14((self.obj.vertex[x][0], self.obj.vertex[x][1], self.obj.vertex[x][2], 1), mat) for x in range(len(self.obj.vertex))]
            self.vb = [Matrix.matmul14proj((self.vb[x][0], self.vb[x][1], self.vb[x][2],1), self.projscreen) for x in range(len(self.obj.vertex))]
            
            self.draw_wire()
            os.system(self.cls)
            g = self.getch()
            if g == 's' : self.move_z += 4
            if g == 'a' : self.move_x -= 4
            if g == 'd' : self.move_x += 4
            if g == 'w' : self.move_z -= 4
            if g == 'e' : self.rot_y += 8
            if g == 'q' : self.rot_y -= 8
            rot_y = (360 + self.rot_y) % 360
            if g == 'z' : break
    
def main():
    if len(sys.argv) > 1:
        app = App(sys.argv[1])
        app.loop()

if __name__ == '__main__':
    main()