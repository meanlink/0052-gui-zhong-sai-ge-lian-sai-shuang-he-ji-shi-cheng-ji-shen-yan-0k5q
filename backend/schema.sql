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
CREATE TABLE IF NOT EXISTS clock_audits (
 meet text PRIMARY KEY REFERENCES meets(code), offsets jsonb NOT NULL, results jsonb NOT NULL,
 blocked int NOT NULL CHECK(blocked>=0), analyzed_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS score_ledgers (
 meet text PRIMARY KEY REFERENCES meets(code), standings jsonb NOT NULL, evidence jsonb NOT NULL,
 source_audit timestamptz NOT NULL, notes text NOT NULL, approved_by text NOT NULL, approved_at timestamptz NOT NULL DEFAULT now()
);
