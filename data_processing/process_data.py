import os

def rename(dpath,lpath):
    for count, filename in enumerate(os.listdir(dpath)):
        dst1 = dpath +'/' + str(count) + ".mat"
        src1 = dpath +'/'+ filename

        dst2 = lpath + '/' + str(count)+".npz"
        src2 = lpath + '/' + filename[:-3]+ "npz"

        # rename() function will
        # rename all the files
        os.rename(src1, dst1)
        os.rename(src2, dst2)

if __name__ == '__main__':
    HOME = os.environ['HOME']
    dpath = f'{HOME}/webots_code/data/samples'
    lpath = f'{HOME}/webots_code/data/lidar_samples'
    rename(dpath,lpath)
