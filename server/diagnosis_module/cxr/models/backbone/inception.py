import re
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.utils.model_zoo as model_zoo
from model.utils import get_norm

__all__ = ["Inception3", "inception_v3"]


model_urls = {
    # Inception v3 ported from TensorFlow
    "inception_v3_google": "https://download.pytorch.org/models/inception_v3_google-1a9a5a14.pth",  # noqa
}


def inception_v3(cfg, **kwargs):
    r"""Inception v3 model architecture from
    `"Rethinking the Inception Architecture for Computer Vision" <http://arxiv.org/abs/1512.00567>`_.  # noqa

    .. note::
        **Important**: In contrast to the other models the inception_v3 expects tensors with a size of  # noqa
        N x 3 x 299 x 299, so ensure your images are sized accordingly.

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    if cfg.pretrained:
        if "transform_input" not in kwargs:
            kwargs["transform_input"] = True
        model = Inception3(norm_type=cfg.norm_type, **kwargs)

        pattern = re.compile(
            r"^(.*bn\d\.(?:weight|bias|running_mean|running_var))$"
        )  # noqa
        state_dict = model_zoo.load_url(model_urls["inception_v3_google"])
        for key in list(state_dict.keys()):
            res = pattern.match(key)
            if res:
                new_key = res.group(1).replace("bn", "norm")
                state_dict[new_key] = state_dict[key]
                del state_dict[key]
        model.load_state_dict(state_dict, strict=False)
        return model

    return Inception3(norm_type=cfg.norm_type, **kwargs)


class Inception3(nn.Module):

    def __init__(
        self,
        num_classes=1000,
        norm_type="Unknown",
        aux_logits=True,
        transform_input=False,
    ):  # noqa
        super(Inception3, self).__init__()
        self.aux_logits = aux_logits
        self.transform_input = transform_input
        self.Conv2d_1a_3x3 = BasicConv2d(
            3, 32, norm_type=norm_type, kernel_size=3, stride=2
        )
        self.Conv2d_2a_3x3 = BasicConv2d(32, 32, norm_type=norm_type, kernel_size=3)
        self.Conv2d_2b_3x3 = BasicConv2d(
            32, 64, norm_type=norm_type, kernel_size=3, padding=1
        )
        self.Conv2d_3b_1x1 = BasicConv2d(64, 80, norm_type=norm_type, kernel_size=1)
        self.Conv2d_4a_3x3 = BasicConv2d(80, 192, norm_type=norm_type, kernel_size=3)
        self.Mixed_5b = InceptionA(192, pool_features=32, norm_type=norm_type)
        self.Mixed_5c = InceptionA(256, pool_features=64, norm_type=norm_type)
        self.Mixed_5d = InceptionA(288, pool_features=64, norm_type=norm_type)
        self.Mixed_6a = InceptionB(288, norm_type=norm_type)
        self.Mixed_6b = InceptionC(768, channels_7x7=128, norm_type=norm_type)
        self.Mixed_6c = InceptionC(768, channels_7x7=160, norm_type=norm_type)
        self.Mixed_6d = InceptionC(768, channels_7x7=160, norm_type=norm_type)
        self.Mixed_6e = InceptionC(768, channels_7x7=192, norm_type=norm_type)
        if aux_logits:
            self.AuxLogits = InceptionAux(768, num_classes, norm_type=norm_type)
        self.Mixed_7a = InceptionD(768, norm_type=norm_type)
        self.Mixed_7b = InceptionE(1280, norm_type=norm_type)
        self.Mixed_7c = InceptionE(2048, norm_type=norm_type)
        self.fc = nn.Linear(2048, num_classes)

        for m in self.modules():
            if isinstance(m, nn.Conv2d) or isinstance(m, nn.Linear):
                import scipy.stats as stats

                stddev = m.stddev if hasattr(m, "stddev") else 0.1
                X = stats.truncnorm(-2, 2, scale=stddev)
                values = torch.Tensor(X.rvs(m.weight.numel()))
                values = values.view(m.weight.size())
                m.weight.data.copy_(values)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.GroupNorm):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.InstanceNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def forward(self, x):
        if self.transform_input:
            x_ch0 = (
                torch.unsqueeze(x[:, 0], 1) * (0.229 / 0.5) + (0.485 - 0.5) / 0.5
            )  # noqa
            x_ch1 = (
                torch.unsqueeze(x[:, 1], 1) * (0.224 / 0.5) + (0.456 - 0.5) / 0.5
            )  # noqa
            x_ch2 = (
                torch.unsqueeze(x[:, 2], 1) * (0.225 / 0.5) + (0.406 - 0.5) / 0.5
            )  # noqa
            x = torch.cat((x_ch0, x_ch1, x_ch2), 1)
        # N x 3 x 299 x 299
        x = self.Conv2d_1a_3x3(x)
        # N x 32 x 149 x 149
        x = self.Conv2d_2a_3x3(x)
        # N x 32 x 147 x 147
        x = self.Conv2d_2b_3x3(x)
        # N x 64 x 147 x 147
        x = F.max_pool2d(x, kernel_size=3, stride=2)
        # N x 64 x 73 x 73
        x = self.Conv2d_3b_1x1(x)
        # N x 80 x 73 x 73
        x = self.Conv2d_4a_3x3(x)
        # N x 192 x 71 x 71
        x = F.max_pool2d(x, kernel_size=3, stride=2)
        # N x 192 x 35 x 35
        x = self.Mixed_5b(x)
        # N x 256 x 35 x 35
        x = self.Mixed_5c(x)
        # N x 288 x 35 x 35
        x = self.Mixed_5d(x)
        # N x 288 x 35 x 35
        x = self.Mixed_6a(x)
        # N x 768 x 17 x 17
        x = self.Mixed_6b(x)
        # N x 768 x 17 x 17
        x = self.Mixed_6c(x)
        # N x 768 x 17 x 17
        x = self.Mixed_6d(x)
        # N x 768 x 17 x 17
        x = self.Mixed_6e(x)
        # N x 768 x 17 x 17
        # if self.training and self.aux_logits:
        #     aux = self.AuxLogits(x)
        # N x 768 x 17 x 17
        x = self.Mixed_7a(x)
        # N x 1280 x 8 x 8
        x = self.Mixed_7b(x)
        # N x 2048 x 8 x 8
        x = self.Mixed_7c(x)
        # N x 2048 x 8 x 8
        # Adaptive average pooling
        # x = F.adaptive_avg_pool2d(x, (1, 1))
        # N x 2048 x 1 x 1
        # x = F.dropout(x, training=self.training)
        # N x 2048 x 1 x 1
        # x = x.view(x.size(0), -1)
        # N x 2048
        # x = self.fc(x)
        # N x 1000 (num_classes)
        # if self.training and self.aux_logits:
        #     return x, aux
        return x


class InceptionA(nn.Module):

    def __init__(self, in_channels, pool_features, norm_type="Unknown"):
        super(InceptionA, self).__init__()
        self.branch1x1 = BasicConv2d(
            in_channels, 64, norm_type=norm_type, kernel_size=1
        )

        self.branch5x5_1 = BasicConv2d(
            in_channels, 48, norm_type=norm_type, kernel_size=1
        )
        self.branch5x5_2 = BasicConv2d(
            48, 64, norm_type=norm_type, kernel_size=5, padding=2
        )

        self.branch3x3dbl_1 = BasicConv2d(
            in_channels, 64, norm_type=norm_type, kernel_size=1
        )
        self.branch3x3dbl_2 = BasicConv2d(
            64, 96, norm_type=norm_type, kernel_size=3, padding=1
        )
        self.branch3x3dbl_3 = BasicConv2d(
            96, 96, norm_type=norm_type, kernel_size=3, padding=1
        )

        self.branch_pool = BasicConv2d(
            in_channels, pool_features, norm_type=norm_type, kernel_size=1
        )  # noqa

    def forward(self, x):
        branch1x1 = self.branch1x1(x)

        branch5x5 = self.branch5x5_1(x)
        branch5x5 = self.branch5x5_2(branch5x5)

        branch3x3dbl = self.branch3x3dbl_1(x)
        branch3x3dbl = self.branch3x3dbl_2(branch3x3dbl)
        branch3x3dbl = self.branch3x3dbl_3(branch3x3dbl)

        branch_pool = F.avg_pool2d(x, kernel_size=3, stride=1, padding=1)
        branch_pool = self.branch_pool(branch_pool)

        outputs = [branch1x1, branch5x5, branch3x3dbl, branch_pool]
        return torch.cat(outputs, 1)


class InceptionB(nn.Module):

    def __init__(self, in_channels, norm_type="Unknown"):
        super(InceptionB, self).__init__()
        self.branch3x3 = BasicConv2d(
            in_channels, 384, norm_type=norm_type, kernel_size=3, stride=2
        )

        self.branch3x3dbl_1 = BasicConv2d(
            in_channels, 64, norm_type=norm_type, kernel_size=1
        )
        self.branch3x3dbl_2 = BasicConv2d(
            64, 96, norm_type=norm_type, kernel_size=3, padding=1
        )
        self.branch3x3dbl_3 = BasicConv2d(
            96, 96, norm_type=norm_type, kernel_size=3, stride=2
        )

    def forward(self, x):
        branch3x3 = self.branch3x3(x)

        branch3x3dbl = self.branch3x3dbl_1(x)
        branch3x3dbl = self.branch3x3dbl_2(branch3x3dbl)
        branch3x3dbl = self.branch3x3dbl_3(branch3x3dbl)

        branch_pool = F.max_pool2d(x, kernel_size=3, stride=2)

        outputs = [branch3x3, branch3x3dbl, branch_pool]
        return torch.cat(outputs, 1)


class InceptionC(nn.Module):

    def __init__(self, in_channels, channels_7x7, norm_type="Unknown"):
        super(InceptionC, self).__init__()
        self.branch1x1 = BasicConv2d(
            in_channels, 192, norm_type=norm_type, kernel_size=1
        )

        c7 = channels_7x7
        self.branch7x7_1 = BasicConv2d(
            in_channels, c7, norm_type=norm_type, kernel_size=1
        )
        self.branch7x7_2 = BasicConv2d(
            c7, c7, norm_type=norm_type, kernel_size=(1, 7), padding=(0, 3)
        )  # noqa
        self.branch7x7_3 = BasicConv2d(
            c7, 192, norm_type=norm_type, kernel_size=(7, 1), padding=(3, 0)
        )  # noqa

        self.branch7x7dbl_1 = BasicConv2d(
            in_channels, c7, norm_type=norm_type, kernel_size=1
        )
        self.branch7x7dbl_2 = BasicConv2d(
            c7, c7, norm_type=norm_type, kernel_size=(7, 1), padding=(3, 0)
        )  # noqa
        self.branch7x7dbl_3 = BasicConv2d(
            c7, c7, norm_type=norm_type, kernel_size=(1, 7), padding=(0, 3)
        )  # noqa
        self.branch7x7dbl_4 = BasicConv2d(
            c7, c7, norm_type=norm_type, kernel_size=(7, 1), padding=(3, 0)
        )  # noqa
        self.branch7x7dbl_5 = BasicConv2d(
            c7, 192, norm_type=norm_type, kernel_size=(1, 7), padding=(0, 3)
        )  # noqa

        self.branch_pool = BasicConv2d(
            in_channels, 192, norm_type=norm_type, kernel_size=1
        )

    def forward(self, x):
        branch1x1 = self.branch1x1(x)

        branch7x7 = self.branch7x7_1(x)
        branch7x7 = self.branch7x7_2(branch7x7)
        branch7x7 = self.branch7x7_3(branch7x7)

        branch7x7dbl = self.branch7x7dbl_1(x)
        branch7x7dbl = self.branch7x7dbl_2(branch7x7dbl)
        branch7x7dbl = self.branch7x7dbl_3(branch7x7dbl)
        branch7x7dbl = self.branch7x7dbl_4(branch7x7dbl)
        branch7x7dbl = self.branch7x7dbl_5(branch7x7dbl)

        branch_pool = F.avg_pool2d(x, kernel_size=3, stride=1, padding=1)
        branch_pool = self.branch_pool(branch_pool)

        outputs = [branch1x1, branch7x7, branch7x7dbl, branch_pool]
        return torch.cat(outputs, 1)


class InceptionD(nn.Module):

    def __init__(self, in_channels, norm_type="Unknown"):
        super(InceptionD, self).__init__()
        self.branch3x3_1 = BasicConv2d(
            in_channels, 192, norm_type=norm_type, kernel_size=1
        )
        self.branch3x3_2 = BasicConv2d(
            192, 320, norm_type=norm_type, kernel_size=3, stride=2
        )

        self.branch7x7x3_1 = BasicConv2d(
            in_channels, 192, norm_type=norm_type, kernel_size=1
        )
        self.branch7x7x3_2 = BasicConv2d(
            192, 192, norm_type=norm_type, kernel_size=(1, 7), padding=(0, 3)
        )  # noqa
        self.branch7x7x3_3 = BasicConv2d(
            192, 192, norm_type=norm_type, kernel_size=(7, 1), padding=(3, 0)
        )  # noqa
        self.branch7x7x3_4 = BasicConv2d(
            192, 192, norm_type=norm_type, kernel_size=3, stride=2
        )

    def forward(self, x):
        branch3x3 = self.branch3x3_1(x)
        branch3x3 = self.branch3x3_2(branch3x3)

        branch7x7x3 = self.branch7x7x3_1(x)
        branch7x7x3 = self.branch7x7x3_2(branch7x7x3)
        branch7x7x3 = self.branch7x7x3_3(branch7x7x3)
        branch7x7x3 = self.branch7x7x3_4(branch7x7x3)

        branch_pool = F.max_pool2d(x, kernel_size=3, stride=2)
        outputs = [branch3x3, branch7x7x3, branch_pool]
        return torch.cat(outputs, 1)


class InceptionE(nn.Module):

    def __init__(self, in_channels, norm_type="Unknown"):
        super(InceptionE, self).__init__()
        self.branch1x1 = BasicConv2d(
            in_channels, 320, norm_type=norm_type, kernel_size=1
        )

        self.branch3x3_1 = BasicConv2d(
            in_channels, 384, norm_type=norm_type, kernel_size=1
        )
        self.branch3x3_2a = BasicConv2d(
            384, 384, norm_type=norm_type, kernel_size=(1, 3), padding=(0, 1)
        )  # noqa
        self.branch3x3_2b = BasicConv2d(
            384, 384, norm_type=norm_type, kernel_size=(3, 1), padding=(1, 0)
        )  # noqa

        self.branch3x3dbl_1 = BasicConv2d(
            in_channels, 448, norm_type=norm_type, kernel_size=1
        )
        self.branch3x3dbl_2 = BasicConv2d(
            448, 384, norm_type=norm_type, kernel_size=3, padding=1
        )
        self.branch3x3dbl_3a = BasicConv2d(
            384, 384, norm_type=norm_type, kernel_size=(1, 3), padding=(0, 1)
        )  # noqa
        self.branch3x3dbl_3b = BasicConv2d(
            384, 384, norm_type=norm_type, kernel_size=(3, 1), padding=(1, 0)
        )  # noqa

        self.branch_pool = BasicConv2d(
            in_channels, 192, norm_type=norm_type, kernel_size=1
        )

    def forward(self, x):
        branch1x1 = self.branch1x1(x)

        branch3x3 = self.branch3x3_1(x)
        branch3x3 = [
            self.branch3x3_2a(branch3x3),
            self.branch3x3_2b(branch3x3),
        ]
        branch3x3 = torch.cat(branch3x3, 1)

        branch3x3dbl = self.branch3x3dbl_1(x)
        branch3x3dbl = self.branch3x3dbl_2(branch3x3dbl)
        branch3x3dbl = [
            self.branch3x3dbl_3a(branch3x3dbl),
            self.branch3x3dbl_3b(branch3x3dbl),
        ]
        branch3x3dbl = torch.cat(branch3x3dbl, 1)

        branch_pool = F.avg_pool2d(x, kernel_size=3, stride=1, padding=1)
        branch_pool = self.branch_pool(branch_pool)

        outputs = [branch1x1, branch3x3, branch3x3dbl, branch_pool]
        return torch.cat(outputs, 1)


class InceptionAux(nn.Module):

    def __init__(self, in_channels, num_classes, norm_type="Unknown"):
        super(InceptionAux, self).__init__()
        self.conv0 = BasicConv2d(in_channels, 128, norm_type=norm_type, kernel_size=1)
        self.conv1 = BasicConv2d(128, 768, norm_type=norm_type, kernel_size=5)
        self.conv1.stddev = 0.01
        self.fc = nn.Linear(768, num_classes)
        self.fc.stddev = 0.001

    def forward(self, x):
        # N x 768 x 17 x 17
        x = F.avg_pool2d(x, kernel_size=5, stride=3)
        # N x 768 x 5 x 5
        x = self.conv0(x)
        # N x 128 x 5 x 5
        x = self.conv1(x)
        # N x 768 x 1 x 1
        # Adaptive average pooling
        x = F.adaptive_avg_pool2d(x, (1, 1))
        # N x 768 x 1 x 1
        x = x.view(x.size(0), -1)
        # N x 768
        x = self.fc(x)
        # N x 1000
        return x


class BasicConv2d(nn.Module):

    def __init__(self, in_channels, out_channels, norm_type="Unknown", **kwargs):
        super(BasicConv2d, self).__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, bias=False, **kwargs)
        self.norm = get_norm(norm_type, out_channels, eps=0.001)

    def forward(self, x):
        x = self.conv(x)
        x = self.norm(x)
        return F.relu(x, inplace=True)
