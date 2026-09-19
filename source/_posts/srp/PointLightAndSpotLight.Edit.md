---
title: 点光源和聚光灯
date: 2026-09-19 18:58:47
categories:
tags:
description:
cover: /images/posts/srp/PointLightAndSpotLight/cover.png
mathjax: true
typora-root-url: ../..
typora-copy-images-to: ../../images/posts/SRP/PointLightAndSpotLight
---

这篇文章讲讲一下点光源和聚光灯的在兰伯特光照模型下的计算原理。

## 点光源

![Unity里的点光源](/images/posts/srp/PointLightAndSpotLight/image-20260919190336506.png)

Unity里，点光源会有一个range参数

点光源可以看作空间中的一个发光点，它向四周均匀发光。与方向光不同，点光源照射到每个片元时的光照方向都不一样，因此需要用光源位置减去片元位置来计算：

$$
\boldsymbol{L}=\boldsymbol{P}_{light}-\boldsymbol{P}_{surface}
$$

其中，$\boldsymbol{P}_{light}$ 是点光源的世界空间位置，$\boldsymbol{P}_{surface}$ 是片元的世界空间位置。$\boldsymbol{L}$ 的长度就是片元到光源的距离 $d$，将它归一化后可以得到片元指向光源的方向：

$$
d^2=\boldsymbol{L}\cdot\boldsymbol{L},\qquad \hat{\boldsymbol{L}}=\frac{\boldsymbol{L}}{d}
$$

在兰伯特光照模型中，表面接收到的光照还与法线和光照方向之间的夹角有关：

$$
NdotL=saturate(\boldsymbol{N}\cdot\hat{\boldsymbol{L}})
$$

当表面正对光源时，$NdotL$ 为 $1$；当光源位于表面背面时，$NdotL$ 为 $0$。

### 距离衰减

光从一个点向四周传播时，会分散到越来越大的球面上。球的表面积与距离的平方成正比，因此点光源的亮度可以使用距离平方的倒数来衰减：

$$
attenuation_{distance}=\frac{1}{max(d^2,\epsilon)}
$$

$\epsilon$ 是一个很小的正数，用来避免片元与光源重合时除以零。单独使用平方反比衰减时，光照永远不会真正变为 $0$。为了让 Unity 中的 `range` 能明确限制光照范围，还需要在靠近范围边缘时增加一段平滑衰减：

$$
attenuation_{range}=saturate\left(1-\frac{d^2}{range^2}\right)^2
$$

当片元位于光源中心时，这一项为 $1$；当距离到达或超过 `range` 时，这一项为 $0$。这里的平方作用于 `saturate` 后的整个范围衰减值，而不是对距离或 `range` 单独平方。假设线性衰减结果为 $x\in[0,1]$，平方后得到 $x^2$：例如 $x=0.5$ 时会从 $0.5$ 降到 $0.25$。这会压低靠近范围边缘处的亮度，并让曲线以零斜率连接到 $0$，从而减弱 `range` 边界处明显的截断感。

这个平方并不是物理定律，而是为了获得更自然的边缘而选择的经验曲线。如果去掉平方，衰减仍然成立，只是从光源中心到 `range` 边界之间会更加明亮，并呈线性过渡。最终的距离衰减为：

$$
attenuation=\frac{attenuation_{range}}{max(d^2,\epsilon)}
$$

CPU 不需要把 `range` 本身交给 GPU，可以预先计算 $\frac{1}{range^2}$。点光源与聚光灯的大部分计算相同，具体实现放在后面的代码实现一节中。

## 聚光灯

![Unity里的聚光灯](/images/posts/srp/PointLightAndSpotLight/image-20260919190707444.png)

聚光灯是一个锥形的光照范围，我们想做到的效果是在边缘不是生硬的直接从要光照变成纯黑，而是要一个过渡，因此我们要内锥角和外锥角的概念。我们先暂定内锥角为外锥角的80%。

