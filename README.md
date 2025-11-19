# ComfyUI-ZMG-Nodes

一个功能丰富的ComfyUI自定义节点集合，提供多种实用工具和增强功能。

## 📋 简介

ComfyUI-ZMG-Nodes是一个专为ComfyUI设计的自定义节点插件包，包含多个实用的节点，旨在提升工作流的效率和功能性。所有节点都经过优化，具有完善的错误处理、类型注解和详细的文档说明。

## 🚀 功能特性

- **完整的类型注解**：所有代码都包含详细的类型注解，提高代码可读性和维护性
- **强大的错误处理**：每个节点都具有完善的异常处理机制
- **详细的文档**：所有函数和类都有完整的中文文档说明
- **高性能优化**：代码结构经过优化，提供更好的性能表现
- **统一的日志系统**：集成彩色日志输出，便于调试和监控
- **统一的分类系统**：所有节点都使用`ZMGNodes/`前缀进行分类，便于在ComfyUI中查找和管理

## 📦 节点列表

所有节点都按照功能分类，在ComfyUI中以`ZMGNodes/`前缀显示：
- `ZMGNodes/network` - 网络相关节点
- `ZMGNodes/data` - 数据处理节点  
- `ZMGNodes/image` - 图像处理节点
- `ZMGNodes/utils` - 工具类节点
- `ZMGNodes/audio` - 音频处理节点

### 🌐 网络请求节点 (ZMGNodes/network)
- **API Request Node** - 强大的HTTP请求节点
  - 支持GET、POST、PUT、DELETE方法
  - 自动JSON解析和错误处理
  - URL验证和超时控制
  - 自定义请求头支持

- **Elasticsearch Update Node** - 专业的Elasticsearch更新节点
  - **多种操作类型**：支持update_by_query、update、delete_by_query操作
  - **灵活查询条件**：支持复杂的Elasticsearch查询语法
  - **脚本更新**：支持自定义更新脚本和参数
  - **认证支持**：支持Basic认证和其他认证方式
  - **智能URL构建**：自动构建正确的Elasticsearch API端点
  - **详细统计**：返回受影响的文档数量和详细响应信息
  - **错误处理**：完善的错误处理和超时机制
  - **格式化输出**：自动格式化JSON响应，便于阅读和调试



### 🔧 数据处理节点 (ZMGNodes/data)
- **JSON Parser Node** - 高级JSON解析节点
  - 支持复杂的JSON路径解析
  - 多种输出格式（字符串、JSON、格式化JSON）
  - 数组索引和嵌套对象支持
  - 强大的错误处理

- **JSON Builder Node** - JSON构建器节点
  - **多键值对输入**：支持5个key-value对的输入配置
  - **智能类型识别**：自动识别字符串、数字、布尔值、JSON对象等数据类型
  - **JSON对象合并**：支持将子JSON对象合并到父级指定key中
  - **灵活合并模式**：可合并到指定key或直接合并到根级别
  - **格式化输出**：提供压缩和格式化两种JSON输出格式
  - **排序选项**：支持按key排序输出
  - **错误处理**：完善的JSON解析和构建错误处理机制
  - **调试支持**：提供详细的合并过程调试信息
  - **数据传递**：支持passthrough数据流传递

- **Remove Empty Lines Node** - 去除空行节点
  - **多种处理模式**：严格模式、宽松模式、仅修剪模式
  - **智能空行检测**：区分完全空行和仅包含空白字符的行
  - **段落保护**：可选择保留单个空行用于段落分隔
  - **空白处理**：自动去除行首尾空白字符
  - **详细统计**：提供处理前后的详细统计信息
  - **大文本支持**：高效处理大量文本内容
  - **灵活配置**：多种参数组合满足不同需求

### 📝 文本处理节点 (ZMGNodes/text)
- **Multiline Prompt Node** - 多行提示词处理节点
  - **多行文本输入**：支持多行提示词的输入和处理
  - **行数统计**：自动统计并输出文本总行数
  - **多种分隔符**：支持换行符、逗号、分号、空格和自定义分隔符
  - **行号添加**：可选择为每行添加行号，支持多种行号格式
  - **智能处理**：自动去除空行和首尾空白字符
  - **格式化输出**：提供格式化后的文本和原始文本输出
  - **详细统计**：显示处理统计信息和行数详情
  - **🆕 COMBO输出**：新增行列表COMBO输出，可用于下拉选择单个行内容
  - **索引功能**：支持直接获取指定行的单条数据
  - **灵活配置**：多种处理选项满足不同的文本格式需求

