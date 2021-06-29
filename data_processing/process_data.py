import os

def rename(dpath,lpath):
    for count, filename in enumerate(os.listdir(dpath)):
        dst1 = dpath +'/' + str(count) + ".mat"
        src1 = dpath +'/'+ filename

        dst2 = lpath + '/' + str(count)+".npy"
        src2 = lpath + '/' + filename[:-3]+ "npy"

        # rename() function will
        # rename all the files
        os.rename(src1, dst1)
        os.rename(src2, dst2)

if __name__ == '__main__':
    dpath = '/home/mohit/webots_code/data/samples'
    lpath = '/home/mohit/webots_code/data/lidar_samples'
    rename(dpath,lpath)
