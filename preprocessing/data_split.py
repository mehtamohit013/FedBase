import os
import shutil

HOME = os.environ['HOME']
data = os.path.join(HOME, 'webots_code', 'data')
lpath = os.path.join(data, 'lidar_samples')
gpath = os.path.join(data, 'samples')
lapath = os.path.join(data, 'sample_label')

train = os.path.join(data,'train')
val = os.path.join(data,'val')

os.makedirs(train,exist_ok=True)
os.makedirs(val,exist_ok=True)

os.makedirs(os.path.join(train,'lidar'),exist_ok=True)
os.makedirs(os.path.join(train,'gps'),exist_ok=True)
os.makedirs(os.path.join(train,'label'),exist_ok=True)

os.makedirs(os.path.join(val,'lidar'),exist_ok=True)
os.makedirs(os.path.join(val,'gps'),exist_ok=True)
os.makedirs(os.path.join(val,'label'),exist_ok=True)

n_samples = len(os.listdir(lpath))
train_samples = int(n_samples*0.8)
val_samples = n_samples-train_samples

for count,filename in enumerate(os.listdir(gpath)):
    a = filename[:-4]

    if count<train_samples:
        shutil.move(os.path.join(lpath,a+'.npz'),
                    os.path.join(data,'train','lidar',str(count)+'.npz'))
        shutil.move(os.path.join(gpath,a+'.mat'),
                    os.path.join(data,'train','gps',str(count)+'.mat'))
        shutil.move(os.path.join(lapath,a+'.mat'),
                    os.path.join(data,'train','label',str(count)+'.mat'))
    else:
        shutil.move(os.path.join(lpath,a+'.npz'),
                    os.path.join(data,'val','lidar',str(count-train_samples)+'.npz'))
        shutil.move(os.path.join(gpath,a+'.mat'),
                    os.path.join(data,'val','gps',str(count-train_samples)+'.mat'))
        shutil.move(os.path.join(lapath,a+'.mat'),
                    os.path.join(data,'val','label',str(count-train_samples)+'.mat'))

print(f'Splitting completed. Train size: {train_samples}. Val size: {val_samples}')