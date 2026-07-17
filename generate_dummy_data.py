"""
조선 Hull 실적 더미데이터 생성 스크립트
- Hull_erec_baseMH
- Hull_info
- R99_rate
협의된 규칙(대화 기반)에 따라 생성. 실제 회사 데이터 아님.
"""

import random
import string
import numpy as np
import pandas as pd

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

SHIP_TYPES = ["LNG", "CONT", "SHTL", "LPG"]

# 계량->기준 factor (선종별 고정)
FACTOR_MAP = {"LNG": 0.8, "CONT": 0.7, "SHTL": 0.85, "LPG": 0.85}

# 계량공수 항목별 비율 (합계 100%)
RATIO = {"심출": 0.11, "취부": 0.22, "용접": 0.54, "사상": 0.10, "기타": 0.03}

# R99율 지정값 (선종, stage) -> 값. 미지정은 0
R99_SPECIFIED = {
    ("LNG", 40): 0.221, ("LNG", 50): 0.312, ("LNG", 51): 0.312, ("LNG", 52): 0.169, ("LNG", 60): 0.378,
    ("CONT", 40): 0.225, ("CONT", 50): 0.349, ("CONT", 51): 0.349, ("CONT", 52): 0.280, ("CONT", 60): 0.147,
    ("SHTL", 40): 0.228, ("SHTL", 50): 0.444, ("SHTL", 51): 0.444, ("SHTL", 52): 0.0, ("SHTL", 60): 0.37,
    ("LPG", 40): 0.145, ("LPG", 50): 0.145, ("LPG", 51): 0.145, ("LPG", 52): 0.145, ("LPG", 60): 0.145,
}
ALL_STAGES = [30, 40, 50, 51, 52, 60, 70]


def random_letters(n):
    return "".join(random.choices(string.ascii_uppercase, k=n))


def random_digits(n):
    return "".join(random.choices(string.digits, k=n))


def gen_mo_block_code(existing):
    # 영문1 + 숫자2 + 영문2 (예: B11UC)
    while True:
        code = random_letters(1) + random_digits(2) + random_letters(2)
        if code not in existing:
            existing.add(code)
            return code


def gen_block_code(mo_block, existing):
    # 모블록 앞 3자리(영문1+숫자2) 유지 + 숫자1+영문1 (예: B110P)
    prefix = mo_block[:3]
    while True:
        code = prefix + random_digits(1) + random_letters(1)
        if code not in existing:
            existing.add(code)
            return code


def gen_module_pool():
    n = random.randint(4, 6)
    return [random_letters(random.randint(5, 7)) for _ in range(n)]


# ---------------------------------------------------------
# 1) Hull_info (프로젝트 마스터) + 프로젝트-선종 매핑
# ---------------------------------------------------------
N_PROJECTS = 10
project_codes = sorted(random.sample(range(1000, 9999), N_PROJECTS))
projects = [f"SN{code}" for code in project_codes]
project_shiptype = {p: random.choice(SHIP_TYPES) for p in projects}

hull_info_rows = []
for p in projects:
    hull_info_rows.append({
        "도크/SKID": random.choice(["도크1", "도크2", "SKID1", "SKID2", ""]),
        "프로젝트": p,
        "시리즈": random.choice(["1차선", "2차선", "3차선", ""]),
        "선주": random.choice(["선주A", "선주B", "선주C", "선주D", ""]),
        "선종": project_shiptype[p],
        "선형": random.choice(["17.4K", "17.5K", "180K", "2700TEU", "membrane", ""]),
        "모선": random.choice(["", f"MV-{random.randint(100,999)}"]),
    })
hull_info_df = pd.DataFrame(hull_info_rows)

# ---------------------------------------------------------
# 2) R99_rate
# ---------------------------------------------------------
r99_rows = []
for st in SHIP_TYPES:
    for stage in ALL_STAGES:
        rate = R99_SPECIFIED.get((st, stage), 0.0)
        r99_rows.append({"선종": st, "stage": stage, "R99율": rate})
r99_df = pd.DataFrame(r99_rows)

# ---------------------------------------------------------
# 3) Hull_erec_baseMH
# ---------------------------------------------------------
WORK_UNITS = ["EA", "M", "TON", "LOT"]
N_MOBLOCK_PER_PROJECT = 5
N_SUBBLOCK_PER_MOBLOCK = 8
SUB_STAGES = [30, 40]
MO_STAGES = [50, 60, 70]

