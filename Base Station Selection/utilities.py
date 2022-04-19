import torch
import math

def top_k_acc(y_true:torch.Tensor,y_pred:torch.Tensor,k=1):
    
    y_pred_tpk = torch.topk(y_pred,k,dim=1)[1]
    
    ovr = 0
    pos = 0

    for i in range(0,len(y_pred_tpk)):
        if(y_true[i] in y_pred_tpk[i]):
            pos+=1
        ovr+=1
    
    acc = float(pos)/float(ovr)
    return acc

def dist_gps(gps1, gps2):
    lat1, lon1, _ = gps1
    lat2, lon2, _ = gps2
    R = 6371000  # radius of Earth in meters
    phi_1 = math.radians(lat1)
    phi_2 = math.radians(lat2)

    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi_1) * math.cos(phi_2) * \
        math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c