### 🖼️ 图像处理节点 (ZMGNodes/image)
- **Load Images From URL Node** - 增强型URL图像加载节点
  - **多种URL格式支持**：HTTP/HTTPS、本地文件路径、File协议、Data URI、ComfyUI内部路径
  - **批量处理**：支持多行URL输入，一次性加载多张图像
  - **Alpha通道处理**：可选择保留或移除图像的透明通道
  - **灵活输出模式**：支持列表输出和批量输出两种模式
  - **智能错误处理**：详细的错误信息和状态反馈
  - **EXIF自动旋转**：自动处理图像的EXIF旋转信息
  - **遮罩提取**：自动从Alpha通道提取遮罩信息
  - **自定义超时**：可配置网络请求超时时间
  - **输入验证**：完整的URL和参数验证机制

- **Text To Image Node** - 智能文本转图像节点
  - **智能文本换行**：自动处理长文本，支持按单词和字符级别的智能换行
  - **宽度限制控制**：图片最大宽度限制为1024像素，确保输出尺寸合理
  - **换行符保持**：完整保留文本中的原有换行符，在图片中正确显示
  - **多语言支持**：完整支持中文、英文、数字和特殊字符的渲染
  - **自定义字体**：支持从fonts目录选择字体文件（.ttf、.ttc、.otf格式）
  - **颜色自定义**：支持文本颜色和背景颜色的自由配置（十六进制格式）
  - **动态画布**：根据文本内容和换行情况自动调整画布大小
  - **行间距控制**：可调节行间距倍数，优化文本显示效果
  - **边距设置**：可自定义文本边距，确保文本不贴边显示

- **Save Video RGBA Node** - 简化的RGBA视频保存节点
  - **多格式支持**：支持MP4、WebM、MOV等主流视频容器格式
  - **智能编解码器选择**：根据选择的格式自动选择最佳编解码器
    - MOV格式：有alpha通道时使用ProRes，无alpha时使用H264
    - WebM格式：使用VP9编解码器
    - MP4格式：使用H264编解码器
  - **Alpha通道处理**：完整支持透明通道的保存和处理
  - **智能格式选择**：auto模式根据是否有alpha通道自动选择最佳格式
  - **音频支持**：可选的音频轨道添加功能
  - **预览模式**：支持预览模式快速查看效果
  - **文件名自定义**：支持自定义文件名前缀和格式化
  - **简化界面**：移除复杂的编解码器选择，专注于格式选择
  - **性能优化**：高效的视频编码和内存管理
  - **错误处理**：完善的错误处理和状态反馈机制

- **Combine Image+Audio → Video** - 图片与音频合成视频节点
  - **视频输出**：将`IMAGE`帧序列与可选`AUDIO`轨道合成为视频文件
  - **编码与容器**：支持 `video/h264-mp4`、`video/vp9-webm`、`video/prores-mov`
  - **像素格式**：`yuv420p`（无透明）、`yuva420p/yuva444p10le`（支持透明）
  - **质量控制**：`crf` 参数（数值越小质量越高，体积越大）
  - **音频混流**：自动按容器选择音频编码（MP4/MOV→AAC，WEBM→Opus），可选择`trim_to_audio`
  - **播放增强**：支持`pingpong`乒乓播放以延长时长
  - **保存位置**：`save_output` 控制保存到`output`或`temp`
  - **命名规则**：输出文件名包含计数与时间戳，避免重名，例如 `AnimateDiff_00001_20251119_103522_123456.mp4`
  - **输出类型**：返回单一 `VIDEO` 输出，兼容 `IO.VIDEO` 类型节点连接
  - **使用示例**：
    1. 用 `Text To Image` 或其它节点得到 `IMAGE`
    2. 用 `Load Audio From URL` 得到 `AUDIO`
    3. 连接到 `Combine Image+Audio → Video`，设置 `frame_rate=24`、`format=video/h264-mp4`、`crf=19`
    4. 输出即为 `VIDEO`，可直接接到后续视频处理/上传节点

  **参数说明**
  - `images`: 输入帧序列，形状 `B x H x W x C`，`C=3/4`
  - `frame_rate`: 视频帧率，常用 `24/25/30`
  - `filename_prefix`: 文件名前缀，系统会自动追加计数与时间戳
  - `format`: 视频容器与编码，`mp4(H.264)`、`webm(VP9)`、`mov(ProRes)`
  - `pix_fmt`: 像素格式，`yuv420p`（无透明）、`yuva420p/yuva444p10le`（有透明）
  - `crf`: 质量系数，越小越清晰、体积越大，建议 `18–23`
  - `save_metadata`: 写入创建时间等元数据
  - `trim_to_audio`: 按音频长度裁剪；关闭则为视频补齐静音
  - `pingpong`: 乒乓播放，延长视频时长
  - `save_output`: 保存到 `output`；关闭保存到 `temp`
 
