import os
import scipy.io

def rename(dpath):
    for count, filename in enumerate(os.listdir(dpath)):
        dst = str(count) + ".mat"
        src = dpath +'/'+ filename
        dst = dpath +'/'+ dst

        # rename() function will
        # rename all the files
        os.rename(src, dst)

# def gps_mat(dpath):




if __name__ == '__main__':
    dpath = '/home/mohit/webots_code/data/samples'
    rename(dpath)
