# 露天台阶爆破效果综合评价系统

## 项目简介

露天台阶爆破效果综合评价系统是一个基于Rio GUI框架开发的专业评价工具，用于对露天矿山台阶爆破效果进行科学、客观的综合评价。系统采用多指标评价体系，支持多种权重计算方法，为爆破工程师提供决策支持。

## 主要功能

- **指标体系管理**：支持爆破质量、安全、经济三大类指标
- **权重计算**：支持等权重、专家打分、AHP层次分析法
- **综合评价**：基于加权综合评价模型计算总体得分
- **报告生成**：自动生成详细的评价报告
- **数据管理**：支持数据导入导出和历史记录

## 技术架构

- **前端框架**：Rio UI
- **后端语言**：Python 3.8+
- **数据处理**：NumPy, Pandas, SciPy
- **配置管理**：ConfigParser
- **日志系统**：Loguru
- **测试框架**：Pytest

## 项目结构

```
baopoapp1/
├── main.py                 # 应用入口
├── requirements.txt        # 依赖包列表
├── README.md              # 项目说明
├── config/                # 配置文件
│   ├── settings.ini       # 应用配置
│   └── indicators.json    # 指标定义
├── src/                   # 源代码
│   ├── app.py            # 主应用类
│   ├── controllers/      # 控制器
│   ├── models/           # 数据模型
│   ├── views/            # 视图组件
│   └── utils/            # 工具模块
├── tests/                # 测试代码
├── logs/                 # 日志文件
├── data/                 # 数据文件
└── reports/              # 报告输出
```

## 快速开始

### 环境要求

- Python 3.8 或更高版本
- Windows 10/11 或 Linux

### 安装步骤

1. 克隆项目
```bash
git clone <repository-url>
cd baopoapp1
```

2. 创建虚拟环境
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# 或
source venv/bin/activate  # Linux/Mac
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 运行应用
```bash
python demo_app.py
```

5. 打开浏览器访问 `http://localhost:8080`

## 使用指南

### 1. 指标选择
- 在第一步中选择需要评价的指标
- 系统提供爆破质量、安全、经济三大类指标
- 可根据实际需要选择相关指标

### 2. 权重设置
- 选择权重计算方法：等权重、专家打分或AHP
- 根据选择的方法输入相应参数
- 系统自动计算并显示权重结果

### 3. 范围设置
- 为每个选中的指标设置评价范围
- 包括最优值、最差值等参数
- 支持正向指标和反向指标

### 4. 实测值输入
- 输入各指标的实际测量值
- 系统提供数据验证功能
- 支持批量导入数据

### 5. 综合评价
- 执行综合评价计算
- 查看各指标得分和总体评价结果
- 生成详细的评价报告

## 开发指南

### 代码规范

- 使用Black进行代码格式化
- 使用Flake8进行代码检查
- 使用MyPy进行类型检查
- 遵循PEP 8编码规范

### 测试

```bash
# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=src

# 运行特定测试文件
pytest tests/test_controller.py
```

### 添加新指标

1. 在 `config/indicators.json` 中添加指标定义
2. 更新相关的数据模型
3. 添加对应的测试用例

### 扩展权重计算方法

1. 在 `src/controllers/evaluation_controller.py` 中添加新方法
2. 更新视图组件以支持新方法
3. 添加相应的测试

## 配置说明

### 应用配置 (config/settings.ini)

- `[App]`：应用基本信息
- `[Server]`：服务器配置
- `[Evaluation]`：评价相关配置
- `[UI]`：界面配置
- `[Logging]`：日志配置

### 指标配置 (config/indicators.json)

定义了系统支持的所有评价指标，包括：
- 指标ID和名称
- 单位和描述
- 指标类型（正向/反向）
- 所属类别

## 常见问题

### Q: 如何修改默认端口？
A: 在 `config/settings.ini` 中修改 `[Server]` 部分的 `Port` 值。

### Q: 如何添加自定义指标？
A: 编辑 `config/indicators.json` 文件，按照现有格式添加新指标。

### Q: 权重计算结果不合理怎么办？
A: 检查输入的判断矩阵是否满足一致性要求，或尝试其他权重计算方法。

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

- 项目维护者：[您的姓名]
- 邮箱：[您的邮箱]
- 项目链接：[项目地址]

## 更新日志

### v1.0.0 (2024-01-XX)
- 初始版本发布
- 实现基本的综合评价功能
- 支持三种权重计算方法
- 提供完整的用户界面