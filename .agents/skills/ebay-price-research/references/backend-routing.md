# eBay 数据后端审计与路由

## 采用顺序

官方 eBay 只读接口优先，其次使用已经安装并加载的 `AIALRA Shopping Browser` 读取 eBay 官方网页，最后使用用户已经安装并完成审计的只读 eBay MCP

本仓库不会自动安装第三方项目，不会创建开发者账户，不会索取或保存 API 密钥

## `AIALRA-0/AIALRA-SHOPPING-BROWSER`

它固定使用微软官方 Playwright MCP，并使用仓库外的独立持久 Chrome 资料

用户直接在可见 Chrome 窗口登录，不导出 Cookie、存储状态或密码

外部观察先通过通用证据校验，再映射为 eBay 节点输出 Schema

本地端到端测试验证 MCP 能启动 Chrome、打开页面并读取可见商品证据

审计结论为默认官方网页后端

## 已调查项目

### `jyarbro/ebay-buyer-mcp`

仓库为 `https://github.com/jyarbro/ebay-buyer-mcp`，许可证为 MIT，覆盖搜索、详情、变体、成交记录、卖家、退货和配送

它需要用户自己的 eBay 开发者凭据和独立部署，公开测试覆盖不足，不能自动安装或默认信任

### `CDataSoftware/ebay-mcp-server-by-cdata`

仓库许可证为 MIT，运行依赖商业 CData JDBC 驱动，适合已经购买并管理该驱动的企业环境

### `brightdata/skills`

它通过付费第三方数据服务读取多个电商平台，需要独立账户、令牌和数据处理信任，不能冒充 eBay 官方数据源

### `CooKey-Monster/EbayMcpServer`

代码中存在凭据占位符硬编码、令牌读写文件名不一致、依赖声明缺失和详情能力不足

审计结论为拒绝采用

### `strangeco0l/ebay-mcp`

功能包含买家、卖家、账户和财务范围，权限超过只读研究，并且没有明确许可证

只能学习公开思路，不能复制代码或作为默认后端

## 统一边界

所有后端必须返回相同 Schema，并经过相同去重、饱和、详情、风险和最终 validator

后端只能在第一次 eBay 访问前选择

AIALRA Shopping Browser 不可用时可以在访问前选择下一个已声明后端

登录、验证码、授权不足、限流和策略阻止出现后不能切换后端

登录失效不能通过 Cookie 导出解决，人机验证不能自动处理，宿主策略阻止不能通过换工具绕过