设外锥角为 $\alpha$，内锥角为 $\beta$。如果没有单独提供内锥角，也可以暂定 $\beta=0.8\alpha$。

![聚光灯内锥角和外锥角示意图](/images/posts/srp/PointLightAndSpotLight/image-20260919192156493.png)

假设片元所在位置和锥中线的夹角为 $\theta$。当 $\theta<\frac{\beta}{2}$ 时，片元位于内锥中，角度衰减为 $1$；当 $\theta>\frac{\alpha}{2}$ 时，片元位于外锥之外，角度衰减为 $0$；内外锥之间则进行平滑过渡：

$$
attenuation_{spot}=saturate\left(\frac{\cos(\theta)-\cos(\alpha/2)}{\cos(\beta/2)-\cos(\alpha/2)}\right)^2
$$

因为 Unity 的 `spotAngle` 表示完整锥角，所以计算余弦前要先除以 $2$。CPU 将公式中可以预先计算的部分存入 `_OtherLightSpotAngles`，GPU 再通过一次乘加得到内外锥之间的衰减值。

这里的平方作用于 `saturate` 得到的整个角度衰减值。若把平方前的线性结果记为 $x$，那么 $x=0.5$ 时，平方后的光照贡献只有 $0.25$。因此内外锥之间的亮度会更低，灯光看起来更集中在内锥附近，同时外锥边界会更柔和。

这个平方也是用于调整视觉效果的经验曲线，并不是聚光灯计算的必要条件。去掉平方后，内锥与外锥之间就是严格的线性过渡，光照范围会显得更亮、更宽。聚光灯剩余的光照方向、距离衰减和 Lambert 项都与点光源相同。距离衰减的平方与聚光衰减的平方是两次独立操作，最后将两个衰减结果相乘，并不是把最终光照颜色整体平方。

## 代码实现

在这套 SRP 中，点光源和聚光灯都被归为 `OtherLights`，最多支持 4 盏。两种灯使用相同的颜色、位置、方向和聚光角参数数组，区别只在 CPU 写入的数据不同。

### CPU 侧：收集灯光数据

首先在 `Lighting.cs` 中声明 Shader 属性 ID 和对应的数组：

```csharp
// 前向渲染中只有一盏主方向光，点光源和聚光灯都是 OtherLights。
public const int maxOtherLightCount = 4;

public static readonly int otherLightCountId =
    Shader.PropertyToID("_OtherLightCount");
public static readonly int otherLightColorsId =
    Shader.PropertyToID("_OtherLightColors");
public static readonly int otherLightPositionsId =
    Shader.PropertyToID("_OtherLightPositions");
public static readonly int otherLightDirectionsId =
    Shader.PropertyToID("_OtherLightDirections");
public static readonly int otherLightSpotAnglesId =
    Shader.PropertyToID("_OtherLightSpotAngles");

public int otherLightCount;
public readonly Vector4[] otherLightColors =
    new Vector4[maxOtherLightCount];
public readonly Vector4[] otherLightPositions =
    new Vector4[maxOtherLightCount];
public readonly Vector4[] otherLightDirections =
    new Vector4[maxOtherLightCount];
public readonly Vector4[] otherLightSpotAngles =
    new Vector4[maxOtherLightCount];
```

调用 `Setup` 时遍历相机剔除后仍然可见的灯光。颜色直接使用 `finalColor`；位置保存在 `otherLightPositions.xyz`；预先算好的 $1/range^2$ 则放入空闲的 `w` 分量：

