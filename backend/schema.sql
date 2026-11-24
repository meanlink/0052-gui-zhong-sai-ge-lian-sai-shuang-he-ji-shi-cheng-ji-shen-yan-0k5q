-- 旧版整场单本成绩簿已被组级 score_books 取代。
DROP TABLE IF EXISTS score_ledgers;
CREATE TABLE IF NOT EXISTS timing_cases (
 tag text PRIMARY KEY, serial text UNIQUE NOT NULL, seal text UNIQUE NOT NULL,
 owner_club text NOT NULL, origin text NOT NULL, target text NOT NULL CHECK(target<>origin),
 phase text NOT NULL CHECK(phase IN ('registered','misrouted','redirected','received'))
);
CREATE TABLE IF NOT EXISTS box_handoffs (
 tag text REFERENCES timing_cases(tag), seq int CHECK(seq>0),
 location text NOT NULL, clock_at timestamptz NOT NULL, witness text NOT NULL,
 PRIMARY KEY(tag,seq), UNIQUE(tag,clock_at)
);

CREATE TABLE IF NOT EXISTS meets (
 code text PRIMARY KEY,title text NOT NULL,desk text NOT NULL,
 calibration_from timestamptz NOT NULL, calibration_to timestamptz NOT NULL,
 finish_from timestamptz NOT NULL, finish_to timestamptz NOT NULL,
 primary_box text NOT NULL REFERENCES timing_cases(tag), witness_box text NOT NULL REFERENCES timing_cases(tag),
 status text NOT NULL DEFAULT 'open' CHECK(status IN ('open','archived')),
 calibration_epoch int NOT NULL DEFAULT 1 CHECK(calibration_epoch>=1),
 CHECK(primary_box<>witness_box),
 CHECK(calibration_from<calibration_to AND calibration_to<=finish_from AND finish_from<finish_to)
);
CREATE TABLE IF NOT EXISTS release_groups (
 meet text REFERENCES meets(code),code text,club text NOT NULL,released_at timestamptz NOT NULL,
 PRIMARY KEY(meet,code)
);
CREATE TABLE IF NOT EXISTS clock_anchors (
 meet text REFERENCES meets(code),box text REFERENCES timing_cases(tag),reference_at timestamptz NOT NULL,
 recorded_at timestamptz NOT NULL, inspector text NOT NULL, PRIMARY KEY(meet,box,reference_at)
);
CREATE TABLE IF NOT EXISTS finish_clicks (
 meet text,group_code text,bird text,primary_at timestamptz NOT NULL,witness_at timestamptz NOT NULL,
 remark text NOT NULL, revision int NOT NULL DEFAULT 1 CHECK(revision>=1), PRIMARY KEY(meet,bird),
 FOREIGN KEY(meet,group_code) REFERENCES release_groups(meet,code)
);
CREATE TABLE IF NOT EXISTS finish_corrections (
 meet text,bird text,revision int,
 prior_primary timestamptz NOT NULL,prior_witness timestamptz NOT NULL,
 reason text NOT NULL, corrected_by text NOT NULL, corrected_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(meet,bird,revision),FOREIGN KEY(meet,bird) REFERENCES finish_clicks(meet,bird)
);
-- 每场审验只有一行；calibration_epoch 记录审验所基于的校点代次，
-- 排队中的旧审验运行时若发现代次已推进即失败，不能用旧校点恢复旧榜。
CREATE TABLE IF NOT EXISTS clock_audits (
 meet text PRIMARY KEY REFERENCES meets(code), offsets jsonb NOT NULL, results jsonb NOT NULL,
 blocked int NOT NULL CHECK(blocked>=0), calibration_epoch int NOT NULL CHECK(calibration_epoch>=1),
 analyzed_at timestamptz NOT NULL DEFAULT now()
);
-- 组级成绩簿：同一 (meet, group_code) 的每次签发占一个新版本；
-- published 为当前榜，superseded 为被新版替代的历史榜，
-- withdrawn 为校点更正后立即撤下、等待新校点审验的榜，
-- reviewing 为迟到击钟/复录后只重开所属组、等待重审的状态。
CREATE TABLE IF NOT EXISTS score_books (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 meet text NOT NULL REFERENCES meets(code),
 group_code text NOT NULL,
 version int NOT NULL CHECK(version>=1),
 calibration_epoch int NOT NULL CHECK(calibration_epoch>=1),
 status text NOT NULL CHECK(status IN ('published','reviewing','withdrawn','superseded')),
 standings jsonb NOT NULL, evidence jsonb NOT NULL,
 source_audit timestamptz NOT NULL,
 notes text NOT NULL, approved_by text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),
 superseded_at timestamptz,
 UNIQUE(meet,group_code,version),
 FOREIGN KEY(meet,group_code) REFERENCES release_groups(meet,code)
);
-- 每场每组至多一本处于当前态（非 superseded）的成绩簿。
CREATE UNIQUE INDEX IF NOT EXISTS score_books_current
 ON score_books(meet,group_code) WHERE status<>'superseded';
-- 同一版审验对同组只能签发一次：重试同次签发不新增成绩簿。
CREATE UNIQUE INDEX IF NOT EXISTS score_books_audit_once
 ON score_books(meet,group_code,source_audit) WHERE status IN ('published','reviewing','withdrawn');
