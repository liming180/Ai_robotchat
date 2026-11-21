# Git 并行工作区

团队约定的并行修复命令是 `git worktree add ../hotfix-order hotfix/order-42`，分支名为 `hotfix/order-42`。独立工作区只用于隔离正在进行的修改，提交前仍需在目标分支运行完整测试。合并完成并确认工作区没有未提交文件后，使用 `git worktree remove ../hotfix-order` 清理，不直接删除目录后留下失效元数据。发现目录已被手工删除时，再执行 `git worktree prune`。
