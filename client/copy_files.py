#!/usr/bin/env python3
import argparse
import shutil
from pathlib import Path

def safe_copy(src: Path, dst: Path):
    """dst가 존재하면 '(1)', '(2)' 식으로 이름을 늘려서 충돌 없이 복사."""
    if not dst.exists():
        shutil.copy2(src, dst)
        return dst
    stem, suffix = dst.stem, dst.suffix
    parent = dst.parent
    i = 1
    while True:
        cand = parent / f"{stem} ({i}){suffix}"
        if not cand.exists():
            shutil.copy2(src, cand)
            return cand
        i += 1

def copy_matching_files(src_dir: Path, dst_dir: Path, exts=(".json", ".pt"), preserve_structure=True):
    src_dir = src_dir.resolve()
    dst_dir = dst_dir.resolve()
    if not src_dir.is_dir():
        raise NotADirectoryError(f"소스 디렉토리가 아닙니다: {src_dir}")

    dst_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    copied_paths = []
    # 확장자 소문자 비교
    exts_lower = tuple(e.lower() for e in exts)

    for path in src_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in exts_lower:
            if preserve_structure:
                # src 기준 상대 경로를 유지
                rel = path.relative_to(src_dir)
                target = dst_dir / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
                copied_paths.append((path, target))
            else:
                target = dst_dir / path.name
                dst_dir.mkdir(parents=True, exist_ok=True)
                # 평탄화 시 이름 충돌 처리
                final_target = safe_copy(path, target)
                copied_paths.append((path, final_target))
            count += 1
            print(f"[복사] {path} -> {copied_paths[-1][1]}")
    print(f"\n완료: 총 {count}개 파일 복사됨 (.json, .pt)")
    return copied_paths

def main():

    src_dir = Path("/home/ktva/PROJECT/Diffusion/GP_adapter/cache/cached_graphs_drama_media_data_embed_fixed_z_ver1+2")
    dst_dir = Path("data/")

    copy_matching_files(src_dir, dst_dir, exts=(".json", ".pt"), preserve_structure=False)

if __name__ == "__main__":
    main()
