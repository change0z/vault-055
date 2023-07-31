import torch
import torch.nn as nn 
import torchvision.transforms.functional as TF

class DoubleConvolution(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(DoubleConvolution, self).__init__() # The super() function is used to give access to methods and properties of a parent or sibling class. The super() function returns an object that represents the parent class.
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 3, 1, 1, bias=False), #bias = False since we are using Batch Normalization
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, 3, 1, 1, bias=False), 
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.conv(x)
    
class UNET(nn.Module):
    def __init__(
            self, in_channels=3, out_channels=1, features=[64, 128, 256, 512], 
    ):
        super(UNET, self).__init__()
        self.ups = nn.ModuleList()
        self.downs = nn.ModuleList()
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        # input = 161x16, maxpool will floor the divsion by 2 = 80x80, afte upsampling, the output will be 160x160 
        # Down part of UNET
        for feature in features:
            self.downs.append(DoubleConvolution(in_channels, feature))
            in_channels = feature

        # Up part of UNET
        for feature in reversed(features):
            self.ups.append(
                nn.ConvTranspose2d(
                    feature*2,  feature, kernel_size = 2, stride =2, #skip connect
                )
            )

            self.ups.append(DoubleConvolution(feature*2, feature))

        self.bottleneck = DoubleConvolution(features[-1], features[-1]*2)
        self.final_conv =  nn.Conv2d(features[0], out_channels, kernel_size=1)

    def forward(self, x):
        skip_connections = []

        for down in self.downs:
            x = down(x)
            skip_connections.append(x)
            x = self.pool(x)

        x = self.bottleneck(x)
        skip_connections = skip_connections[::-1]

        for idx in range(0, len(self.ups), 2):
            x = self.ups[idx](x)
            skip_connection = skip_connections[idx//2]

            if x.shape != skip_connection.shape:
                x = TF.resize(x, size = skip_connection.shape[2:])

            concat_skip = torch.cat((skip_connection,x), dim=1)
            x = self.ups[idx+1](concat_skip)
        
        return self.final_conv(x)
    
def test():
    x = torch.randn((3, 1, 160, 160))
    model =  UNET(in_channels=1, out_channels=1)
    prediction = model(x)
    print(prediction.shape)
    print(x.shape)
    assert prediction.shape == x.shape

if __name__ == "__main__":
    test()