```csharp
public void Setup(CullingResults cullingResults)
{
    otherLightCount = 0;

    for (int i = 0; i < cullingResults.visibleLights.Length; i++)
    {
        if (otherLightCount >= maxOtherLightCount)
        {
            break;
        }

        var light = cullingResults.visibleLights[i];

        if (light.lightType == LightType.Point)
        {
            otherLightColors[otherLightCount] = light.finalColor;
            otherLightPositions[otherLightCount] =
                light.localToWorldMatrix.GetColumn(3);

            otherLightPositions[otherLightCount].w =
                1f / Mathf.Max(
                    light.range * light.range,
                    0.0001f
                );

            otherLightDirections[otherLightCount] = Vector4.zero;

            // 与零方向点乘后为 0，再代入 (0, 1) 得到 1。
            otherLightSpotAngles[otherLightCount] =
                new Vector4(0f, 1f, 0f, 0f);

            otherLightCount++;
        }
        else if (light.lightType == LightType.Spot)
        {
            otherLightColors[otherLightCount] = light.finalColor;
            otherLightPositions[otherLightCount] =
                light.localToWorldMatrix.GetColumn(3);

            otherLightPositions[otherLightCount].w =
                1f / Mathf.Max(
                    light.range * light.range,
                    0.0001f
                );

            // Shader 中需要从片元指向光源的锥轴方向。
            otherLightDirections[otherLightCount] =
                -light.localToWorldMatrix.GetColumn(2);

            float outerCos = Mathf.Cos(
                Mathf.Deg2Rad * light.spotAngle * 0.5f
            );
            float innerCos = Mathf.Cos(
                Mathf.Deg2Rad * light.spotAngle * 0.5f * 0.8f
            );

            // 预存 1/(inner-outer) 与 -outer/(inner-outer)。
            float rangeInv = 1f / Mathf.Max(
                innerCos - outerCos,
                0.0001f
            );

            otherLightSpotAngles[otherLightCount] =
                new Vector4(
                    rangeInv,
                    -outerCos * rangeInv,
                    0f,
                    0f
                );

            otherLightCount++;
        }
    }
}
```

这里没有使用 Unity 的 `innerSpotAngle`，而是按照前面的约定，将内锥角近似为外锥角的 $80\%$。

点光源没有方向和锥角，但 GPU 仍会执行同一段聚光衰减代码。点光源的方向设为零向量，`otherLightSpotAngles` 设为 $(0,1,0,0)$，代入 GPU 代码后得到：

$$
saturate(0\times 0+1)^2=1
$$

这样 GPU 不需要根据灯光类型产生分支。

### CPU 侧：通过 RenderGraph 上传数据

`Lighting.Setup` 只负责整理 CPU 数据。在 `CameraRenderer` 中，还需要添加一个 RenderGraph Pass，将数据设为全局 Shader 参数。

Pass Data 负责把当前帧的数据带进 RenderGraph 的执行阶段：

```csharp
private class LightingPassData
{
    public Vector4 color;
    public Vector4 direction;
    public int otherLightCount;
    public Vector4[] otherColors;
    public Vector4[] otherPositions;
    public Vector4[] otherDirections;
    public Vector4[] otherSpotAngles;
}
```

然后在 `AddLightingSetupPass` 中上传：

```csharp
private void AddLightingSetupPass(RenderGraph graph)
{
    using var builder = graph.AddUnsafePass(
        "Setup Lighting",
        out LightingPassData data
    );

    data.color = _lighting.dirLightColor;
    data.direction = _lighting.dirLightDirection;
    data.otherLightCount = _lighting.otherLightCount;
    data.otherColors = _lighting.otherLightColors;
    data.otherPositions = _lighting.otherLightPositions;
    data.otherDirections = _lighting.otherLightDirections;
    data.otherSpotAngles = _lighting.otherLightSpotAngles;

    // 改写全局状态必须声明，否则 RenderGraph 会报错。
    builder.AllowGlobalStateModification(true);

    // 防止这个没有纹理输出的 Pass 被裁剪。
    builder.AllowPassCulling(false);

    builder.SetRenderFunc(static (
        LightingPassData data,
        UnsafeGraphContext context
    ) =>
    {
        var cmd = context.cmd;

        cmd.SetGlobalVector(
            Lighting.dirLightColorId,
            data.color
        );
        cmd.SetGlobalVector(
            Lighting.dirLightDirectionId,
            data.direction
        );
        cmd.SetGlobalInteger(
            Lighting.otherLightCountId,
            data.otherLightCount
        );

        if (data.otherLightCount > 0)
        {
            cmd.SetGlobalVectorArray(
                Lighting.otherLightPositionsId,
                data.otherPositions
            );
            cmd.SetGlobalVectorArray(
                Lighting.otherLightDirectionsId,
                data.otherDirections
            );
            cmd.SetGlobalVectorArray(
                Lighting.otherLightSpotAnglesId,
                data.otherSpotAngles
            );
            cmd.SetGlobalVectorArray(
                Lighting.otherLightColorsId,
                data.otherColors
            );
        }
    });
}
```