### 🔊 音频处理节点 (ZMGNodes/audio)
- **Load Audio From URL Node** - URL音频加载节点
  - **多源支持**：HTTP/HTTPS、file://、Data URI、ComfyUI内部路径
  - **下载到INPUT**：直接下载到ComfyUI的`input`目录
  - **输出AUDIO**：同时输出AUDIO字典（`waveform`、`sample_rate`），仅解码为PCM，不重新编码
  - **参数说明**：
    - `audio`：多行音频URL输入；支持 `http/https`、`file://`、`data:audio`、`/view?`；取首个有效URL下载
  - **输出说明**：
    - `audio`：AUDIO字典（`waveform`、`sample_rate`）
    - `file_path`：保存到`input`目录的完整路径
    - `saved`：是否保存成功
    - `has_audio`：是否存在有效音频（True/False）

### ☁️ 云存储节点 (ZMGNodes/cloud)
- **OSS Upload Node** - 阿里云OSS上传节点
  - **任意类型输入**：支持图片、视频、音频、文本等任意类型数据上传
  - **类型匹配优化**：使用AlwaysEqualProxy解决ComfyUI类型匹配问题，完美兼容AUDIO等特殊类型
  - **智能类型检测**：自动识别输入数据类型并设置正确的MIME类型
  - **标准化输出格式**：
    - 音频数据：自动转换为MP3格式（需要pydub库支持）
    - 单张图片：自动转换为PNG格式
    - 多张图片：自动合成为MP4视频格式
    - 文本数据：保存为UTF-8编码的文本文件
    - 字节数据：直接上传二进制文件
    - JSON数据：格式化保存为JSON文件
  - **增强的视频合成功能**：
    - **FFmpeg优先策略**：优先使用FFmpeg进行视频合成，提供更好的编码器兼容性
    - **智能编码器回退**：FFmpeg不可用时自动回退到OpenCV方法
    - **多编码器支持**：支持H.264、MPEG-4、Xvid、MJPEG等多种编码器
    - **尺寸自动调整**：确保视频尺寸为偶数，满足H.264编码要求
    - **兼容性优化**：使用baseline profile和合适的质量设置提高播放兼容性
    - **错误恢复机制**：编码失败时自动尝试更兼容的编码参数
  - **灵活配置**：支持自定义OSS配置（Access Key、Secret Key、端点等）
  - **智能路径生成**：基于时间戳和哈希值生成唯一文件路径
  - **自定义域名**：支持自定义访问域名和基础路径
  - **详细反馈**：提供完整的上传结果信息和错误处理
  - **上传开关**：可选择性启用/禁用上传功能
  - **多重输出**：返回文件URL、路径、大小、状态等详细信息

### 🔧 工具类节点 (ZMGNodes/utils)
- **Empty Image Node** - 增强型空图像节点
  - 支持多种输出模式（无输出、空张量、占位符图像）
  - 可自定义占位符图像尺寸和颜色
  - 支持直通模式和动态类型处理
  - 灵活的输入输出配置，适用于复杂工作流

## 🛠️ 安装方法

1. 克隆仓库到ComfyUI的custom_nodes目录：
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/fq393/ComfyUI-ZMG-Nodes.git
```

2. 安装依赖（如果需要）：
```bash
cd ComfyUI-ZMG-Nodes
pip install -r requirements.txt
```

3. 重启ComfyUI

## 📁 项目结构

```
    ComfyUI-ZMG-Nodes/
├── __init__.py                 # 主入口文件
├── README.md                   # 项目文档
├── requirements.txt            # 依赖包列表
├── fonts/                      # 字体文件目录
│   └── Songti.ttc              # 宋体字体文件
├── nodes/                      # 节点实现目录
│   ├── __init__.py             # 节点包初始化文件
│   ├── ApiRequestNode.py       # API请求节点
│   ├── JsonParserNode.py       # JSON解析节点
│   ├── LoadImageFromUrlNode.py # 从URL加载图像节点
│   ├── LoadAudioFromUrlNode.py # 从URL加载音频节点
│   ├── TextToImageNode.py      # 文本转图像节点
│   ├── SaveVideoRGBA.py        # RGBA视频保存节点
│   ├── CombineImageAudioToVideoNode.py # 图片+音频合成视频节点
│   ├── EmptyImageNode.py       # 增强型空图像节点
│   └── config/                 # 配置文件目录
│       └── NodeCategory.py     # 节点分类配置
└── web/                        # Web资源目录
    ├── text-switch-case.js     # 文本大小写切换脚本
    ├── upload.js               # 上传功能脚本
    └── utils.js                # 工具函数脚本
```


## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) - 强大的AI图像生成界面
- [ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite) - 视频处理参考
- [ModelScope](https://modelscope.cn/) - AI模型服务

## 📞 联系方式

- GitHub: [@fq393](https://github.com/fq393)
- 项目链接: [https://github.com/fq393/ComfyUI-ZMG-Nodes](https://github.com/fq393/ComfyUI-ZMG-Nodes)
