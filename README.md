# 实时投票系统

## 项目概述

这是一个简化版实时投票系统，支持用户投票并实时查看统计结果。

## 功能需求

### 1. 投票问卷
- 系统预置 1 份问卷，包含 1 道单选题（3~5 个选项）
- 所有用户可投票，每人一次（不需用户登录，简单前端限制即可）

### 2. 数据统计
- 投票后，系统统计每个选项的当前票数
- 所有正在查看页面的用户应实时收到统计结果更新

### 3. 前端界面
使用 Vue3实现：
- 显示问卷题目和选项
- 用户选择并提交投票
- 实时展示投票结果

### 4. 后端服务
- 提供 RESTful API 实现投票和获取当前问卷数据
- 支持 WebSocket接口用于实时推送统计变化