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
- **Load Image From URL Node** - 从URL加载图像节点
  - 支持从网络URL直接加载图像
  - 自动格式检测和转换
  - 支持多种图像格式（JPEG、PNG、WebP等）
  - 内置错误处理和超时控制

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

### Load Image From URL Node
```python
# 从URL加载图像
url = "https://example.com/image.jpg"
# 节点会自动下载并转换为ComfyUI可用的图像格式
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