`AllowGlobalStateModification(true)` 和 `AllowPassCulling(false)` 都不能省略：前者告诉 RenderGraph 这个 Pass 会改写全局状态，后者防止这个没有纹理输出的 Pass 被当成无用 Pass 删除。

### GPU 侧：接收灯光数据

`LightingInput.hlsl` 中的字段名称、类型和数组长度必须与 CPU 侧完全一致：

```hlsl
#pragma once
#include "Packages/com.unity.render-pipelines.core/ShaderLibrary/Common.hlsl"

CBUFFER_START(_CustomLight)
    float4 _DirectionalLightColor;
    float4 _DirectionalLightDirection;

    int _OtherLightCount;
    float4 _OtherLightColors[4];
    float4 _OtherLightPositions[4];
    float4 _OtherLightDirections[4];
    float4 _OtherLightSpotAngles[4];
CBUFFER_END
```

其中，`_OtherLightPositions.w` 存储 $1/range^2$；`_OtherLightSpotAngles.xy` 存储 CPU 预先算好的两个聚光衰减参数，GPU 直接将它们代入乘加运算。

### GPU 侧：计算光照

点光源和聚光灯共用 `GetOtherLighting`。先计算片元指向光源的方向和距离衰减，再计算聚光衰减，最后乘上 Lambert 项：

```hlsl
#pragma once
#include "LightingInput.hlsl"

float DistanceAttenuation(float distSqr, float invRangeSqr)
{
    float rangeAtten = saturate(
        1 - distSqr * invRangeSqr
    );
    rangeAtten *= rangeAtten;

    return rangeAtten / max(distSqr, 0.0001);
}

float3 GetOtherLighting(
    float3 baseColor,
    float3 normalWS,
    float3 positionWS
)
{
    float3 sum = 0;

    for (int i = 0; i < _OtherLightCount; ++i)
    {
        float3 toLight =
            _OtherLightPositions[i].xyz - positionWS;
        float distSqr = dot(toLight, toLight);
        float3 lightDir =
            toLight * rsqrt(max(distSqr, 0.0001));

        float atten = DistanceAttenuation(
            distSqr,
            _OtherLightPositions[i].w
        );

        // 不 normalize：点光源在这个数组中存储的是零向量。
        float spotCos = dot(
            lightDir,
            _OtherLightDirections[i].xyz
        );
        float spotAtten = saturate(
            spotCos * _OtherLightSpotAngles[i].x
                + _OtherLightSpotAngles[i].y
        );
        spotAtten *= spotAtten;

        float ndotl = saturate(dot(normalWS, lightDir));

        sum += baseColor
            * _OtherLightColors[i].rgb
            * (ndotl * atten * spotAtten);
    }

    return sum;
}
```

`DistanceAttenuation` 中的 `rangeAtten` 负责让灯光在 `range` 处平滑归零，除以 `distSqr` 则实现平方反比衰减。聚光灯还会乘上 `spotAtten`，而点光源通过 CPU 预设的参数使这一项恒为 $1$。

最后在 Lambert 片元着色器中，把 Other Lights 的结果累加到主方向光结果上：

```hlsl
float3 ndotl = saturate(dot(normalWS, lightDir));
float3 color = base.rgb * lightColor * ndotl;

color += GetOtherLighting(
    base.rgb,
    normalWS,
    input.positionWS
);

return float4(color, base.a);
```
