import pyMeow as pm
import math

proc = pm.open_process("gta_sa.exe")

class Colors:
    red = pm.get_color("red")
    cyan = pm.get_color("cyan")
    green = pm.get_color("lime")
    yellow = pm.get_color("yellow")

class Modules:
    base = pm.get_module(proc,"gta_sa.exe")["base"]
    vcsawin = pm.get_module(proc,"iii.vc.sa.windowedmode.asi")["base"]
class Addresses:
    visible_ents = Modules.base+0x776844
    cam_pos = Modules.base+0x76EBFC 
    cam_yaw = Modules.base+0x76F258
    cam_pitch = Modules.base+0x76F248
    screen_dim = Modules.base+0x817044
    fps = Modules.vcsawin+0x3A03C
    xfov = Modules.base+0x76F250

class Pointers:
    pos = 0x14
    entity_list = Modules.base+0x76F3B8
    ent_aimed = Modules.base+0x76F3B8

class Offsets:
    health = 0x540
    ent_size = 0x7C4
    pos = 0x30
    is_valid = 0x414
    aimed = 0x79C
    burning = 0x730
    
    
class Entity:
    def __init__(self,base):
        self.base = base
        self.h = self.base+Offsets.health
        self.pos = pm.r_int(proc,self.base+Pointers.pos)+Offsets.pos
        self.burning = self.base+Offsets.burning
        
    def health(self):
        return pm.r_float(proc,self.h)
    def position(self):
        try:
            return pm.r_floats(proc,self.pos,3)
        except:
            return [-1.0,-1.0,-1.0]
    def burn(self):
        pm.w_int(proc,self.burning,12002112)
    def teleport(self,pos):
        pm.w_floats(proc,self.pos,pos)

def aimed_ent():
    return pm.r_int(proc,pm.r_int(proc,Pointers.ent_aimed)+Offsets.aimed)

def entities():
    player = pm.r_int(proc,Pointers.entity_list)
    nfound = 1
    ents = []
    ent_count = 140
    ply = player
    while nfound != ent_count:
        ply += Offsets.ent_size
        try:
            if pm.r_int(proc,ply+Pointers.pos) != 0 and pm.r_float(proc,ply+Offsets.health)>0:
                ents.append(Entity(ply))
                nfound+=1
        except:
            continue
        if len(ents) > 140:
            break


    return Entity(player),ents

def camera_position():
    return pm.r_floats(proc,Addresses.cam_pos,3)

def camera_orientation():
    return pm.r_float(proc,Addresses.cam_yaw),pm.r_float(proc,Addresses.cam_pitch)

def screen_resolution():
    return pm.r_ints(proc,Addresses.screen_dim,2)

def aim(yaw,pitch):
    pm.w_float(proc,Addresses.cam_yaw,yaw)
    pm.w_float(proc,Addresses.cam_pitch,pitch)

def wts(pos,camYaw,camPitch,worldpos,width,height,x_fov,y_fov):
    cam_pos = pos
    camToObj = [worldpos[i]-cam_pos[i] for i in range(3)]
    distToObj = math.sqrt(sum([camToObj[i]**2 for i in range(3)]))
    if distToObj == 0:
        distToObj = 0.0001
    camToObj = [i/distToObj for i in camToObj]
    objYaw = math.atan2(-camToObj[1],-camToObj[0])
    relYaw = camYaw-objYaw
    if (relYaw > math.pi):
        relYaw -= 2*math.pi
    if (relYaw<-math.pi):
        relYaw += 2*math.pi
    objPitch = math.asin(camToObj[2])
    relPitch = camPitch-objPitch
    if x_fov == 0:
        x_fov =0.001
    if y_fov == 0:
        y_fov = 0.001
    x = relYaw/(0.5*x_fov)
    y = relPitch/(0.5*y_fov)
    x = (x+1)/2
    y = (y+1)/2
    return x*width,y*height,distToObj

screen_width,screen_height = screen_resolution()
x_fov = math.radians(pm.r_float(proc,Addresses.xfov))
y_fov = x_fov/screen_width * screen_height
fps = pm.r_int(proc,Addresses.fps)
pm.overlay_init(target=f"GTA: San Andreas | {screen_width}x{screen_height} @ {fps} fps", fps=200, trackTarget=False)

while pm.overlay_loop(): #pm.overlay_loop():
    ply,ents = entities()
    yaw,pitch = camera_orientation()
    pos = camera_position()
    pm.begin_drawing()
    aimed = aimed_ent()
    if aimed != 0:
        ent = Entity(aimed)
        ent.burn()
        entpos = ent.position()
        entpos[2] += 0.25
        ent.teleport(entpos)
    pm.draw_text(hex(aimed_ent()),30,30,20,Colors.cyan)
    dists = []
    for i in ents:
        w_pos = i.position()
        x,y,dist = wts(pos,yaw,pitch,w_pos,screen_width,screen_height,x_fov,y_fov)
        dists.append(dist)
        try:
            width = 200/dist
            height = 400/dist
            x-=width/2
            pm.draw_line(x,y,x+width,y,Colors.red)
            pm.draw_line(x,y,x,y+height,Colors.green)
            pm.draw_line(x+width,y,x+width,y+height,Colors.cyan)
            pm.draw_line(x,y+height,x+width,y+height,Colors.yellow)
        except:
            pass
    pm.end_drawing()

