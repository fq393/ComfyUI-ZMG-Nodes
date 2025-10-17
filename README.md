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



### 🔧 数据处理节点 (ZMGNodes/data)
- **JSON Parser Node** - 高级JSON解析节点
  - 支持复杂的JSON路径解析
  - 多种输出格式（字符串、JSON、格式化JSON）
  - 数组索引和嵌套对象支持
  - 强大的错误处理

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
│   ├── TextToImageNode.py      # 文本转图像节点
│   ├── SaveVideoRGBA.py        # RGBA视频保存节点
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