erec_rows = []
mo_block_codes_global = set()

for p in projects:
    ship_type = project_shiptype[p]
    factor = FACTOR_MAP[ship_type]

    for _ in range(N_MOBLOCK_PER_PROJECT):
        mo_block = gen_mo_block_code(mo_block_codes_global)
        module_pool = gen_module_pool()  # 이 모블록 하위에서 대부분 재사용되는 모듈셋

        sub_block_codes = set()
        sub_blocks = [gen_block_code(mo_block, sub_block_codes) for _ in range(N_SUBBLOCK_PER_MOBLOCK)]

        def make_row(block_no, stage, module):
            butt_e = round(random.uniform(50, 450), 1)
            fillet_e = round(random.uniform(50, 450), 1)
            butt_w = round(random.uniform(50, 450), 1)
            fillet_w = round(random.uniform(50, 450), 1)

            total_gy = random.randint(100, 1000)  # total_계량
            simchul_gy = round(total_gy * RATIO["심출"], 2)
            chwibu_gy = round(total_gy * RATIO["취부"], 2)
            yongjeop_gy = round(total_gy * RATIO["용접"], 2)
            sasang_gy = round(total_gy * RATIO["사상"], 2)
            gita_gy = round(total_gy - (simchul_gy + chwibu_gy + yongjeop_gy + sasang_gy), 2)  # 나머지(반올림 오차 보정)

            simchul_gj = round(simchul_gy * factor, 2)
            chwibu_gj = round(chwibu_gy * factor, 2)
            yongjeop_gj = round(yongjeop_gy * factor, 2)
            sasang_gj = round(sasang_gy * factor, 2)
            gita_gj = round(gita_gy * factor, 2)
            total_gj = round(simchul_gj + chwibu_gj + yongjeop_gj + sasang_gj + gita_gj, 2)

            a2 = f"H{block_no}SF0{stage:02d}0"

            return {
                "프로젝트": p,
                "모블록번호": mo_block,
                "블록번호": block_no,
                "stage": stage,
                "기능": "D",
                "a2": a2,
                "모듈": module,
                "취부장_total": round(butt_e + fillet_e, 1),
                "취부장_butt": butt_e,
                "취부장_fillet": fillet_e,
                "용접장_total": round(butt_w + fillet_w, 1),
                "용접장_butt": butt_w,
                "용접장_fillet": fillet_w,
                "작업량": random.randint(1, 100),
                "작업량_단위": random.choice(WORK_UNITS),
                "심출_계량": simchul_gy,
                "취부_계량": chwibu_gy,
                "용접_계량": yongjeop_gy,
                "사상_계량": sasang_gy,
                "기타_계량": gita_gy,
                "total_계량": total_gy,
                "심출_기준": simchul_gj,
                "취부_기준": chwibu_gj,
                "용접_기준": yongjeop_gj,
                "사상_기준": sasang_gj,
                "기타_기준": gita_gj,
                "total_기준": total_gj,
                "원본파일명": f"{p}_{mo_block}_dummy.xlsx",
            }

        # 자블록 레벨: stage 30, 40
        for block_no in sub_blocks:
            for stage in SUB_STAGES:
                sampled_modules = random.sample(module_pool, k=min(len(module_pool), random.randint(4, 6)))
                for module in sampled_modules:
                    erec_rows.append(make_row(block_no, stage, module))

        # 모블록 레벨: stage 50, 60, 70 (블록번호 = 모블록번호)
        for stage in MO_STAGES:
            sampled_modules = random.sample(module_pool, k=min(len(module_pool), random.randint(4, 6)))
            for module in sampled_modules:
                erec_rows.append(make_row(mo_block, stage, module))

erec_df = pd.DataFrame(erec_rows)

# ---------------------------------------------------------
# 저장
# ---------------------------------------------------------
erec_df.to_csv("/home/claude/Hull_erec_baseMH.csv", index=False, encoding="utf-8-sig")
hull_info_df.to_csv("/home/claude/Hull_info.csv", index=False, encoding="utf-8-sig")
r99_df.to_csv("/home/claude/R99_rate.csv", index=False, encoding="utf-8-sig")

print("Hull_erec_baseMH:", erec_df.shape)
print("Hull_info:", hull_info_df.shape)
print("R99_rate:", r99_df.shape)
print()
print(erec_df.head(10).to_string())
