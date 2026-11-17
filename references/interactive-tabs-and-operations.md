# Tabs 与表格操作列

## Tabs 必须有真实状态

Tabs 是导航和内容切换组件，不是装饰性标题。每个 Tab 必须有对应内容；点击后同时更新当前项视觉、可访问状态和面板内容。不得使用空链接、只写 `active` 类、固定 `activeKey` 或固定 `model-value` 造成看似可点但无法切换。

### React + Ant Design

简单页面优先使用非受控 Tabs，让组件自行维护状态：

```jsx
<Tabs
  defaultActiveKey="all"
  items={[
    { key: "all", label: "全部", children: <AllRecords /> },
    { key: "pending", label: "待处理", children: <PendingRecords /> },
  ]}
/>
```

当切换会联动筛选、请求或其他区域时才使用受控模式，并同时提供状态更新：

```jsx
const [activeTab, setActiveTab] = React.useState("all");
<Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
```

不要写 `<Tabs activeKey="all" ... />` 而没有 `onChange`。若 design.md 将页级 Tabs 定义为自建导航，仍应使用 `useState` 更新 `aria-selected`、`tabIndex` 与面板显隐；支持鼠标点击，键盘聚焦可达。

### Vue + Element Plus

使用可写的响应式值绑定 `v-model`：

```html
<el-tabs v-model="activeTab">
  <el-tab-pane label="全部" name="all"><all-records /></el-tab-pane>
  <el-tab-pane label="待处理" name="pending"><pending-records /></el-tab-pane>
</el-tabs>
```

```js
const activeTab = Vue.ref("all");
```

不要使用固定 `model-value="all"`。页级自建 Tabs 同样需要响应式状态和对应内容切换。

### Tabs 浏览器验收

1. 记录默认 Tab 的文本、`aria-selected` 和可见面板。
2. 点击第二个 Tab；确认第二项成为选中，默认项取消选中，原面板隐藏，新面板可见且内容不同。
3. 再切回默认项，确认状态可逆且输入值是否保留符合业务设定。
4. 查看控制台；修复运行错误和组件警告。仅静态阅读 JSX/Vue 模板不能代替这一步。

## 操作列先服从目标系统

从 design.md 的 Table、Operation Column、Button、Interaction 章节提取以下规则后再编码：固定位置、列宽、文字/按钮形态、间距、分隔符、危险色、条件显隐、行 hover 行为、超过多少项进入“更多”。没有证据时沿用目标组件库和项目相似页面，不自造胶囊、实底按钮或图标按钮。

### 已提供规范的差异

- **Market W+**：操作列固定在右侧，白底，左侧 1px 分隔线；操作使用主色文字链接、零内边距，间隔 16px，链接之间不加竖线。仅显示当前记录可做的操作，不适用项直接隐藏。可见操作超过 3 个时，前 3 个平铺，其余进入“更多 ▾”。
- **WE**：显性操作使用主色文字链接，并以灰色 `|` 分隔；条件性操作初始隐藏，在当前行 hover 时出现。不要把五个以上操作始终全部平铺。
- **财富 w+ 或只有 Ant Design 5 默认规则的系统**：先查真实项目 Table 列定义与样式；没有项目证据时使用 `Button type="link" size="small"`、紧凑 `Space` 和 `Dropdown`，保持文字操作，不添加厚重边框或实底。

这些差异不能互相覆盖。尤其不要因为 WE 使用 `|`，就在 Market W+ 中也加入分隔符。

### Ant Design 实现形态

- Table 操作列使用 `fixed: "right"`（目标规范要求固定时）和足够但紧凑的明确宽度。
- 行内操作使用 `<Button type="link" size="small">`，通过局部类去掉多余水平 padding 与固定高度；不要将整页 `.ant-btn-link` 全局覆盖。
- 根据当前记录先构造可见 action 数组。前三项直接渲染，其余转换为 `Dropdown` 的 `menu.items`；每个菜单项保留稳定 key 和真实回调。
- Market W+ 可使用 `<Space size={16}>` 且无 split。WE 可使用带灰色分隔符的局部容器；分隔符不应出现在首尾，也不应把隐藏项留下空竖线。

### Element Plus 实现形态

- 目标规范要求固定时使用 `<el-table-column fixed="right">`。
- 行内操作使用 `<el-button link type="primary">`；超出阈值的操作放进 `el-dropdown`。根据行数据用 `v-if` 隐藏不适用操作，不用 disabled 灰字占位。
- WE 风格的 hover 显示通过操作列局部类与当前行 hover 控制，保留至少一个稳定可见的主要操作，避免键盘用户完全无法发现入口。

### 操作列浏览器验收

1. 检查普通行与不同状态行，确认可见操作符合数据条件，隐藏项没有留下空白和分隔符。
2. hover 行，确认需要渐进显示的操作出现，行移出后恢复；检查文字颜色、间距和对齐。
3. 横向滚动表格，确认固定操作列仍可见且遮挡关系正确。
4. 点击直接操作和“更多”菜单中的每一项，确认能打开对应弹窗/抽屉或产生明确的本地反馈。
