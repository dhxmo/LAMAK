import torch.nn as nn
import torch.utils.model_zoo as model_zoo
from model.utils import get_norm

__all__ = [
    "VGG",
    "vgg11",
    "vgg11_bn",
    "vgg13",
    "vgg13_bn",
    "vgg16",
    "vgg16_bn",
    "vgg19_bn",
    "vgg19",
]


model_urls = {
    "vgg11": "https://download.pytorch.org/models/vgg11-bbd30ac9.pth",
    "vgg13": "https://download.pytorch.org/models/vgg13-c768596a.pth",
    "vgg16": "https://download.pytorch.org/models/vgg16-397923af.pth",
    "vgg19": "https://download.pytorch.org/models/vgg19-dcbb9e9d.pth",
    "vgg11_bn": "https://download.pytorch.org/models/vgg11_bn-6002323d.pth",
    "vgg13_bn": "https://download.pytorch.org/models/vgg13_bn-abd245e5.pth",
    "vgg16_bn": "https://download.pytorch.org/models/vgg16_bn-6c64b313.pth",
    "vgg19_bn": "https://download.pytorch.org/models/vgg19_bn-c79401a0.pth",
}


class VGG(nn.Module):

    def __init__(self, features, num_classes=1000, init_weights=True):
        super(VGG, self).__init__()
        self.features = features
        self.avgpool = nn.AdaptiveAvgPool2d((7, 7))
        self.classifier = nn.Sequential(
            nn.Linear(512 * 7 * 7, 4096),
            nn.ReLU(True),
            nn.Dropout(),
            nn.Linear(4096, 4096),
            nn.ReLU(True),
            nn.Dropout(),
            nn.Linear(4096, num_classes),
        )
        if init_weights:
            self._initialize_weights()

    def forward(self, x):
        x = self.features(x)
        # x = self.avgpool(x)
        # x = x.view(x.size(0), -1)
        # x = self.classifier(x)
        return x

    def _initialize_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(
                    m.weight, mode="fan_out", nonlinearity="relu"
                )  # noqa
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.GroupNorm):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.InstanceNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)


def make_layers(cfg, batch_norm=False, norm_type="Unknown"):
    layers = []
    in_channels = 3
    for v in cfg:
        if v == "M":
            layers += [nn.MaxPool2d(kernel_size=2, stride=2)]
        else:
            conv2d = nn.Conv2d(in_channels, v, kernel_size=3, padding=1)
            if batch_norm:
                layers += [conv2d, get_norm(norm_type, v), nn.ReLU(inplace=True)]
            else:
                layers += [conv2d, nn.ReLU(inplace=True)]
            in_channels = v
    return nn.Sequential(*layers)


cfg = {
    "A": [64, "M", 128, "M", 256, 256, "M", 512, 512, "M", 512, 512, "M"],
    "B": [
        64,
        64,
        "M",
        128,
        128,
        "M",
        256,
        256,
        "M",
        512,
        512,
        "M",
        512,
        512,
        "M",
    ],  # noqa
    "D": [
        64,
        64,
        "M",
        128,
        128,
        "M",
        256,
        256,
        256,
        "M",
        512,
        512,
        512,
        "M",
        512,
        512,
        512,
        "M",
    ],  # noqa
    "E": [
        64,
        64,
        "M",
        128,
        128,
        "M",
        256,
        256,
        256,
        256,
        "M",
        512,
        512,
        512,
        512,
        "M",
        512,
        512,
        512,
        512,
        "M",
    ],  # noqa
}


def vgg11(config, **kwargs):
    """VGG 11-layer model (configuration "A")

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    if config.pretrained:
        kwargs["init_weights"] = False
    model = VGG(make_layers(cfg["A"]), **kwargs)
    if config.pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls["vgg11"]), strict=False)
    return model


def vgg11_bn(config, **kwargs):
    """VGG 11-layer model (configuration "A") with batch normalization

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    if config.pretrained:
        kwargs["init_weights"] = False
    model = VGG(
        make_layers(cfg["A"], batch_norm=True, norm_type=config.norm_type), **kwargs
    )
    if config.pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls["vgg11_bn"]), strict=False)
    return model


def vgg13(config, **kwargs):
    """VGG 13-layer model (configuration "B")

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    if config.pretrained:
        kwargs["init_weights"] = False
    model = VGG(make_layers(cfg["B"]), **kwargs)
    if config.pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls["vgg13"]), strict=False)
    return model


def vgg13_bn(config, **kwargs):
    """VGG 13-layer model (configuration "B") with batch normalization

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    if config.pretrained:
        kwargs["init_weights"] = False
    model = VGG(
        make_layers(cfg["B"], batch_norm=True, norm_type=config.norm_type), **kwargs
    )
    if config.pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls["vgg13_bn"]), strict=False)
    return model


def vgg16(config, **kwargs):
    """VGG 16-layer model (configuration "D")

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    if config.pretrained:
        kwargs["init_weights"] = False
    model = VGG(make_layers(cfg["D"]), **kwargs)
    if config.pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls["vgg16"]), strict=False)
    return model


def vgg16_bn(config, **kwargs):
    """VGG 16-layer model (configuration "D") with batch normalization

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    if config.pretrained:
        kwargs["init_weights"] = False
    model = VGG(
        make_layers(cfg["D"], batch_norm=True, norm_type=config.norm_type), **kwargs
    )
    if config.pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls["vgg16_bn"]), strict=False)
    return model


def vgg19(config, **kwargs):
    """VGG 19-layer model (configuration "E")

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    if config.pretrained:
        kwargs["init_weights"] = False
    model = VGG(make_layers(cfg["E"]), **kwargs)
    if config.pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls["vgg19"]), strict=False)
    return model


def vgg19_bn(config, **kwargs):
    """VGG 19-layer model (configuration 'E') with batch normalization

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    if config.pretrained:
        kwargs["init_weights"] = False
    model = VGG(
        make_layers(cfg["E"], batch_norm=True, norm_type=config.norm_type), **kwargs
    )
    if config.pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls["vgg19_bn"]), strict=False)
    return model
