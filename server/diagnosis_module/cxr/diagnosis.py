from torchvision import transforms
from PIL import Image
import torch
from diagnosis_module.cxr.models.classifier import Classifier
from easydict import EasyDict as edict
import json
from diagnosis_module.cxr.utils import transform
import numpy as np
import torch.nn.functional as F


def get_img(img_path: str, idx: int = None):
    # idx should be 1 or 2
    img = Image.open(img_path).convert("RGB")
    report_transpose = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
        ]
    )
    img_transformed = transforms.Compose(
        [
            transforms.Resize((384, 384)),
            transforms.ToTensor(),
            transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
        ]
    )
    img1, img2 = report_transpose(img), img_transformed(img)
    res = [img1.unsqueeze(dim=0), img2.unsqueeze(dim=0)]
    # img0 for text generation, img1 for inference
    if idx is not None:
        return res[idx - 1]
    return res


def get_cxr_img(img_path: str, img_cfg, idx: int = None):
    # idx should be 1 or 2
    img1 = Image.open(img_path).convert("RGB")
    img2 = Image.open(img_path)
    report_transpose = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
        ]
    )
    img1 = report_transpose(img1)
    img2 = np.array(img2)
    img2 = transform(img2, img_cfg)
    img2 = torch.tensor(img2, dtype=torch.float32)
    res = [img1.unsqueeze(dim=0), img2.unsqueeze(dim=0)]
    # img0 for text generation, img1 for inference
    if idx is not None:
        return res[idx - 1]
    return res


def get_pred(output, cfg):
    if cfg.criterion == "BCE" or cfg.criterion == "FL":
        # for num_class in cfg.num_classes:
        #     assert num_class == 1
        # pred = torch.sigmoid(output.view(-1)).cpu().detach().numpy()
        pred = torch.sigmoid(output.view(-1))
    elif cfg.criterion == "CE":
        for num_class in cfg.num_classes:
            assert num_class >= 2
        prob = F.softmax(output)
        # pred = prob[:, 1].cpu().detach().numpy()
        pred = prob[:, 1]
    else:
        raise Exception("Unknown criterion : {}".format(cfg.criterion))
    return pred


def cxr_infer(img_model, img, imgcfg):
    img_model.eval()
    outs_classes, _ = img_model(img)
    assert isinstance(outs_classes, list)
    # prob = np.zeros((len(imgcfg.Data_CLASSES), 1))
    prob = get_pred(torch.Tensor(outs_classes), imgcfg)
    return prob


def cxr_init(cfg_path, weight_path):
    imgcfg = edict(json.load(open(cfg_path)))
    img_model = Classifier(imgcfg)
    # model.to(torch.cuda())
    img_model.load_state_dict(torch.load(weight_path))
    return img_model, imgcfg
