# 本地 CDN 运行方式

这些文件是用户先前提供并随技能一起保存的原始资源，位于技能的 `assets/cdn/`。生成模板时选择与目标项目相同的一套技术栈，把相应文件复制到本次 HTML 所在目录的 `cdn/` 下。这里的“CDN”是本地离线资源目录，不访问外部网络，也不再依赖最初提供资源时的磁盘路径。

`assets/cdn/manifest.json` 是资源清单，记录每个文件的大小、SHA-256、所属技术栈和实测版本。必须通过 `copy_cdn_assets.py` 复制；脚本在复制前后验证哈希，防止本机其他同名文件或后续下载版本替换用户提供的资源。`validate_cdn_html.py` 再核对交付目录里的文件与清单完全一致。

## 技术栈选择

- 从 `package.json`、锁文件、入口代码、既有页面和设计文档判断框架、组件库及主版本。项目代码证据优于文件名推测。
- Ant Design 5 默认使用 `antd5`（本地 bundle 实测为 5.28.0）；只有项目明确需要较早的 Ant Design 5 行为时才使用 `antd5-legacy`（本地 `antd.min.js` 实测为 5.12.8）。Vue 3 + Element Plus 使用 `element-plus`（实测为 2.5.6）。当前资源不包含 Ant Design 4；目标为 Ant Design 4 时应使用项目提供的可运行资源，不能把 `antd.min.js` 误当成 Ant Design 4。不要同时加载两套 Ant Design，也不要在同一模板集中混用 React 和 Vue。
- 若用户只提供设计文档而没有技术栈，设计文档明确写出组件库时按其选择；仍无法确定时说明缺少的证据，不要擅自选一个组件库并声称来自目标系统。

使用复制脚本：

```text
python scripts/copy_cdn_assets.py --stack antd5 --output-dir <html-output-directory>
```

## React + Ant Design 5.12.8 兼容档

仅在项目版本需要时选择 `antd5-legacy`。

样式：

```html
<link rel="stylesheet" href="./cdn/antd.min.css" />
```

脚本必须依次加载：

```html
<script src="./cdn/react.production.min.js"></script>
<script src="./cdn/react-dom.production.min.js"></script>
<script src="./cdn/dayjs.min.js"></script>
<script src="./cdn/antd.min.js"></script>
<script src="./cdn/babel.min.js"></script>
<script type="text/babel">/* React 业务组件 */</script>
```

页面必须有 `#root`，由 `ReactDOM.createRoot` 挂载 React 组件；从全局 `antd` 解构并实际使用 `Form`、`Input`、`Select`、`Table`、`Modal`、`Drawer`、`Button` 等当前页面需要的组件。Modal/Drawer 使用 Ant Design 5 的 `open` 属性。根组件包在 `antd.App` 中。本地资源未提供 `@ant-design/icons` UMD 包，独立 HTML 使用清楚的文字按钮，不额外引入外部图标资源。

## React + Ant Design 5.28.0 默认档

样式：

```html
<link rel="stylesheet" href="./cdn/reset.css" />
```

脚本必须依次加载：

```html
<script src="./cdn/react.production.min.js"></script>
<script src="./cdn/react-dom.production.min.js"></script>
<script src="./cdn/dayjs.min.js"></script>
<script src="./cdn/antd5.min.js"></script>
<script src="./cdn/babel.min.js"></script>
<script type="text/babel">/* React 业务组件 */</script>
```

页面必须有 `#root`，使用 `ReactDOM.createRoot` 挂载。根组件包在 `antd.App` 中，从全局 `antd` 使用当前页面所需组件。Modal/Drawer 使用 `open`；需要消息提示时从 `App.useApp()` 获取 message。使用 `ConfigProvider` 将 design.md 解析出的主题令牌映射到 Ant Design token，再用页面 CSS 完成组件级差异。

## Vue 3 + Element Plus

样式：

```html
<link rel="stylesheet" href="./cdn/element-plus/dist/index.css" />
```

脚本必须依次加载：

```html
<script src="./cdn/vue.min.js"></script>
<script src="./cdn/element-plus/dist/index.full.min.js"></script>
<script>/* Vue 应用 */</script>
```

页面必须有 `#app`，使用 `Vue.createApp` 创建应用、`app.use(ElementPlus)` 注册组件库并挂载。模板主体使用 `el-form`、`el-table`、`el-dialog`、`el-drawer` 等对应组件。将 design.md 令牌映射为 `--el-*` 主题变量与系统自定义 CSS；不要用静态 `<input>`、`<table>` 代替可用的 Element Plus 组件。

## 交付文件的运行要求

- 本次清单中的每个 HTML 都包含挂载节点和应用初始化代码，并能从文件系统单独打开。文件数量和名称由用户选择或自定义描述决定。
- 允许把业务初始化提取成同目录脚本，但单独打开任一页面时引用必须完整。每页只加载所选栈必需的资源，加载失败时不能静默退化成另一套手写界面。
- 对本次交付的全部 HTML 实际路径运行以下命令。每个脚本均支持一个或多个路径，文件名不受限制：

```text
python scripts/validate_cdn_html.py <HTML路径> [其他HTML路径...]
python scripts/validate_html_syntax.py <HTML路径> [其他HTML路径...]
```

第一个脚本检查资源存在、依赖顺序和组件库实际使用标记。第二个脚本检查外层 HTML 标签结构，并使用技能内置 Babel 对内联 JavaScript/JSX 做编译级语法校验但不执行代码；它用于提前拦截多余括号、未闭合 JSX、损坏的表达式等问题。两个脚本通过后，仍需在浏览器检查运行时错误、真实交互和组件视觉。
