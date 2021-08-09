import os

HOME = os.environ['HOME']
spath = f'{HOME}/webots_code/data/stats'
ovr = 0

for filename in os.listdir(spath):
    with open(spath+f'/{filename}','r') as a:
        ovr += int(a.read())

print(ovr)
# 16342 at timestep=1920