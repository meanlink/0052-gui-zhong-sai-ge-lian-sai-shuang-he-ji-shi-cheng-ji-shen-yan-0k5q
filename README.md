# 归钟 · 赛鸽联赛双盒计时成绩审验

禾湾计时联盟由三家俱乐部组成，共用赛台计时器。一场比赛的主盒与见证盒分别记录归巢脉冲，封条与校点纸常分开放，串行人工复核容易漏掉坏校点、混淆分批放飞起点或把未退回的异常成绩提前列榜。系统接收赛台验封、时钟对点和击钟时间，输出按放飞组归档的成绩簿。

## 一天的工作顺序

1. 07:55 核验主盒 BX-42 的 ZC-10042 封条与河桥厅交接。
2. 07:56 核验见证盒 BX-48 的 ZC-10048 封条后登记赛台到达。
3. 08:03–08:07 分别记录盒内时点与标准时点，主盒四记保留三记。
4. 08:40、09:00 两俱乐部独立放飞，分别以各自起点算用时。
5. 10:45 比对三张击钟，两盒估计偏移 +1200 ms、-400 ms，足环 39140 的差 3000 ms 阻止归档。
6. 11:05 复核见证盒原始记录并复录足环 39140；审验须重跑。
7. 11:20 双盒一致后按放飞组签发成绩簿，计时与校点证据冻结进每个版本。

## 成绩簿生命周期

- 成绩簿按**放飞组**独立签发与计版（`score_books`，每组每版一行）：状态为
  `published`（在榜）、`reviewing`（迟到击钟/复录后只重开所属组）、
  `withdrawn`（共用校点更正后立即撤榜）或 `superseded`（被新版替代的历史簿）。
- 成绩簿签发后到达的迟到击钟、或对已发榜击钟的复录，只把**所属放飞组**的当前簿
  置为 `reviewing`；其他组的在榜成绩簿不受影响，照常查榜。重新审验通过后，
  仅受影响组出新版，未变化的组保持原版本。
- 共用校点是两只计时盒的共同基准。已形成审验（或已发榜）后再登记校点即构成更正：
  `meets.calibration_epoch` 加一，所有受影响组的当前簿**立即**置为 `withdrawn`，
  旧审验删除。全部组按同一代校点审验通过后，才在同一次签发中一次性切换到新榜。
- 审验作业入队时携带当时的校点代次；更正前已排队的审验即使晚完成，也会因
  代次不符而失败，旧榜不会被恢复。
- 同一次审验（同一 `source_audit`）对同一组重复签发不产生新簿：复核中的簿
  恢复在榜，在榜中的簿原样保留。
- `GET /api/standings` 展示各组当前状态与校点代次；
  `GET /api/standings/{meet}/history` 按原校点证据（offsets）、排名和批注
  回查该场历次签发。

## 算法口径

以盒内时点减标准时点作为候选偏移。对每盒按中位数和 MAD 排除离群点，阈值取 100 ms 与三倍缩放 MAD 中的大值；至少三记有效，剩余最大差不超过 250 ms。使用剩余中位数校正击钟；两盒差超 500 ms 或越过比赛时窗须退回复录，中心时间减各组放飞起点作成绩。同组用时平局采用相同竞赛名次。结果可按原始时点、修订史与校点账复算。

## 上手

```sh
cp .env.example .env
docker compose up -d --build --wait
docker compose exec -T backend python -m scripts.seed_demo
docker compose down --remove-orphans
```

前端走本机 **18446**，API 走 **19446**，PostgreSQL 走 **17946**。本地开发可在安装 Python 3.11、PostgreSQL 和 Redis 后配置与 Compose 相同的环境变量，在 backend 运行 `uvicorn app:app --reload`，前端以 Nginx 同源代理启动。

| 角色 | 邮箱 | 业务权限 |
|---|---|---|
| 录入员 | operator@demo.local | 登记器材、验封交接、校点、录入击钟与运行审验 |
| 复核员 | reviewer@demo.local | 复录被标记的异常击钟并按组签发/切换成绩簿 |
| 查阅员 | viewer@demo.local | 查封条、赛台交接、校点、击钟、各组成绩簿与历次签发 |

三个演示账号默认密码均为 `Demo2026!`。使用本地合成样本，seed 只插入缺失的自然键。关闭 `SEED_DEMO` 可跳过自动 seed。使用自己的 `JWT_SECRET`、`POSTGRES_PASSWORD` 和 `DEMO_PASSWORD` 部署。

| 目录 | 技术与职责 |
|---|---|
| backend | Python 3.11 / FastAPI，使用 PostgreSQL 16；Worker 轮询持久化队列，Redis 为登录限流及健康检查提供支持 |
| frontend | Nginx、HTML、CSS、JavaScript ES modules，HTTP 同源代理 |
| docker-compose.yml | 5 服务及健康检查、独立卷；Redis 与 worker 无宿主端口 |

角色、作业状态在 `backend/core.py`、`frontend/base.js` 定义，在 `backend/core.py`（鉴权、队列）与 `backend/worker.py` 使用。领域阶段（含成绩簿的 `published/reviewing/withdrawn/superseded`）由数据库约束与业务服务维护，状态文案见 `frontend/view.js`，`frontend/standings.js` 负责显示并支持历次签发回查。接口输出为最新已提交状态。

本样本保存手工录入的时戳与备注；真实计时硬件和赛事系统接入超出演示范围。

MIT License
