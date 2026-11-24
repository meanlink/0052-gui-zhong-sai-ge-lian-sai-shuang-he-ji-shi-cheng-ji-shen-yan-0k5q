# 归钟 · 赛鸽联赛双盒计时成绩审验

禾湾计时联盟由三家俱乐部组成，共用赛台计时器。一场比赛的主盒与见证盒分别记录归巢脉冲，封条与校点纸常分开放，串行人工复核容易漏掉坏校点、混淆分批放飞起点或把未退回的异常成绩提前列榜。系统接收赛台验封、时钟对点和击钟时间，输出按放飞组归档的成绩簿。

## 一天的工作顺序

1. 07:55 核验主盒 BX-42 的 ZC-10042 封条与河桥厅交接。
2. 07:56 核验见证盒 BX-48 的 ZC-10048 封条后登记赛台到达。
3. 08:03–08:07 分别记录盒内时点与标准时点，主盒四记保留三记。
4. 08:40、09:00 两俱乐部独立放飞，分别以各自起点算用时。
5. 10:45 比对三张击钟，两盒估计偏移 +1200 ms、-400 ms，足环 39140 的差 3000 ms 阻止归档。
6. 11:05 复核见证盒原始记录并复录足环 39140；审验须重跑。
7. 11:20 双盒一致后签发分组成绩簿，计时与校点证据冻结。

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
| 复核员 | reviewer@demo.local | 复录被标记的异常击钟并签发成绩 |
| 查阅员 | viewer@demo.local | 查封条、赛台交接、校点、击钟和分组成绩簿 |

三个演示账号默认密码均为 `Demo2026!`。使用本地合成样本，seed 只插入缺失的自然键。关闭 `SEED_DEMO` 可跳过自动 seed。使用自己的 `JWT_SECRET`、`POSTGRES_PASSWORD` 和 `DEMO_PASSWORD` 部署。

| 目录 | 技术与职责 |
|---|---|
| backend | Python 3.11 / FastAPI，使用 PostgreSQL 16；Worker 轮询持久化队列，Redis 为登录限流及健康检查提供支持 |
| frontend | Nginx、HTML、CSS、JavaScript ES modules，HTTP 同源代理 |
| docker-compose.yml | 5 服务及健康检查、独立卷；Redis 与 worker 无宿主端口 |

角色、作业状态在 `backend/core.py`、`frontend/base.js` 定义，在 `backend/core.py`（鉴权、队列）与 `backend/worker.py` 使用。领域阶段由数据库约束与业务服务维护，`frontend/view.js` 负责显示。接口输出为最新已提交状态。

本样本保存手工录入的时戳与备注；真实计时硬件和赛事系统接入超出演示范围。

MIT License
