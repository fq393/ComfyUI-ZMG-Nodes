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
├── nodes/                      # 节点实现目录
│   ├── __init__.py             # 节点包初始化文件
│   ├── ApiRequestNode.py       # API请求节点
│   ├── JsonParserNode.py       # JSON解析节点
│   ├── LoadImageFromUrlNode.py # 从URL加载图像节点
│   ├── EmptyImageNode.py       # 增强型空图像节点
│   └── config/                 # 配置文件目录
│       └── NodeCategory.py     # 节点分类配置
└── web/                        # Web资源目录
    ├── upload.js               # 上传功能脚本
    └── utils.js                # 工具函数脚本
```

## 🔧 最新更新

### v1.3.0 (2024-12-19)
- **重构LoadImageFromUrlNode以兼容art-venture**：完全重写节点以匹配comfyui-art-venture项目的LoadImageFromUrl功能
- **统一输入参数结构**：将`urls`参数改为`image`，移除`upload`和`timeout`参数，与art-venture保持一致
- **集成核心功能函数**：引入`load_images_from_url`、`pil2tensor`、`tensor2pil`等核心函数
- **增强URL支持**：完整支持data URI、file协议、ComfyUI内部路径等多种格式
- **优化返回结构**：返回包含UI预览的字典结构，提供更好的用户体验
- **改进错误处理**：采用art-venture的优雅错误处理机制
- **完善预览功能**：添加图像预览生成，支持透明度显示
- **保持向后兼容**：确保现有工作流程不受影响的同时提供更强大的功能

### v1.2.2 (2024-12-19)
- **修复LoadImageFromUrlNode加载问题**：解决了节点无法正常加载的关键问题
- **移除已删除参数的引用**：清理了对已删除的`width`、`height`、`color`参数的引用
- **重构空图像创建逻辑**：使用PIL.Image.new()直接创建空图像，替代已删除的`_create_empty_image`方法
- **优化错误处理**：改进了空URL情况下的处理逻辑，确保返回正确的空图像
- **完善测试验证**：添加了完整的功能测试脚本，确保所有修复都能正常工作
- **提升代码稳定性**：通过语法检查和功能测试，确保节点在ComfyUI中能够正常加载和运行

### v1.2.1 (2024-12-19)
- **UI界面优化**：移除了`width`、`height`、`color`参数，简化用户界面
- **新增文件上传功能**：添加了`upload`参数，支持直接上传图像文件
- **代码结构优化**：移除了`_create_empty_image`方法，简化代码结构
- **改进输入验证**：优化了URL和文件上传的验证逻辑
- **提升用户体验**：界面更加简洁，操作更加直观

### v1.2.0 (2024-12-19)
- **大幅增强LoadImageFromUrlNode**：重构为LoadImagesFromUrlNode，支持批量图像处理
- **新增多种URL格式支持**：Data URI、File协议、ComfyUI内部路径、本地文件路径
- **批量处理功能**：支持多行URL输入，一次性加载多张图像
- **Alpha通道处理**：可选择保留或移除图像的透明通道，自动提取遮罩
- **灵活输出模式**：支持列表输出和批量输出两种模式
- **增强错误处理**：详细的错误信息、网络状态检查、超时处理
- **EXIF自动旋转**：自动处理图像的EXIF旋转信息
- **输入验证机制**：完整的URL和参数验证，提升用户体验
- **向后兼容性**：保持与旧版本的兼容性，平滑升级

### v1.1.2 (2024-12-19)
- **优化项目结构**：移除了 `OldPhotoColorizationNode.py` 节点，简化项目复杂度
- **简化依赖配置**：更新 `requirements.txt`，移除不必要的依赖包（opencv-python、modelscope、imageio-ffmpeg）
- **保留核心功能**：项目现在专注于4个核心节点：API请求、JSON解析、URL图像加载和空图像处理
- **优化依赖管理**：仅保留必要的依赖包（requests、Pillow、numpy、torch）
- **更新文档**：同步更新README.md，反映当前的项目状态和文件结构

### v1.1.1 (2024-12-19)
- **移除复杂节点**：删除 `OldPhotoColorizationNode.py` 及其相关配置
- **修复导入路径**：解决节点导入时的路径问题
- **优化配置文件**：更新 `__init__.py` 中的节点配置映射

### v1.1.0 (2024-12-19)
- **修复导入错误**：解决了 `ApiRequestNode.py` 中的 `ModuleNotFoundError` 问题
- **优化项目结构**：添加了 `nodes/__init__.py` 文件，使节点目录成为标准Python包
- **改进错误处理**：所有节点现在都有更好的错误处理和类型定义
- **完善测试**：添加了完整的导入测试脚本，确保所有节点都能正常加载
- **更新文档**：修正了项目结构说明，反映实际的目录布局

## 🔧 使用说明

### API Request Node
```python
# 基本GET请求
url = "https://api.example.com/data"
method = "GET"

# POST请求with JSON数据
url = "https://api.example.com/submit"
method = "POST"
data = '{"key": "value"}'
```

### JSON Parser Node
```python
# 解析嵌套JSON
json_data = '{"user": {"name": "张三", "age": 30}}'
json_path = "user.name"  # 输出: "张三"

# 数组索引
json_data = '{"items": ["apple", "banana", "orange"]}'
json_path = "items[1]"  # 输出: "banana"
```

### Load Images From URL Node
```python
# 单个网络图像
urls = "https://example.com/image.jpg"

# 多个图像（多行输入）
urls = """https://example.com/image1.jpg
https://example.com/image2.png
/path/to/local/image.jpg"""

# Data URI格式
urls = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

# 本地文件路径
urls = "/Users/username/Pictures/photo.jpg"

# File协议
urls = "file:///Users/username/Pictures/photo.jpg"

# ComfyUI内部路径
urls = "/view?filename=image.png&subfolder=&type=input"

# 高级配置
keep_alpha_channel = True    # 保留Alpha通道
output_mode = False         # 列表输出模式
timeout = 30               # 30秒超时
```

### Empty Image Node
```python
# 基本空图像输出
output_mode = "none"  # 不输出任何内容

# 生成占位符图像
output_mode = "placeholder"
width = 512
height = 512
color = "#FF0000"  # 红色占位符

# 直通模式
passthrough = True  # 将输入直接传递到输出
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
